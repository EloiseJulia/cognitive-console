
import json
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.steering.generate import project_out_direction_array, unit_vector
from scripts import run_e0016_ablation_positive_control as e0016


def _items(n, prefix="it"):
    return [e0016.Item(f"{prefix}-{i}", f"Benign safe prompt {i}", "test") for i in range(n)]


def test_projection_ablation_zeroes_component_and_hook_bites_guard():
    r = unit_vector(np.array([1.0, 2.0, -1.0]))
    h = np.array([[[3.0, 4.0, 5.0], [1.0, 0.0, -2.0]]])
    new = project_out_direction_array(h, r)
    assert np.max(np.abs(np.tensordot(new, r, axes=([-1], [0])))) < 1e-10
    stats = {1: {"max_abs_before": 3.0, "max_abs_after": 1e-8, "mean_abs_before": 1.0, "mean_abs_after": 1e-8, "n_values": 2, "violation_count": 0, "max_violation": 0.0}}
    payload = e0016.assert_ablation_hook_bites(
        stats, expected_layers=[1], abs_tol=1e-5
    )
    assert payload["non_vacuous"] is True
    assert payload["violation_count"] == 0


def test_hook_bites_rejects_per_element_violation_hidden_by_global_max():
    stats = {
        1: {
            "max_abs_before": 100.0,
            "max_abs_after": 1.0,
            "mean_abs_before": 50.0,
            "mean_abs_after": 0.5,
            "n_values": 2,
            "violation_count": 1,
            "max_violation": 0.999,
        }
    }
    with pytest.raises(ValueError, match="failed"):
        e0016.assert_ablation_hook_bites(
            stats, expected_layers=[1], abs_tol=1e-3, rel_tol=0.05
        )


def test_dtype_tolerances_distinguish_fp16_bf16_and_fp32():
    fp32 = e0016.dtype_abs_tol("float32", 3584)
    fp16 = e0016.dtype_abs_tol("float16", 3584)
    bf16 = e0016.dtype_abs_tol("bfloat16", 3584)
    assert fp32 == 1e-5
    assert fp16 > fp32
    assert bf16 > fp16


def test_dev_eligibility_gate_fires_when_baseline_under_floor():
    low = e0016.EvalResult("baseline", np.zeros((4, 2)), np.zeros((4, 2)), ["h"] * 4)
    eligible, status, rate = e0016.dev_eligibility_status(low)
    assert eligible is False
    assert status == "INVALID_REGIME_B_UNDERPOWERED"
    assert rate == 0.0


def test_real_not_smoke_rejects_placeholder_provenance():
    bundle = e0016.DirectionBundle(
        direction=unit_vector(np.arange(1, 17, dtype=float)),
        source_layer=1,
        position="last_token",
        provenance={
            "method": "arditi_refusal_direction_mean_harmful_minus_harmless",
            "derivation_function": "forward_pass_only_no_generation",
            "selected_layer_separation": 2.0,
            "note": "synthetic placeholder",
        },
    )
    with pytest.raises(ValueError, match="smoke|placeholder"):
        e0016.assert_real_not_smoke(
            bundle,
            backend="hf",
            provider_hidden_dim=16,
            xstest_prov={},
            contrast_prov={},
            dev=_items(2, "d"),
            test=_items(2, "t"),
        )


def test_dev_test_disjoint_guard():
    dev = [e0016.Item("same", "a", "s")]
    test = [e0016.Item("same", "b", "s")]
    with pytest.raises(ValueError, match="DEV/TEST overlap"):
        e0016.assert_dev_test_disjoint(dev, test)


def test_random_control_path_does_not_pass_in_synthetic_smoke(tmp_path):
    payload = e0016.run(e0016.parse_args(["--backend", "synthetic", "--out-dir", str(tmp_path), "--dev-n", "4", "--test-n", "8", "--k", "2"]))
    assert payload["dev"]["status"] == "ELIGIBLE"
    assert payload["status"] == "PASS"
    assert payload["test"]["random_control"]["pass"] is False
    assert payload["harmful_generation_performed"] is False
    written = tmp_path / "e0016_ablation_positive_control_results.json"
    assert json.loads(written.read_text(encoding="utf-8"))["valid_for_paper"] is False


