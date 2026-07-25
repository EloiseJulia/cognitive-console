import json
import sys
import types

import numpy as np
import pytest

from cognitive_console.experiments import adjudicate_c2b as A
from cognitive_console.steering import psr
from scripts import run_psr_arm as P


def _items(prefix, n):
    return [{"id": f"{prefix}-{i}", "prompt": f"q {i}", "answer": "1"} for i in range(n)]


def test_basis_construction_keeps_caa_iti_and_top_pca():
    caa = np.array([1.0, 0.0, 0.0, 0.0])
    iti = np.array([0.0, 1.0, 0.0, 0.0])
    acts = np.array([
        [1.0, 0.0, 1.0, 0.0],
        [-1.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, -1.0, 0.0],
        [0.0, -1.0, -1.0, 0.0],
    ])
    basis = psr.build_psr_basis(
        axis="deliberation",
        layer=3,
        caa_direction=caa,
        iti_direction=iti,
        natural_activations=acts,
        r=2,
    )
    assert basis.labels[:2] == ["caa", "iti"]
    gram = basis.basis @ basis.basis.T
    np.testing.assert_allclose(gram, np.eye(basis.n_basis), atol=1e-10)
    assert basis.diagnostics["requested_pca_rank"] == 2


class _DirectionalSampler(A.OutcomeSampler):
    def __init__(self, target, seen):
        self.target = np.asarray(target, dtype=float)
        self.seen = seen

    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        self.seen.append(str(item["id"]))
        align = max(0.0, float(np.dot(direction, self.target)))
        score = min(1.0, align * (float(alpha) / 24.0))
        return A.SampleBatch(outcomes=[score] * int(k), degeneracies=[0.0] * int(k))


def _toy_basis():
    caa = np.array([1.0, 0.0, 0.0])
    iti = np.array([0.0, 1.0, 0.0])
    acts = np.array([
        [1.0, 0.0, 0.2],
        [-1.0, 0.0, -0.2],
        [0.0, 1.0, 0.3],
        [0.0, -1.0, -0.3],
    ])
    return psr.build_psr_basis(
        axis="deliberation",
        layer=2,
        caa_direction=caa,
        iti_direction=iti,
        natural_activations=acts,
        r=1,
    )


def _optimize_with_target(target, budget=2, seed=123):
    seen = []

    def factory(schedule):
        return _DirectionalSampler(target, seen)

    cfg = psr.PSRConfig(candidate_budget=budget, optimizer_seed=seed)
    res = psr.optimize_psr_on_dev(
        axis="deliberation",
        model="toy",
        backend="synthetic",
        basis=_toy_basis(),
        sampler_factory=factory,
        dev_items=_items("dev", 3),
        forbidden_test_items=_items("test", 3),
        neutral_prompt="neutral",
        config=cfg,
        k=2,
        num_hidden_layers=3,
    )
    return res, seen


def test_dev_only_optimizer_budget_determinism_and_no_test_use():
    res1, seen1 = _optimize_with_target(np.array([1.0, 0.0, 0.0]), budget=4, seed=99)
    res2, seen2 = _optimize_with_target(np.array([1.0, 0.0, 0.0]), budget=4, seed=99)
    assert res1.evaluations_used <= 4
    assert res1.evaluations_used == 4
    assert res1.evaluations_used == res2.evaluations_used
    assert res1.direction == res2.direction
    assert res1.alpha == res2.alpha
    assert all(s.startswith("dev-") for s in seen1)
    assert not any(s.startswith("test-") for s in seen1)
    assert seen1 == seen2
    # One baseline DEV pass plus exactly one DEV pass per candidate tuple.
    assert len(seen1) == (1 + res1.evaluations_used) * 3


def test_psr_recovers_caa_and_iti_special_cases():
    caa_res, _ = _optimize_with_target(np.array([1.0, 0.0, 0.0]), budget=2)
    np.testing.assert_allclose(caa_res.direction_array(), np.array([1.0, 0.0, 0.0]), atol=1e-10)

    iti_res, _ = _optimize_with_target(np.array([0.0, 1.0, 0.0]), budget=2)
    assert abs(float(np.dot(iti_res.direction_array(), np.array([0.0, 1.0, 0.0])))) > 0.999


class _RatioPenaltySampler(A.OutcomeSampler):
    def sample(self, axis, item, instruction, alpha, k, direction, layer):
        if float(alpha) == 0.0:
            return A.SampleBatch(outcomes=[0.0] * int(k), degeneracies=[0.1] * int(k))
        caa_align = abs(float(np.dot(direction, np.array([1.0, 0.0, 0.0]))))
        if caa_align > 0.99:
            # outcome 1.0, ratio 2.0 => J = 1 - (2 - 1.5) = 0.5
            return A.SampleBatch(outcomes=[1.0] * int(k), degeneracies=[0.2] * int(k))
        # outcome 0.75, ratio 1.0 => J = 0.75
        return A.SampleBatch(outcomes=[0.75] * int(k), degeneracies=[0.1] * int(k))


