
import json
from copy import deepcopy
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


@pytest.mark.parametrize(
    ("point", "ci_lo", "coherent", "expected"),
    [
        (0.20, 0.01, True, "PARTIAL"),
        (0.00, 0.00, True, "FAIL"),
        (0.10, -0.01, True, "FAIL"),
        (-0.10, -0.20, True, "FAIL"),
        (0.30, 0.01, False, "INVALID_COHERENCE"),
        (0.25, 0.01, True, "PASS"),
    ],
)
def test_preregistered_runtime_status_boundaries(
    monkeypatch, point, ci_lo, coherent, expected
):
    base = e0016.EvalResult(
        "baseline", np.ones((4, 1)), np.zeros((4, 1)), ["h"] * 4
    )
    ablated = e0016.EvalResult(
        "ablation",
        np.zeros((4, 1)),
        np.zeros((4, 1)) if coherent else np.ones((4, 1)),
        ["h"] * 4,
    )
    random_null = e0016.EvalResult(
        "random", np.ones((4, 1)), np.zeros((4, 1)), ["h"] * 4
    )
    cis = iter(
        [
            SimpleNamespace(
                point=point,
                ci_lo=ci_lo,
                ci_hi=max(point, ci_lo) + 0.1,
                ci_level=0.95,
                b=10000,
            ),
            SimpleNamespace(
                point=0.0,
                ci_lo=-0.1,
                ci_hi=0.1,
                ci_level=0.95,
                b=10000,
            ),
        ]
    )
    monkeypatch.setattr(e0016.adj, "cluster_bootstrap_ci", lambda *a, **k: next(cis))
    result = e0016.pass_rule(base, ablated, random_null)
    assert result["status"] == expected


def test_random_pass_is_invalid_even_when_ablation_passes(monkeypatch):
    result = _pass_rule_with_fixed_cis(
        monkeypatch,
        ablation=(0.30, 0.01),
        random=(0.30, 0.01),
    )
    assert result["status"] == "INVALID_RANDOM"
    assert result["pass"] is False


def _pass_rule_with_fixed_cis(monkeypatch, *, ablation, random):
    base = e0016.EvalResult(
        "baseline", np.ones((4, 1)), np.zeros((4, 1)), ["h"] * 4
    )
    changed = e0016.EvalResult(
        "changed", np.zeros((4, 1)), np.zeros((4, 1)), ["h"] * 4
    )
    cis = iter(
        [
            SimpleNamespace(
                point=ablation[0],
                ci_lo=ablation[1],
                ci_hi=ablation[0] + 0.1,
                ci_level=0.95,
                b=10000,
            ),
            SimpleNamespace(
                point=random[0],
                ci_lo=random[1],
                ci_hi=random[0] + 0.1,
                ci_level=0.95,
                b=10000,
            ),
        ]
    )
    monkeypatch.setattr(e0016.adj, "cluster_bootstrap_ci", lambda *a, **k: next(cis))
    return e0016.pass_rule(base, changed, changed)



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


def test_hf_rejects_arbitrary_seed_before_model_or_data_load(tmp_path, monkeypatch):
    args = _frozen_hf_args(tmp_path, "--seed", "999")
    monkeypatch.setattr(
        e0016,
        "load_xstest_items",
        lambda *a, **k: pytest.fail("data load must not occur"),
    )
    monkeypatch.setattr(
        e0016,
        "build_shared_hf_handles",
        lambda *a, **k: pytest.fail("model load must not occur"),
    )
    with pytest.raises(ValueError, match="complete frozen"):
        e0016.run(args)


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
        max_length = e0016.HF_PROVIDER_MAX_LENGTH
        _config = SimpleNamespace(_commit_hash=e0016.FROZEN_MODEL_REVISION)

    class HookBackend:
        decoder_layer_indices = [1, 2]
        max_length = e0016.HF_BACKEND_MAX_LENGTH
        num_hidden_layers = 2

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
        guard_payload = json.loads(guard.read_text(encoding="utf-8"))
        assert guard_payload["frozen_config"]["identity_stage"] == (
            "post_resolution_full_run"
        )
        assert guard_payload["frozen_config_hash"] == e0016.config_hash(
            guard_payload["frozen_config"]
        )
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
        config=SimpleNamespace(hidden_size=4, num_hidden_layers=3),
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