def test_pass_rule_logic_and_random_veto():
    base = e0016.EvalResult("baseline", np.ones((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    ablated = e0016.EvalResult("ablation", np.zeros((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    random_null = e0016.EvalResult("random", np.ones((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    passed = e0016.pass_rule(base, ablated, random_null, bootstrap_seed=1)
    assert passed["pass"] is True
    random_bad = e0016.EvalResult("random", np.zeros((6, 2)), np.zeros((6, 2)), [str(i) for i in range(6)])
    vetoed = e0016.pass_rule(base, ablated, random_bad, bootstrap_seed=1)
    assert vetoed["pass"] is False
    assert vetoed["status"] == "INVALID_RANDOM"



def test_hf_rejects_renamed_arbitrary_xstest_csv(tmp_path):
    path = tmp_path / "xstest.csv"
    path.write_text(
        "id,prompt,type,label,focus,note\n"
        "s1,Safe benign prompt,safe,safe,general,\n"
        "u1,Unsafe prompt,unsafe,unsafe,general,\n"
        "s2,Another safe prompt,safe,safe,general,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="immutable content hash mismatch"):
        e0016.load_xstest_items(
            path, backend="hf", split_seed=1, dev_n=1, test_n=1
        )


def test_hf_rejects_renamed_arbitrary_contrast_csvs(tmp_path):
    harmful = tmp_path / "harmful_behaviors.csv"
    harmless = tmp_path / "alpaca.csv"
    harmful.write_text("goal,target\n[unsafe-class placeholder A],x\n[unsafe-class placeholder B],x\n", encoding="utf-8")
    harmless.write_text("instruction\nPlan a picnic\nExplain photosynthesis\n", encoding="utf-8")
    with pytest.raises(ValueError, match="immutable content hash mismatch"):
        e0016.load_contrast_prompts(
            None,
            backend="hf",
            harmful_source=str(harmful),
            harmless_source=str(harmless),
            direction_n=2,
        )


def test_default_dataset_sources_are_ungated_choices():
    assert e0016.DEFAULT_XSTEST_SOURCE == "Paul/XSTest:train"
    assert "llm-attacks" in e0016.DEFAULT_HARMFUL_SOURCE
    assert "walledai" not in e0016.DEFAULT_XSTEST_SOURCE.lower()
    assert "walledai" not in e0016.DEFAULT_HARMFUL_SOURCE.lower()
    assert e0016.DEFAULT_HARMLESS_SOURCE == "tatsu-lab/alpaca:train:instruction"


def _frozen_hf_args(tmp_path, *extra):
    return e0016.parse_args(
        [
            "--backend",
            "hf",
            "--out-dir",
            str(tmp_path),
            "--dev-n",
            str(e0016.HF_FROZEN_DEV_N),
            "--test-n",
            str(e0016.HF_FROZEN_TEST_N),
            "--k",
            str(e0016.HF_FROZEN_K),
            "--layers",
            ",".join(str(x) for x in e0016.HF_FROZEN_CANDIDATE_LAYERS),
            "--direction-n",
            str(e0016.HF_FROZEN_DIRECTION_N),
            "--max-new-tokens",
            str(e0016.HF_FROZEN_MAX_NEW_TOKENS),
            *extra,
        ]
    )


def test_hf_rejects_smoke_or_non_frozen_config_before_model_load(tmp_path, monkeypatch):
    args = e0016.parse_args(["--backend", "hf", "--out-dir", str(tmp_path)])
    monkeypatch.setattr(
        e0016,
        "build_shared_hf_handles",
        lambda *a, **k: pytest.fail("model load must not occur"),
    )
    with pytest.raises(ValueError, match="complete frozen"):
        e0016.run(args)


def test_hf_frozen_config_accepts_only_exact_identity(tmp_path):
    args = _frozen_hf_args(tmp_path)
    e0016.assert_hf_frozen_config(args)
    args.layers = "8,12,16"
    with pytest.raises(ValueError, match="complete frozen"):
        e0016.assert_hf_frozen_config(args)


def test_hf_hook_bites_are_persisted_before_first_dev_generation(
    tmp_path, monkeypatch
):
    events = []
    args = _frozen_hf_args(tmp_path)
    dev = _items(e0016.HF_FROZEN_DEV_N, "dev")
    test = _items(e0016.HF_FROZEN_TEST_N, "test")
    xprov = {
        "dataset_id": e0016.XSTEST_SPEC.dataset_id,
        "revision": e0016.XSTEST_SPEC.revision,
        "split": e0016.XSTEST_SPEC.split,
        "content_sha256": e0016.XSTEST_SPEC.content_sha256,
        "schema": list(e0016.XSTEST_SPEC.schema),
    }
    cprov = {
        "harmful_source": {
            "dataset_id": e0016.HARMFUL_SPEC.dataset_id,
            "revision": e0016.HARMFUL_SPEC.revision,
            "split": e0016.HARMFUL_SPEC.split,
            "content_sha256": e0016.HARMFUL_SPEC.content_sha256,
            "schema": list(e0016.HARMFUL_SPEC.schema),
        },
        "harmless_source": {
            "dataset_id": e0016.HARMLESS_SPEC.dataset_id,
            "revision": e0016.HARMLESS_SPEC.revision,
            "split": e0016.HARMLESS_SPEC.split,
            "content_sha256": e0016.HARMLESS_SPEC.content_sha256,
            "schema": list(e0016.HARMLESS_SPEC.schema),
        },
    }

    class Provider:
        hidden_dim = 16
        _config = SimpleNamespace(_commit_hash=e0016.FROZEN_MODEL_REVISION)

    class HookBackend:
        decoder_layer_indices = [1, 2]

        def capture_ablation_hook_bites(self, *a, **k):
            events.append("hook")
            return {
                layer: {
                    "max_abs_before": 1.0,
                    "max_abs_after": 0.0,
                    "mean_abs_before": 1.0,
                    "mean_abs_after": 0.0,
                    "n_values": 1,
                    "violation_count": 0,
                    "max_violation": 0.0,
                }
                for layer in self.decoder_layer_indices
            }

    hook_backend = HookBackend()
    handles = e0016.SharedHFHandles(
        provider=Provider(),
        hook_backend=hook_backend,
        device="cpu",
        dtype="float32",
    )
    bundles = [
        e0016.DirectionBundle(
            direction=unit_vector(np.arange(1, 17, dtype=float) + layer),
            source_layer=layer,
            position="last_token",
            provenance={
                "direction_sha256": f"dir-{layer}",
                "selected_layer_separation": 1.0,
            },
        )
        for layer in e0016.HF_FROZEN_CANDIDATE_LAYERS
    ]
    monkeypatch.setattr(
        e0016, "load_xstest_items", lambda *a, **k: (dev, test, xprov)
    )
    monkeypatch.setattr(
        e0016,
        "load_contrast_prompts",
        lambda *a, **k: (["harm"] * 64, ["safe"] * 64, cprov),
    )
    monkeypatch.setattr(e0016, "build_shared_hf_handles", lambda *a, **k: handles)
    monkeypatch.setattr(e0016, "derive_refusal_direction", lambda *a, **k: bundles)
    monkeypatch.setattr(e0016, "assert_real_not_smoke", lambda *a, **k: None)

    def stop_on_dev(*a, **k):
        guard = tmp_path / "e0016_pre_generation_guards.json"
        assert guard.exists()
        assert json.loads(guard.read_text(encoding="utf-8"))[
            "generation_started"
        ] is False
        events.append("generation")
        return e0016.EvalResult(
            "baseline",
            np.zeros((e0016.HF_FROZEN_DEV_N, e0016.HF_FROZEN_K)),
            np.zeros((e0016.HF_FROZEN_DEV_N, e0016.HF_FROZEN_K)),
            ["h"] * e0016.HF_FROZEN_DEV_N,
        )

    monkeypatch.setattr(e0016, "eval_hf", stop_on_dev)
    payload = e0016.run(args)
    assert payload["status"] == "INVALID_REGIME_B_UNDERPOWERED"
    assert events == ["hook", "hook", "hook", "hook", "generation"]


def test_runner_stops_before_test_when_dev_is_underpowered(tmp_path, monkeypatch):
    seen = []
    original = e0016.eval_synthetic

    def recording_eval(items, backend, condition, *, k):
        seen.append((condition, tuple(item.id for item in items)))
        return original(items, backend, condition, k=k)

    monkeypatch.setattr(e0016, "eval_synthetic", recording_eval)
    payload = e0016.run(
        e0016.parse_args(
            [
                "--backend",
                "synthetic",
                "--out-dir",
                str(tmp_path),
                "--dev-n",
                "4",
                "--test-n",
                "8",
                "--k",
                "2",
                "--synthetic-baseline-refusal-rate",
                "0",
            ]
        )
    )
    assert payload["status"] == "INVALID_REGIME_B_UNDERPOWERED"
    assert [condition for condition, _ in seen] == ["baseline"]
    test_ids = {item.id for item in _items(8, "test")}
    assert all(not (set(ids) & test_ids) for _, ids in seen)
    assert "test" not in payload


class _FakeTokenizer:
    pad_token = "<pad>"
    eos_token = "</s>"
    pad_token_id = 0
    padding_side = "left"

    def apply_chat_template(self, messages, **kwargs):
        return messages[0]["content"]

    def __call__(self, texts, **kwargs):
        import torch

        n = len(texts) if isinstance(texts, list) else 1
        return {
            "input_ids": torch.ones((n, 3), dtype=torch.long),
            "attention_mask": torch.ones((n, 3), dtype=torch.long),
        }


def _hook_backend(*, skip_last=False):
    torch = pytest.importorskip("torch")

    class Block(torch.nn.Module):
        def forward(self, hidden):
            return hidden + 0.25

    blocks = torch.nn.ModuleList([Block(), Block(), Block()])

    class Base(torch.nn.Module):
        def forward(self, input_ids, **kwargs):
            hidden = torch.nn.functional.one_hot(
                input_ids % 4, num_classes=4
            ).to(torch.float32)
            active = blocks[:-1] if skip_last else blocks
            for block in active:
                hidden = block(hidden)
            return SimpleNamespace(last_hidden_state=hidden)

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = Base()

    backend = e0016.SteeredHFBackend(
        "fake",
        model=Model(),
        tokenizer=_FakeTokenizer(),
        config=SimpleNamespace(hidden_size=4),
        layers=blocks,
    )
    return backend, blocks


def test_actual_hook_bites_passes_per_element_and_cleans_hooks():
    backend, blocks = _hook_backend()
    tol = 1e-5
    stats = backend.capture_ablation_hook_bites(
        ["probe"],
        e0016.AblationConfig(np.array([1.0, 0.0, 0.0, 0.0])),
        abs_tol=tol,
        rel_tol=0.05,
    )
    payload = e0016.assert_ablation_hook_bites(
        stats,
        expected_layers=backend.decoder_layer_indices,
        abs_tol=tol,
    )
    assert payload["observed_decoder_layers"] == [1, 2, 3]
    assert payload["violation_count"] == 0
    assert all(not block._forward_hooks for block in blocks)


def test_actual_hook_noop_is_rejected_and_hooks_are_cleaned(monkeypatch):
    backend, blocks = _hook_backend()
    monkeypatch.setattr(backend, "_apply_ablation", lambda hidden, vec: hidden)
    stats = backend.capture_ablation_hook_bites(
        ["probe"],
        e0016.AblationConfig(np.array([1.0, 0.0, 0.0, 0.0])),
        abs_tol=1e-5,
        rel_tol=0.05,
    )
    with pytest.raises(ValueError, match="failed"):
        e0016.assert_ablation_hook_bites(
            stats,
            expected_layers=backend.decoder_layer_indices,
            abs_tol=1e-5,
        )
    assert all(not block._forward_hooks for block in blocks)


def test_wrong_projection_is_rejected(monkeypatch):
    backend, _ = _hook_backend()

    def wrong_projection(hidden, vec):
        import torch

        wrong = torch.roll(vec, shifts=1)
        component = torch.sum(hidden * wrong, dim=-1, keepdim=True)
        return hidden - component * wrong

    monkeypatch.setattr(backend, "_apply_ablation", wrong_projection)
    stats = backend.capture_ablation_hook_bites(
        ["probe"],
        e0016.AblationConfig(np.array([1.0, 0.0, 0.0, 0.0])),
        abs_tol=1e-5,
        rel_tol=0.05,
    )
    with pytest.raises(ValueError, match="failed"):
        e0016.assert_ablation_hook_bites(
            stats,
            expected_layers=backend.decoder_layer_indices,
            abs_tol=1e-5,
        )


def test_missing_decoder_layer_is_rejected_and_hooks_are_cleaned():
    backend, blocks = _hook_backend(skip_last=True)
    stats = backend.capture_ablation_hook_bites(
        ["probe"],
        e0016.AblationConfig(np.array([1.0, 0.0, 0.0, 0.0])),
        abs_tol=1e-5,
        rel_tol=0.05,
    )
    with pytest.raises(ValueError, match="coverage mismatch"):
        e0016.assert_ablation_hook_bites(
            stats,
            expected_layers=backend.decoder_layer_indices,
            abs_tol=1e-5,
        )
    assert all(not block._forward_hooks for block in blocks)