def test_psr_objective_uses_frozen_coherence_ratio_penalty():
    cfg = psr.PSRConfig(candidate_budget=2, optimizer_seed=123, coherence_lambda=1.0)
    res = psr.optimize_psr_on_dev(
        axis="deliberation",
        model="toy",
        backend="synthetic",
        basis=_toy_basis(),
        sampler_factory=lambda _schedule: _RatioPenaltySampler(),
        dev_items=_items("dev", 3),
        forbidden_test_items=_items("test", 3),
        neutral_prompt="neutral",
        config=cfg,
        k=2,
        num_hidden_layers=3,
    )
    assert abs(float(np.dot(res.direction_array(), np.array([0.0, 1.0, 0.0])))) > 0.999
    assert res.selected_dev_score == pytest.approx(0.75)
    assert res.candidate.coherence_penalty == pytest.approx(0.0)


def test_coverage_guard_rejects_incomplete_and_mismatched_runs():
    expected_ids = {"deliberation": ["i0", "i1", "i2"]}
    good_axis = {
        "axis": "deliberation",
        "n_dev": 1,
        "n_test": 2,
        "k": A.K_SAMPLES,
        "dev_selection": {"frozen_alpha": 2.0},
        "per_item_prompt": [0.0, 0.0],
        "per_item_steer": [1.0, 1.0],
        "per_item_diff": [1.0, 1.0],
    }
    payload = {
        "steering_method": "psr",
        "config_fingerprint": "abc",
        "axes": [good_axis],
        "psr_provenance": {
            "psr_optimization": {
                "deliberation": {
                    "axis": "deliberation",
                    "evaluations_used": 2,
                    "candidate_budget": 32,
                    "candidate": {"alpha": 2.0},
                    "config": {"coherence_lambda": 1.0},
                }
            }
        },
    }
    psr.validate_psr_coverage(
        result_payload=payload,
        expected_fingerprint="abc",
        expected_axes=["deliberation"],
        expected_item_ids_by_axis=expected_ids,
    )
    bad = json.loads(json.dumps(payload))
    bad["axes"][0]["per_item_steer"] = [1.0]
    with pytest.raises(ValueError):
        psr.validate_psr_coverage(
            result_payload=bad,
            expected_fingerprint="abc",
            expected_axes=["deliberation"],
            expected_item_ids_by_axis=expected_ids,
        )
    bad_fp = json.loads(json.dumps(payload))
    bad_fp["config_fingerprint"] = "forged"
    with pytest.raises(ValueError):
        psr.validate_psr_coverage(
            result_payload=bad_fp,
            expected_fingerprint="abc",
            expected_axes=["deliberation"],
            expected_item_ids_by_axis=expected_ids,
        )
    bad_budget = json.loads(json.dumps(payload))
    bad_budget["psr_provenance"]["psr_optimization"]["deliberation"]["evaluations_used"] = 33
    with pytest.raises(ValueError):
        psr.validate_psr_coverage(
            result_payload=bad_budget,
            expected_fingerprint="abc",
            expected_axes=["deliberation"],
            expected_item_ids_by_axis=expected_ids,
        )