def test_truncated_decoder_module_list_fails_at_production_backend_init():
    torch = pytest.importorskip("torch")

    class Block(torch.nn.Module):
        def forward(self, hidden):
            return hidden

    blocks = torch.nn.ModuleList([Block(), Block(), Block()])

    class Base(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = blocks

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = Base()

    with pytest.raises(ValueError, match="config declares 4.*has 3"):
        e0016.SteeredHFBackend(
            "fake",
            model=Model(),
            tokenizer=_FakeTokenizer(),
            config=SimpleNamespace(hidden_size=4, num_hidden_layers=4),
        )


@pytest.mark.parametrize(
    "depth",
    [
        None,
        0,
        -1,
        3.5,
        "3",
        True,
        float("nan"),
        np.int64(3),
        np.float64(3.0),
    ],
)
def test_production_backend_rejects_non_strict_decoder_depth(depth):
    torch = pytest.importorskip("torch")

    class Block(torch.nn.Module):
        def forward(self, hidden):
            return hidden

    blocks = torch.nn.ModuleList([Block(), Block(), Block()])

    class Base(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = blocks

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = Base()

    config = SimpleNamespace(hidden_size=4)
    if depth is not None:
        config.num_hidden_layers = depth
    with pytest.raises(ValueError, match="decoder depth|must be"):
        e0016.SteeredHFBackend(
            "fake",
            model=Model(),
            tokenizer=_FakeTokenizer(),
            config=config,
        )


def test_production_backend_rejects_extra_decoder_module():
    torch = pytest.importorskip("torch")

    class Block(torch.nn.Module):
        def forward(self, hidden):
            return hidden

    blocks = torch.nn.ModuleList([Block(), Block(), Block(), Block()])

    class Base(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = blocks

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = Base()

    with pytest.raises(ValueError, match="config declares 3.*has 4"):
        e0016.SteeredHFBackend(
            "fake",
            model=Model(),
            tokenizer=_FakeTokenizer(),
            config=SimpleNamespace(hidden_size=4, num_hidden_layers=3),
        )


def test_all_layer_hook_registration_rolls_back_on_second_layer_failure(
    monkeypatch,
):
    backend, blocks = _hook_backend()

    def fail_registration(*args, **kwargs):
        raise RuntimeError("second layer registration failed")

    monkeypatch.setattr(blocks[1], "register_forward_hook", fail_registration)
    with pytest.raises(RuntimeError, match="second layer"):
        backend._register_all_layer_ablation_hooks(
            e0016.AblationConfig(np.array([1.0, 0.0, 0.0, 0.0]))
        )
    assert all(not block._forward_hooks for block in blocks)


def test_supported_alternate_config_depth_field_is_accepted():
    torch = pytest.importorskip("torch")

    class Block(torch.nn.Module):
        def forward(self, hidden):
            return hidden

    blocks = torch.nn.ModuleList([Block(), Block()])

    class Base(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = blocks

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.model = Base()

    backend = e0016.SteeredHFBackend(
        "fake",
        model=Model(),
        tokenizer=_FakeTokenizer(),
        config=SimpleNamespace(hidden_size=4, n_layer=2),
    )
    assert backend.decoder_layer_indices == [1, 2]


def _resolved_config_fixture(tmp_path):
    args = _frozen_hf_args(tmp_path)
    dev = _items(e0016.HF_FROZEN_DEV_N, "dev")
    test = _items(e0016.HF_FROZEN_TEST_N, "test")
    xprov = {
        "dataset_id": e0016.XSTEST_SPEC.dataset_id,
        "revision": e0016.XSTEST_SPEC.revision,
        "split": e0016.XSTEST_SPEC.split,
        "content_path": e0016.XSTEST_SPEC.content_path,
        "content_sha256": e0016.XSTEST_SPEC.content_sha256,
        "schema": list(e0016.XSTEST_SPEC.schema),
        "safe_filter": "type/label/annotation/focus safe and not unsafe/harm",
        "safe_prompt_hashes_sha256": "safe-pool-hash",
    }
    cprov = {
        "harmful_source": {
            "dataset_id": e0016.HARMFUL_SPEC.dataset_id,
            "revision": e0016.HARMFUL_SPEC.revision,
            "split": e0016.HARMFUL_SPEC.split,
            "content_path": e0016.HARMFUL_SPEC.content_path,
            "content_sha256": e0016.HARMFUL_SPEC.content_sha256,
            "schema": list(e0016.HARMFUL_SPEC.schema),
        },
        "harmless_source": {
            "dataset_id": e0016.HARMLESS_SPEC.dataset_id,
            "revision": e0016.HARMLESS_SPEC.revision,
            "split": e0016.HARMLESS_SPEC.split,
            "content_path": e0016.HARMLESS_SPEC.content_path,
            "content_sha256": e0016.HARMLESS_SPEC.content_sha256,
            "schema": list(e0016.HARMLESS_SPEC.schema),
        },
        "harmful_hashes_sha256": "harm-used",
        "harmless_hashes_sha256": "safe-used",
        "count_harmful_used": e0016.HF_FROZEN_DIRECTION_N,
        "count_harmless_used": e0016.HF_FROZEN_DIRECTION_N,
    }
    kwargs = {
        "xstest_prov": xprov,
        "contrast_prov": cprov,
        "dev": dev,
        "test": test,
        "model_revision_resolved": e0016.FROZEN_MODEL_REVISION,
        "device": "cuda:1",
        "dtype": "float16",
        "provider_max_length": e0016.HF_PROVIDER_MAX_LENGTH,
        "backend_max_length": e0016.HF_BACKEND_MAX_LENGTH,
        "hidden_dim": 3584,
        "declared_decoder_layers": 28,
    }
    return e0016.resolved_frozen_run_config(args, **kwargs)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("seed",), 999),
        (("data", "xstest", "content_sha256"), "other-data"),
        (("model", "revision_resolved"), "other-model"),
        (("runtime", "device"), "cpu"),
        (("runtime", "dtype"), "bfloat16"),
        (("runtime", "generation_backend_max_length"), 1024),
        (("generation", "temperature"), 0.9),
        (("generation", "batch_scheme"), "per-item"),
        (("dev_n",), 61),
        (("candidate_layers",), [4, 8]),
        (("statistics", "bootstrap_b"), 999),
        (("statistics", "pass_delta"), 0.2),
        (("random_control", "seed"), 999),
        (("hook_all_layer_recipe", "abs_tol"), 1e-5),
        (("scorers", "refusal_version"), "v2"),
        (("split_identity", "test", "item_ids_sha256"), "other-split"),
    ],
)
def test_resolved_frozen_config_hash_covers_identity_categories(
    tmp_path, path, replacement
):
    config = _resolved_config_fixture(tmp_path)
    baseline_hash = e0016.config_hash(config)
    assert baseline_hash == e0016.config_hash(deepcopy(config))
    mutated = deepcopy(config)
    cursor = mutated
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = replacement
    assert e0016.config_hash(mutated) != baseline_hash


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("selected_intervention", "source_layer"), 12),
        (("selected_intervention", "position"), "first_token"),
        (("selected_intervention", "direction_sha256"), "other-direction"),
    ],
)
def test_finalized_identity_hash_is_stable_and_selected_intervention_sensitive(
    tmp_path, path, replacement
):
    resolved = _resolved_config_fixture(tmp_path)
    selected = e0016.DirectionBundle(
        direction=np.ones(4),
        source_layer=8,
        position="last_token",
        provenance={"direction_sha256": "selected-direction"},
    )
    dev_payload = {
        "status": "ELIGIBLE",
        "baseline_false_refusal_rate": 0.5,
        "selected": {
            "source_layer": 8,
            "position": "last_token",
            "direction_sha256": "selected-direction",
            "mean_reduction": 0.3,
            "coherence_ok": True,
            "random_mean_reduction": 0.0,
        },
        "selection_rows": [{"source_layer": 8, "mean_reduction": 0.3}],
    }
    identity = e0016.finalized_run_identity(resolved, selected, dev_payload)
    baseline_hash = e0016.config_hash(identity)
    assert baseline_hash == e0016.config_hash(deepcopy(identity))
    mutated = deepcopy(identity)
    cursor = mutated
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = replacement
    assert e0016.config_hash(mutated) != baseline_hash


def test_finalized_identity_is_persisted_before_test_and_used_by_artifact(
    tmp_path, monkeypatch
):
    calls = []
    dev_ids = None
    original = e0016.eval_synthetic

    def recording_eval(items, backend, condition, *, k):
        nonlocal dev_ids
        calls.append(condition)
        item_ids = tuple(item.id for item in items)
        if dev_ids is None:
            dev_ids = item_ids
        if item_ids != dev_ids:
            identity_path = tmp_path / "e0016_finalized_run_identity.json"
            manifest_path = tmp_path / "e0016_ablation_positive_control_results.json"
            selection_path = tmp_path / "e0016_dev_selection_manifest.json"
            assert identity_path.exists()
            assert manifest_path.exists()
            assert selection_path.exists()
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            selection = json.loads(selection_path.read_text(encoding="utf-8"))
            final_hash = identity["finalized_run_identity_hash"]
            assert identity["test_generation_started"] is False
            assert identity["valid_for_paper"] is False
            assert manifest["finalized_run_identity_hash"] == final_hash
            assert selection["finalized_run_identity_hash"] == final_hash
            assert manifest["artifact_identity"] == {
                "experiment_id": e0016.EXPERIMENT_ID,
                "finalized_run_identity_hash": final_hash,
            }
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
            ]
        )
    )
    assert payload["finalized_run_identity_hash"] == payload["artifact_identity"][
        "finalized_run_identity_hash"
    ]
    assert payload["valid_for_paper"] is False