def test_psr_runner_tiny_synthetic_smoke(tmp_path):
    out_dir = tmp_path / "psr_smoke"
    rc = P.main([
        "--backend", "synthetic",
        "--axes", "deliberation",
        "--n-items", "4",
        "--psr-candidate-budget", "2",
        "--bootstrap-b", "50",
        "--allow-underpowered",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    payload = json.loads((out_dir / "psr_c2b_adjudication_results.json").read_text(encoding="utf-8"))
    assert payload["steering_method"] == "psr"
    assert payload["experiment_id"].startswith("psr-c2b-adj-")
    assert "psr_optimization" in payload["psr_provenance"]
    assert payload["psr_provenance"]["psr_optimization"]["deliberation"]["evaluations_used"] <= 32
    assert (out_dir / "transcripts" / "paired_test_channels.jsonl").exists()
    assert not (out_dir / "c2b_adjudication_results.json").exists()


def test_psr_runner_guard_precedes_done_persistence(tmp_path, monkeypatch):
    out_dir = tmp_path / "psr_guard_fail"

    def fail_guard(**kwargs):
        raise ValueError("forced guard failure")

    monkeypatch.setattr(psr, "validate_psr_coverage", fail_guard)
    with pytest.raises(ValueError):
        P.main([
            "--backend", "synthetic",
            "--axes", "deliberation",
            "--n-items", "4",
            "--psr-candidate-budget", "2",
            "--bootstrap-b", "50",
            "--allow-underpowered",
            "--out-dir", str(out_dir),
        ])
    assert not (out_dir / "psr_c2b_adjudication_results.json").exists()
    assert not (out_dir / "experiment-registry.yaml").exists()


def test_hf_psr_arm_shares_single_base_model_load(tmp_path, monkeypatch):
    calls = {"from_pretrained": 0}

    class _FakeCuda:
        @staticmethod
        def is_available():
            return False

        @staticmethod
        def manual_seed_all(seed):
            return None

        @staticmethod
        def empty_cache():
            return None

    fake_torch = types.SimpleNamespace(
        float32="float32",
        float16="float16",
        bfloat16="bfloat16",
        cuda=_FakeCuda(),
        manual_seed=lambda seed: None,
    )

    class _FakeConfig:
        hidden_size = 4
        num_hidden_layers = 4

    class _FakeTokenizer:
        eos_token = "<eos>"
        pad_token = None
        pad_token_id = 0
        padding_side = "right"

    class _FakeModel:
        def __init__(self):
            self.model = types.SimpleNamespace(layers=[object(), object(), object(), object()])

        def to(self, device):
            return self

        def eval(self):
            return self

    class _FakeAutoConfig:
        @staticmethod
        def from_pretrained(model_name):
            return _FakeConfig()

    class _FakeAutoTokenizer:
        @staticmethod
        def from_pretrained(model_name):
            return _FakeTokenizer()

    class _FakeAutoModelForCausalLM:
        @staticmethod
        def from_pretrained(model_name, **kwargs):
            calls["from_pretrained"] += 1
            return _FakeModel()

    fake_transformers = types.SimpleNamespace(
        AutoConfig=_FakeAutoConfig,
        AutoTokenizer=_FakeAutoTokenizer,
        AutoModelForCausalLM=_FakeAutoModelForCausalLM,
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    monkeypatch.setattr(P.p0, "_pick_device", lambda: "cpu")
    monkeypatch.setattr(P.p0, "_pick_dtype", lambda: "float32")

    def fake_c1_run(**kwargs):
        provider = kwargs["activation_provider"]
        assert provider.available_layers() == [0, 1, 2, 3, 4]
        assert provider.hidden_dim == 4
        return {"axes": [{"axis": "deliberation", "chosen_layer": 2, "stable_layer_found": True}]}

    monkeypatch.setattr(P.c1, "run", fake_c1_run)
    monkeypatch.setattr(P.p0, "_extract_direction", lambda *args, **kwargs: np.array([1.0, 0.0, 0.0, 0.0]))

    class _FakeITI:
        direction = np.array([0.0, 1.0, 0.0, 0.0])

    monkeypatch.setattr(P, "extract_iti", lambda *args, **kwargs: _FakeITI())

    def fake_get_activations(self, texts, layer):
        self._ensure_loaded()
        rows = []
        for i, _text in enumerate(texts):
            rows.append(np.array([1.0, float(i), float(layer), 0.5], dtype=np.float32))
        return np.vstack(rows)

    monkeypatch.setattr("cognitive_console.activations.provider.HFActivationProvider.get_activations", fake_get_activations)
    monkeypatch.setattr(P.c2b, "load_axis_items", lambda axis, use_fixture, n_items: _items(axis, 4))
    monkeypatch.setattr(P.c2b, "build_strong_prompts", lambda axis, n: [("p0", "strong prompt")])

    def fake_optimize(**kwargs):
        return psr.PSRResult(
            axis=kwargs["axis"],
            model=kwargs["model"],
            backend=kwargs["backend"],
            layer=kwargs["basis"].layer,
            schedule_layers=[kwargs["basis"].layer],
            schedule_weights=[1.0],
            direction=[1.0, 0.0, 0.0, 0.0],
            alpha=2.0,
            selected_dev_score=0.0,
            selected_dev_outcome=0.0,
            selected_dev_degeneracy=0.0,
            baseline_degeneracy=0.0,
            evaluations_used=1,
            candidate_budget=kwargs["config"].candidate_budget,
            item_ids_dev=[str(it["id"]) for it in kwargs["dev_items"]],
            item_ids_forbidden_test=[str(it["id"]) for it in kwargs["forbidden_test_items"]],
            config=kwargs["config"].to_dict(),
            basis_labels=list(kwargs["basis"].labels),
            basis_diagnostics=dict(kwargs["basis"].diagnostics),
            candidate=psr.PSRCandidate(
                coefficients=[1.0],
                schedule_weights=[1.0],
                direction=[1.0, 0.0, 0.0, 0.0],
                alpha=2.0,
                dev_score=0.0,
                dev_outcome=0.0,
                dev_degeneracy=0.0,
                baseline_degeneracy=0.0,
                coherence_penalty=0.0,
                coherence_ratio=0.0,
                candidate_index=0,
            ),
        )

    monkeypatch.setattr(psr, "optimize_psr_on_dev", fake_optimize)

    args = types.SimpleNamespace(
        model="fake-model",
        axes=["deliberation"],
        n_extraction=4,
        seed=123,
        psr_rank=16,
        psr_candidate_budget=32,
        psr_seed=20260723,
        psr_coherence_lambda=1.0,
        n_items=4,
        use_fixture=True,
        n_strong=1,
        max_new_tokens=4,
        temperature=0.7,
        batch_size=2,
    )
    specs, results, sampler_for_axis, model, hardware = P.build_specs_hf_psr(args, tmp_path)
    assert calls["from_pretrained"] == 1
    assert model == "fake-model"
    assert hardware == "cpu-float32"
    assert len(specs) == 1
    assert set(results) == {"deliberation"}
    assert sampler_for_axis("deliberation").gen._model is not None
