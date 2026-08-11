
import json
import os
import shutil
from copy import deepcopy
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest
from tokenizers import AddedToken

from cognitive_console.activations import provider as activation_provider_module
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
    assert e0016.HARMLESS_SPEC.schema == (
        "instruction",
        "input",
        "output",
        "text",
    )
    assert e0016.HARMLESS_SPEC.expected_row_count == 52002


@pytest.mark.parametrize(
    ("name", "total_gib", "expected"),
    [
        ("NVIDIA A800 80GB PCIe", 79.1, "nvidia-a800-80gb"),
        (
            "NVIDIA GeForce RTX 4080 SUPER",
            31.9,
            "autodl-rtx4080-super-32gb",
        ),
    ],
)
def test_authorized_hardware_profiles_accept_a800_or_autodl_32gb(
    name, total_gib, expected
):
    assert (
        e0016.select_authorized_hardware_profile(name, total_gib).profile_id
        == expected
    )


@pytest.mark.parametrize(
    ("name", "total_gib"),
    [
        ("NVIDIA GeForce RTX 4080 SUPER", 15.9),
        ("NVIDIA RTX 4090", 23.9),
        ("NVIDIA A100-SXM4-80GB", 79.1),
    ],
)
def test_hardware_profile_rejects_unapproved_name_or_memory(name, total_gib):
    with pytest.raises(ValueError, match="unauthorized GPU hardware profile"):
        e0016.select_authorized_hardware_profile(name, total_gib)


def test_visible_gpu_binding_maps_exact_physical_identity():
    rows = e0016._parse_nvidia_smi_rows(
        "0, GPU-aaa, 00000000:01:00.0, NVIDIA GeForce RTX 4080 SUPER, 32768, 32000\n"
        "1, GPU-bbb, 00000000:02:00.0, NVIDIA A800 80GB PCIe, 81920, 80000\n"
    )
    selected = e0016._select_physical_gpu_row(rows, "0")
    assert selected["uuid"] == "GPU-aaa"
    assert selected["pci_bus_id"] == "00000000:01:00.0"
    with pytest.raises(ValueError, match="did not bind"):
        e0016._select_physical_gpu_row(rows, "GPU-missing")


def test_gpu_visibility_must_bind_exactly_one_device(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0,1")
    with pytest.raises(ValueError, match="exactly one"):
        e0016._single_visible_gpu_selector()


def test_transformers_4442_uses_compatible_torch_dtype_keyword(monkeypatch):
    monkeypatch.setattr(
        activation_provider_module.importlib.metadata,
        "version",
        lambda name: "4.44.2",
    )
    marker = object()
    assert activation_provider_module._transformers_model_dtype_kwargs(marker) == {
        "torch_dtype": marker
    }


def test_autodl_cache_paths_are_all_bound_under_hf_home(tmp_path, monkeypatch):
    hf_home = tmp_path / "hf"
    out_dir = tmp_path / "E-0016-autodl"
    profile = e0016.HardwareProfile(
        profile_id="test-autodl",
        accepted_name_fragments=("GPU",),
        min_total_vram_gib=1.0,
        max_total_vram_gib=None,
        min_free_before_load_gib=1.0,
        min_free_after_load_gib=1.0,
        managed_disk_ceiling_gib=45.0,
        filesystem_free_reserve_gib=5.0,
        required_hf_home=hf_home,
        required_output_root=tmp_path,
    )
    monkeypatch.setenv("HF_HOME", str(hf_home))
    for key in (
        "HF_HUB_CACHE",
        "HUGGINGFACE_HUB_CACHE",
        "TRANSFORMERS_CACHE",
        "HF_DATASETS_CACHE",
    ):
        monkeypatch.delenv(key, raising=False)
    identity = e0016.configure_hf_cache_environment(profile, out_dir)
    assert Path(identity["hf_hub_cache"]).parent == hf_home.resolve()
    assert Path(identity["datasets_cache"]).parent == hf_home.resolve()
    assert Path(identity["out_dir"]) == out_dir.resolve()


def test_disk_guard_hard_fails_at_profile_ceiling(tmp_path, monkeypatch):
    profile = e0016.HardwareProfile(
        profile_id="test-disk",
        accepted_name_fragments=("GPU",),
        min_total_vram_gib=1.0,
        max_total_vram_gib=None,
        min_free_before_load_gib=1.0,
        min_free_after_load_gib=1.0,
        managed_disk_ceiling_gib=45.0,
        filesystem_free_reserve_gib=5.0,
    )
    hf_home = tmp_path / "hf"
    hf_home.mkdir()
    out_dir = tmp_path / "E-0016-run"
    monkeypatch.setattr(
        e0016, "dir_size_bytes", lambda path: int(45 * 1024**3)
    )
    with pytest.raises(ValueError, match="hard ceiling"):
        e0016.check_managed_disk_guard(
            profile,
            {"hf_home": str(hf_home)},
            out_dir,
            stage="after_model_load",
        )


def test_frozen_snapshot_revision_and_shard_hashes_are_verified(
    tmp_path, monkeypatch
):
    snapshot = tmp_path / e0016.FROZEN_MODEL_REVISION
    snapshot.mkdir()
    shard_bytes = {"a.safetensors": b"alpha", "b.safetensors": b"beta"}
    frozen = {}
    for name, raw in shard_bytes.items():
        (snapshot / name).write_bytes(raw)
        frozen[name] = {"size": len(raw), "sha256": e0016._sha256_bytes(raw)}
    (snapshot / "model.safetensors.index.json").write_text(
        json.dumps({"weight_map": {"a": "a.safetensors", "b": "b.safetensors"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(e0016, "FROZEN_MODEL_SHARDS", frozen)
    monkeypatch.setitem(
        __import__("sys").modules,
        "huggingface_hub",
        SimpleNamespace(snapshot_download=lambda **kwargs: str(snapshot)),
    )
    identity = e0016.verify_frozen_model_snapshot(
        model_id=e0016.DEFAULT_MODEL,
        revision=e0016.FROZEN_MODEL_REVISION,
        hf_hub_cache=tmp_path,
        config=SimpleNamespace(_commit_hash=e0016.FROZEN_MODEL_REVISION),
    )
    assert identity["resolved_revision"] == e0016.FROZEN_MODEL_REVISION
    assert identity["all_shard_sha256_verified"] is True


def test_raw_harmful_local_source_cannot_live_in_git_worktree(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(e0016, "_REPO", tmp_path)
    source = tmp_path / "harmful_behaviors.csv"
    source.write_text("goal,target\n[raw-harmful-sentinel],x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden inside the git worktree"):
        e0016.assert_harmful_local_source_not_in_repo(source)
    repo_ignore = Path(__file__).resolve().parents[1] / ".gitignore"
    assert "**/harmful_behaviors.csv" in repo_ignore.read_text(encoding="utf-8")


def test_contrast_provenance_contains_hashes_not_raw_harmful_text(tmp_path):
    source = tmp_path / "contrast.jsonl"
    source.write_text(
        "\n".join(
            [
                json.dumps(
                    {"prompt": "[raw-harmful-sentinel]", "label": "harmful"}
                ),
                json.dumps({"prompt": "Plan a picnic", "label": "harmless"}),
            ]
        ),
        encoding="utf-8",
    )
    harmful, _, provenance = e0016.load_contrast_prompts(
        source,
        backend="synthetic",
        harmful_source="unused",
        harmless_source="unused",
        direction_n=1,
    )
    assert harmful == ["[raw-harmful-sentinel]"]
    assert "[raw-harmful-sentinel]" not in json.dumps(provenance)
    assert provenance["raw_harmful_prompts_committed"] is False


def test_preflight_and_dev_only_flags_do_not_change_frozen_science_identity(
    tmp_path,
):
    preflight = _frozen_hf_args(tmp_path, "--preflight-only")
    dev_only = _frozen_hf_args(tmp_path, "--stop-after-dev")
    assert e0016.pre_load_eligibility_config(
        preflight
    ) == e0016.pre_load_eligibility_config(dev_only)


def _frozen_hf_args(tmp_path, *extra):
    return e0016.parse_args(
        [
            "--backend",
            "hf",
            "--out-dir",
            str(tmp_path / "E-0016-unit-test"),
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
    args.generation_batch_size = 2
    with pytest.raises(ValueError, match="complete frozen"):
        e0016.assert_hf_frozen_config(args)
    args.generation_batch_size = e0016.HF_FROZEN_GENERATION_BATCH_SIZE
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

    class Config:
        _commit_hash = e0016.FROZEN_MODEL_REVISION

        def to_dict(self):
            return {"_commit_hash": self._commit_hash}

    class Provider:
        hidden_dim = 16
        max_length = e0016.HF_PROVIDER_MAX_LENGTH
        _config = Config()

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
    operational_identity = {
        "profile_id": "nvidia-a800-80gb",
        "cuda_visible_devices": "0",
        "logical_device": "cuda:0",
        "physical_gpu": {
            "physical_index": 0,
            "uuid": "GPU-test",
            "pci_bus_id": "00000000:01:00.0",
            "name": "NVIDIA A800 80GB PCIe",
            "total_memory_mib": 81920,
            "free_memory_mib": 80000,
            "torch_device_name": "NVIDIA A800 80GB PCIe",
            "torch_total_vram_gib": 80.0,
            "compute_capability": [8, 0],
        },
        "runtime": {
            "python": "3.12.0",
            "torch": "2.8.0",
            "torch_cuda_runtime": "12.8",
            "transformers": "4.44.2",
        },
        "cuda_allocator": {
            "environment_variable": "PYTORCH_CUDA_ALLOC_CONF",
            "value": "expandable_segments:True",
        },
        "cache": {
            "hf_home": str(tmp_path / "hf"),
            "hf_hub_cache": str(tmp_path / "hf" / "hub"),
            "transformers_cache": str(tmp_path / "hf" / "hub"),
            "datasets_cache": str(tmp_path / "hf" / "datasets"),
            "out_dir": str(tmp_path),
            "managed_disk_ceiling_gib": 70.0,
            "filesystem_free_reserve_gib": 5.0,
        },
        "disk_policy": {
            "managed_hard_ceiling_gib": 70.0,
            "filesystem_free_reserve_gib": 5.0,
        },
        "model_snapshot": {
            "requested_revision": e0016.FROZEN_MODEL_REVISION,
            "resolved_revision": e0016.FROZEN_MODEL_REVISION,
            "all_shard_sha256_verified": True,
        },
    }
    handles = e0016.SharedHFHandles(
        provider=Provider(),
        hook_backend=hook_backend,
        device="cpu",
        dtype="float32",
        operational_preflight=operational_identity,
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
    monkeypatch.setattr(
        e0016,
        "capture_authorized_hardware_preflight",
        lambda: (e0016.AUTHORIZED_HARDWARE_PROFILES[0], operational_identity),
    )
    monkeypatch.setattr(
        e0016, "configure_cuda_allocator_environment", lambda: "test"
    )
    monkeypatch.setattr(
        e0016,
        "configure_hf_cache_environment",
        lambda *a, **k: operational_identity["cache"],
    )
    monkeypatch.setattr(
        e0016,
        "check_managed_disk_guard",
        lambda *a, stage, **k: {"stage": stage},
    )
    monkeypatch.setattr(
        e0016,
        "check_cuda_memory_headroom",
        lambda *a, stage, **k: {"stage": stage},
    )
    monkeypatch.setattr(e0016, "derive_refusal_direction", lambda *a, **k: bundles)
    monkeypatch.setattr(e0016, "assert_real_not_smoke", lambda *a, **k: None)

    def stop_on_dev(*a, **k):
        guard = Path(args.out_dir) / "e0016_pre_generation_guards.json"
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

    def recording_eval(items, backend, condition, *, k, **kwargs):
        seen.append((condition, tuple(item.id for item in items)))
        return original(items, backend, condition, k=k, **kwargs)

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
        (("data", "harmless", "loaded_rows_sha256"), "other-loaded-rows"),
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
    selected_direction = np.ones(4)
    selected_sha256 = e0016.vector_sha256(selected_direction)
    selected = e0016.DirectionBundle(
        direction=selected_direction,
        source_layer=8,
        position="last_token",
        provenance={"direction_sha256": selected_sha256},
    )
    dev_payload = {
        "status": "ELIGIBLE",
        "baseline_false_refusal_rate": 0.5,
        "selected": {
            "source_layer": 8,
            "position": "last_token",
            "direction_sha256": selected_sha256,
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

    def recording_eval(items, backend, condition, *, k, **kwargs):
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
            assert manifest["artifact_identity"]["experiment_id"] == e0016.EXPERIMENT_ID
            assert manifest["artifact_identity"]["finalized_run_identity_hash"] == final_hash
            assert manifest["artifact_identity"]["artifact_identity_sha256"]
        return original(items, backend, condition, k=k, **kwargs)

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


class _DeterministicBatchBackend:
    def __init__(self, *, fail_on_call=None):
        self.batch_sizes = []
        self.calls = 0
        self.fail_on_call = fail_on_call

    @staticmethod
    def _texts(seeds):
        return [
            (
                "I cannot help with that request."
                if int(seed) % 2
                else f"Benign deterministic answer {seed}."
            )
            for seed in seeds
        ]

    def generate_batch(self, prompts, **kwargs):
        self.calls += 1
        self.batch_sizes.append(len(prompts))
        if self.calls == self.fail_on_call:
            raise RuntimeError("injected generation interruption")
        return self._texts(kwargs["seeds"])

    def generate_batch_with_ablation(self, prompts, ablation, **kwargs):
        return self.generate_batch(prompts, **kwargs)


def test_hf_microbatch_is_bounded_and_batch_partition_invariant():
    items = _items(5)
    first = _DeterministicBatchBackend()
    second = _DeterministicBatchBackend()
    result_two = e0016.eval_hf(
        items,
        first,
        "baseline",
        None,
        k=2,
        max_new_tokens=8,
        seed=17,
        generation_batch_size=2,
    )
    result_four = e0016.eval_hf(
        items,
        second,
        "baseline",
        None,
        k=2,
        max_new_tokens=8,
        seed=17,
        generation_batch_size=4,
    )
    assert max(first.batch_sizes) <= 2
    assert max(second.batch_sizes) <= 4
    assert result_two.records == result_four.records


def test_checkpoint_resume_converges_and_repeated_resume_is_idempotent(tmp_path):
    items = _items(4)
    checkpoint = tmp_path / "resume.json"
    identity = {
        "config_hash": "cfg",
        "finalized_run_identity_hash": e0016.config_hash({"final": 1}),
        "condition": "baseline",
    }
    interrupted = _DeterministicBatchBackend(fail_on_call=2)
    with pytest.raises(RuntimeError, match="interruption"):
        e0016.eval_hf(
            items,
            interrupted,
            "baseline",
            None,
            k=2,
            max_new_tokens=8,
            seed=19,
            generation_batch_size=2,
            checkpoint_path=checkpoint,
            checkpoint_identity=identity,
        )
    partial = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert len(partial["records"]) == 2
    resumed = e0016.eval_hf(
        items,
        _DeterministicBatchBackend(),
        "baseline",
        None,
        k=2,
        max_new_tokens=8,
        seed=19,
        generation_batch_size=2,
        checkpoint_path=checkpoint,
        checkpoint_identity=identity,
    )
    uninterrupted = e0016.eval_hf(
        items,
        _DeterministicBatchBackend(),
        "baseline",
        None,
        k=2,
        max_new_tokens=8,
        seed=19,
        generation_batch_size=2,
        checkpoint_identity=identity,
    )
    assert resumed.records == uninterrupted.records
    repeated = e0016.eval_hf(
        items,
        pytest.fail,
        "baseline",
        None,
        k=2,
        max_new_tokens=8,
        seed=19,
        generation_batch_size=2,
        checkpoint_path=checkpoint,
        checkpoint_identity=identity,
    )
    assert repeated.records == resumed.records


def test_checkpoint_rejects_config_or_finalized_identity_mismatch(tmp_path):
    checkpoint = tmp_path / "mismatch.json"
    identity = {
        "config_hash": "cfg-a",
        "finalized_run_identity_hash": e0016.config_hash({"final": "a"}),
        "condition": "baseline",
    }
    e0016.eval_hf(
        _items(2),
        _DeterministicBatchBackend(),
        "baseline",
        None,
        k=1,
        max_new_tokens=8,
        seed=23,
        checkpoint_path=checkpoint,
        checkpoint_identity=identity,
    )
    mutated = dict(
        identity, finalized_run_identity_hash=e0016.config_hash({"final": "b"})
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        e0016.eval_hf(
            _items(2),
            _DeterministicBatchBackend(),
            "baseline",
            None,
            k=1,
            max_new_tokens=8,
            seed=23,
            checkpoint_path=checkpoint,
            checkpoint_identity=mutated,
        )


def test_selected_direction_copy_rejects_alias_and_post_finalize_mutation():
    original = unit_vector(np.arange(1, 9, dtype=float))
    copied = e0016.immutable_direction(original)
    expected = e0016.vector_sha256(copied)
    original[0] += 5.0
    assert e0016.vector_sha256(copied) == expected
    with pytest.raises(ValueError):
        copied[0] += 1.0
    copied.setflags(write=True)
    copied[0] += 1.0
    with pytest.raises(ValueError, match="direction hash mismatch"):
        e0016.eval_hf(
            _items(1),
            pytest.fail,
            "ablation",
            copied,
            k=1,
            max_new_tokens=8,
            seed=29,
            expected_direction_sha256=expected,
        )


def test_synthetic_artifact_reconstructs_all_statistics_from_benign_text(
    tmp_path,
):
    args = e0016.parse_args(
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
            "--generation-batch-size",
            "3",
        ]
    )
    payload = e0016.run(args)
    records_path = tmp_path / payload["generation_records_artifact"]["path"]
    assert (
        e0016._sha256_bytes(records_path.read_bytes())
        == payload["generation_records_artifact"]["artifact_file_sha256"]
    )
    artifact = json.loads(records_path.read_text(encoding="utf-8"))
    rebuilt = e0016.reconstruct_test_from_generation_artifact(
        artifact,
        seed=args.seed,
        expected_artifact_identity=payload["artifact_identity"],
        expected_finalized_run_identity=payload["finalized_run_identity"],
    )
    assert rebuilt["test"] == payload["test"]
    assert rebuilt["test_baseline"]["mean_refusal"] == payload["test_baseline"][
        "mean_refusal"
    ]
    assert rebuilt["test_ablation"]["mean_refusal"] == payload["test_ablation"][
        "mean_refusal"
    ]
    assert rebuilt["test_random"]["mean_refusal"] == payload["test_random"][
        "mean_refusal"
    ]
    assert rebuilt["ci_inputs"]["ablation_reductions"]
    serialized = records_path.read_text(encoding="utf-8")
    assert "Benign safe prompt" not in serialized
    assert '"prompt":' not in serialized
    assert '"output_text":' in serialized
    assert all(
        row["output_text_encoding"] == "utf-8"
        and row["output_content_class"] == "benign_xstest_safe_generation"
        and e0016.sha_text(row["output_text"]) == row["output_sha256"]
        for row in artifact["records"]
    )
    assert artifact["harmful_generation_performed"] is False
    before = records_path.read_bytes()
    repeated = e0016.run(args)
    assert records_path.read_bytes() == before
    assert repeated["generation_records_artifact"]["artifact_file_sha256"] == payload[
        "generation_records_artifact"
    ]["artifact_file_sha256"]


def test_synthetic_result_affecting_config_is_identity_bound(tmp_path):
    first = e0016.parse_args(
        [
            "--backend",
            "synthetic",
            "--out-dir",
            str(tmp_path),
            "--synthetic-baseline-refusal-rate",
            "0.75",
        ]
    )
    second = e0016.parse_args(
        [
            "--backend",
            "synthetic",
            "--out-dir",
            str(tmp_path),
            "--synthetic-baseline-refusal-rate",
            "0.5",
        ]
    )
    assert e0016.config_hash(e0016.pre_load_eligibility_config(first)) != (
        e0016.config_hash(e0016.pre_load_eligibility_config(second))
    )
    hf = _frozen_hf_args(tmp_path)
    assert "synthetic" not in e0016.pre_load_eligibility_config(hf)
    e0016.run(first)
    with pytest.raises(ValueError, match="different config/code identity"):
        e0016.run(second)


@pytest.mark.parametrize("seed", ["20260804", 20260804.0, True, np.int64(20260804), -1])
def test_hf_frozen_seed_requires_nonnegative_genuine_integer(seed, tmp_path):
    args = _frozen_hf_args(tmp_path)
    args.seed = seed
    with pytest.raises(ValueError, match="genuine integer|non-negative"):
        e0016.assert_hf_frozen_config(args)


def test_verified_parquet_bytes_are_the_only_rows_loaded(tmp_path, monkeypatch):
    raw = b"verified immutable parquet bytes"
    path = tmp_path / "alpaca.parquet"
    path.write_bytes(raw)
    spec = e0016.ImmutableDataSpec(
        name="test_alpaca",
        canonical_source="repo:train",
        dataset_id="repo",
        revision="rev",
        split="train",
        content_path="data.parquet",
        content_sha256=e0016._sha256_bytes(raw),
        schema=("instruction", "input", "output"),
        format="parquet",
        column="instruction",
        expected_row_count=1,
    )
    parsed = [
        {
            "instruction": "verified row",
            "input": "",
            "output": "verified output",
        }
    ]
    monkeypatch.setattr(e0016, "_parse_parquet_bytes", lambda value: parsed if value == raw else pytest.fail("wrong bytes"))
    rows, provenance = e0016._load_immutable_hf_rows(path, spec)
    assert rows == parsed
    assert provenance["count_loaded"] == 1
    assert provenance["loaded_rows_sha256"] == e0016._canonical_rows_sha256(
        parsed, spec.schema
    )


def _completed_artifact(tmp_path):
    args = e0016.parse_args(
        ["--backend", "synthetic", "--out-dir", str(tmp_path)]
    )
    manifest = e0016.run(args)
    artifact = json.loads(
        (tmp_path / "e0016_generation_records.json").read_text(encoding="utf-8")
    )
    return args, manifest, artifact


def _artifact_load_kwargs(manifest):
    return {
        "seed": manifest["seed"],
        "expected_artifact_identity": manifest["artifact_identity"],
        "expected_finalized_run_identity": manifest["finalized_run_identity"],
        "expected_environment_identity": manifest["environment_identity"],
        "expected_full_config_hash": manifest["pre_load_eligibility_config_hash"],
        "expected_frozen_config_hash": manifest["frozen_config_hash"],
        "expected_data_identity_hash": e0016.config_hash(
            manifest["frozen_config"]["data"]
        ),
    }


def test_output_directory_rejects_traversal_and_source_hiding():
    with pytest.raises(ValueError, match="traversal"):
        e0016.resolve_output_directory(Path("results") / ".." / "src")
    with pytest.raises(ValueError, match="exact results"):
        e0016.resolve_output_directory(e0016._REPO / "src" / "hidden-output")
    with pytest.raises(ValueError, match="dedicated"):
        e0016.assert_dedicated_output_directory(
            e0016._REPO / "results", backend="hf"
        )
    with pytest.raises(ValueError, match="direct dedicated"):
        e0016.assert_dedicated_output_directory(
            e0016._REPO / "results" / "parent" / "E-0016-run", backend="hf"
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("degeneracy_score", -0.1),
        ("degeneracy_score", float("nan")),
        ("degeneracy_score", float("inf")),
        ("output_sha256", "not-a-hash"),
        ("refusal_score", 1),
        ("item_id", "forged-item"),
        ("condition", "extra-condition"),
        ("sample_index", 99),
        ("seed", 99),
        ("item_prompt_sha256", "0" * 64),
        ("direction_sha256_actual_used", "1" * 64),
    ],
)
def test_strict_record_validator_rejects_scientific_mutations(
    tmp_path, field, value
):
    _, manifest, artifact = _completed_artifact(tmp_path)
    mutated = deepcopy(artifact)
    row = next(
        record
        for record in mutated["records"]
        if field != "direction_sha256_actual_used"
        or record["condition"] == "ablation"
    )
    row[field] = value
    with pytest.raises(ValueError):
        e0016.reconstruct_test_from_generation_artifact(
            mutated,
            seed=e0016.HF_FROZEN_SEED,
            expected_artifact_identity=manifest["artifact_identity"],
        )


def test_strict_record_validator_rejects_flipped_refusal(tmp_path):
    _, manifest, artifact = _completed_artifact(tmp_path)
    mutated = deepcopy(artifact)
    mutated["records"][0]["refusal_score"] = not mutated["records"][0][
        "refusal_score"
    ]
    mutated["records_sha256"] = e0016.config_hash(mutated["records"])
    mutated["records"][0]["record_identity_sha256"] = e0016._record_identity(
        mutated["records"][0]
    )
    mutated["records_sha256"] = e0016.config_hash(mutated["records"])
    with pytest.raises(ValueError, match="current frozen scorer"):
        e0016.reconstruct_test_from_generation_artifact(
            mutated,
            seed=e0016.HF_FROZEN_SEED,
            expected_artifact_identity=manifest["artifact_identity"],
        )


def test_record_text_hash_and_rescore_are_independently_enforced(tmp_path):
    _, manifest, artifact = _completed_artifact(tmp_path)
    changed_text = deepcopy(artifact)
    changed_text["records"][0]["output_text"] += " modified"
    changed_text["records"][0]["record_identity_sha256"] = e0016._record_identity(
        changed_text["records"][0]
    )
    changed_text["records_sha256"] = e0016.config_hash(changed_text["records"])
    with pytest.raises(ValueError, match="text/hash"):
        e0016.reconstruct_test_from_generation_artifact(
            changed_text,
            seed=manifest["seed"],
            expected_artifact_identity=manifest["artifact_identity"],
        )

    rehashed = deepcopy(artifact)
    row = rehashed["records"][0]
    row["output_text"] = (
        "Here is a plain safe answer."
        if row["refusal_score"]
        else "I cannot help with that request."
    )
    row["output_sha256"] = e0016.sha_text(row["output_text"])
    row["record_identity_sha256"] = e0016._record_identity(row)
    rehashed["records_sha256"] = e0016.config_hash(rehashed["records"])
    with pytest.raises(ValueError, match="current frozen scorer"):
        e0016.reconstruct_test_from_generation_artifact(
            rehashed,
            seed=manifest["seed"],
            expected_artifact_identity=manifest["artifact_identity"],
        )


def test_strict_record_validator_rejects_unknown_duplicate_extra_and_missing(
    tmp_path,
):
    _, manifest, artifact = _completed_artifact(tmp_path)
    identity = manifest["artifact_identity"]

    unknown = deepcopy(artifact)
    unknown["records"][0]["unknown"] = True
    unknown["records_sha256"] = e0016.config_hash(unknown["records"])
    with pytest.raises(ValueError, match="field set"):
        e0016.reconstruct_test_from_generation_artifact(
            unknown, seed=e0016.HF_FROZEN_SEED, expected_artifact_identity=identity
        )

    duplicate = deepcopy(artifact)
    duplicate["records"].append(deepcopy(duplicate["records"][0]))
    duplicate["records_sha256"] = e0016.config_hash(duplicate["records"])
    with pytest.raises(ValueError, match="duplicate"):
        e0016.reconstruct_test_from_generation_artifact(
            duplicate,
            seed=e0016.HF_FROZEN_SEED,
            expected_artifact_identity=identity,
        )

    extra = deepcopy(artifact)
    forged = deepcopy(extra["records"][0])
    forged["sample_identity_sha256"] = e0016.config_hash({"extra": True})
    forged["record_identity_sha256"] = e0016._record_identity(forged)
    extra["records"].append(forged)
    extra["records_sha256"] = e0016.config_hash(extra["records"])
    with pytest.raises(ValueError, match="not an expected"):
        e0016.reconstruct_test_from_generation_artifact(
            extra, seed=e0016.HF_FROZEN_SEED, expected_artifact_identity=identity
        )

    missing = deepcopy(artifact)
    missing["records"].pop()
    missing["records_sha256"] = e0016.config_hash(missing["records"])
    with pytest.raises(ValueError, match="exactly match"):
        e0016.reconstruct_test_from_generation_artifact(
            missing,
            seed=e0016.HF_FROZEN_SEED,
            expected_artifact_identity=identity,
        )


def test_checkpoint_validator_accepts_only_valid_strict_subset(tmp_path):
    _, _, artifact = _completed_artifact(tmp_path)
    subset = artifact["records"][:3]
    assert e0016.validate_generation_records(
        subset, artifact["test_plan"]["jobs"], allow_subset=True
    ) == subset
    with pytest.raises(ValueError, match="exactly match"):
        e0016.validate_generation_records(
            subset, artifact["test_plan"]["jobs"], allow_subset=False
        )


def test_checkpoint_rejects_gap_order_and_false_complete(tmp_path):
    _, _, artifact = _completed_artifact(tmp_path)
    jobs = artifact["test_plan"]["jobs"][:4]
    records = artifact["records"][:4]
    source = e0016.capture_source_state(None)
    identity = {"condition": "baseline", "environment_identity_hash": "sha256:" + "1" * 64}
    checkpoint = tmp_path / "checkpoint.json"

    for bad_records, complete, message in (
        ([records[0], records[2]], False, "prefix"),
        ([records[1], records[0]], False, "prefix"),
        (records[:2], True, "complete"),
    ):
        payload = e0016._checkpoint_payload(
            condition="baseline",
            checkpoint_identity=identity,
            run_start_source_state=source,
            expected_jobs_hash=e0016.config_hash(jobs),
            records=bad_records,
            complete=complete,
        )
        checkpoint.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            e0016._load_checkpoint(
                checkpoint,
                condition="baseline",
                checkpoint_identity=identity,
                run_start_source_state=source,
                expected_jobs=jobs,
                out_dir=None,
            )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda meta: meta.__setitem__("path", "forged.json"), "metadata"),
        (lambda meta: meta.__setitem__("manifest_schema_version", 99), "metadata"),
        (lambda meta: meta.__setitem__("record_count", 1), "record count|metadata"),
        (lambda meta: meta.__setitem__("expected_plan_hash", "sha256:" + "0" * 64), "metadata"),
        (lambda meta: meta.__setitem__("artifact_identity_sha256", "sha256:" + "0" * 64), "metadata"),
        (lambda meta: meta.__setitem__("environment_identity_hash", "sha256:" + "0" * 64), "metadata"),
    ],
)
def test_manifest_metadata_forgery_is_rejected(tmp_path, mutator, message):
    _, manifest, _ = _completed_artifact(tmp_path)
    forged = deepcopy(manifest)
    mutator(forged["generation_records_artifact"])
    with pytest.raises(ValueError, match=message):
        e0016.load_and_reconstruct_generation_artifact(
            tmp_path / "e0016_generation_records.json",
            forged,
            **_artifact_load_kwargs(manifest),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("seed", 123),
        ("condition", "extra"),
        ("direction_sha256_actual_used", "f" * 64),
    ],
)
def test_canonical_test_plan_rejects_seed_condition_and_direction_forgery(
    tmp_path, field, value
):
    _, manifest, artifact = _completed_artifact(tmp_path)
    forged = deepcopy(artifact)
    forged["test_plan"]["jobs"][0][field] = value
    plan_material = {
        key: val
        for key, val in forged["test_plan"].items()
        if key != "test_plan_hash"
    }
    forged["test_plan"]["test_plan_hash"] = e0016.config_hash(plan_material)
    forged["test_plan_hash"] = forged["test_plan"]["test_plan_hash"]
    with pytest.raises(ValueError, match="canonical rebuild"):
        e0016.reconstruct_test_from_generation_artifact(
            forged,
            seed=manifest["seed"],
            expected_artifact_identity=manifest["artifact_identity"],
        )


def test_environment_identity_mutation_rejects_resume(tmp_path, monkeypatch):
    args, _, _ = _completed_artifact(tmp_path)
    original = e0016._package_version

    def mutated(name):
        value = original(name)
        return "forged-version" if name == "numpy" else value

    monkeypatch.setattr(e0016, "_package_version", mutated)
    with pytest.raises(ValueError, match="environment identity changed"):
        e0016.run(args)


def test_added_token_nested_config_has_stable_semantic_identity():
    token = AddedToken(
        "<tool>",
        single_word=True,
        lstrip=True,
        rstrip=False,
        normalized=False,
        special=True,
    )
    original = {
        "nested": [{"token": token}, (token,)],
        "ordinary": "value",
    }
    reordered = {
        "ordinary": "value",
        "nested": [{"token": token}, (token,)],
    }

    canonical = e0016._canonical_identity_value(original)
    canonical_items = {
        entry["key"]["value"]: entry["value"] for entry in canonical["items"]
    }
    nested_items = {
        entry["key"]["value"]: entry["value"]
        for entry in canonical_items["nested"][0]["items"]
    }
    token_identity = nested_items["token"]
    assert token_identity == {
        "__type__": "tokenizers.AddedToken",
        "content": "<tool>",
        "single_word": True,
        "lstrip": True,
        "rstrip": False,
        "normalized": False,
        "special": True,
    }
    assert canonical_items["nested"][1]["__type__"] == "builtins.tuple"
    assert e0016._object_config_identity(original) == e0016._object_config_identity(
        reordered
    )
    assert original["nested"][0]["token"] is token
    assert token.content == "<tool>"


def test_added_token_semantic_field_change_changes_identity_hash():
    base = AddedToken("<tool>", normalized=False, special=True)
    changed = AddedToken("<tool>", normalized=True, special=True)
    assert (
        e0016._object_config_identity({"token": base})["sha256"]
        != e0016._object_config_identity({"token": changed})["sha256"]
    )


def test_environment_identity_serializer_rejects_unknown_objects():
    with pytest.raises(TypeError, match="unsupported non-JSON object"):
        e0016._object_config_identity({"unknown": object()})


def test_dictionary_key_types_are_collision_free_and_order_stable():
    assert (
        e0016._object_config_identity({1: "value"})["sha256"]
        != e0016._object_config_identity({"1": "value"})["sha256"]
    )
    assert (
        e0016._object_config_identity({1: "value"})["sha256"]
        != e0016._object_config_identity({2: "value"})["sha256"]
    )
    assert (
        e0016._object_config_identity({True: "value"})["sha256"]
        != e0016._object_config_identity({1: "value"})["sha256"]
    )
    assert (
        e0016._object_config_identity({1.0: "value"})["sha256"]
        != e0016._object_config_identity({1: "value"})["sha256"]
    )
    assert (
        e0016._object_config_identity({None: "value"})["sha256"]
        != e0016._object_config_identity({"None": "value"})["sha256"]
    )
    original = {2: "two", "1": "one", None: "none", False: "false", 1.5: "float"}
    reordered = dict(reversed(list(original.items())))
    assert e0016._object_config_identity(original) == e0016._object_config_identity(
        reordered
    )


def test_environment_identity_serializer_rejects_complex_dictionary_keys():
    with pytest.raises(TypeError, match="unsupported dictionary key"):
        e0016._object_config_identity({("complex",): "value"})
    with pytest.raises(TypeError, match="float keys must be finite"):
        e0016._object_config_identity({float("nan"): "value"})


def test_cpu_hf_environment_identity_accepts_real_pretrained_config(monkeypatch):
    from transformers import PretrainedConfig

    token = AddedToken(
        "<tool>",
        single_word=True,
        lstrip=True,
        normalized=False,
        special=True,
    )

    class Tokenizer:
        init_kwargs = {"added_tokens": [{"tool": token}]}
        special_tokens_map = {"additional_special_tokens": [token]}

        @staticmethod
        def get_vocab():
            return {"<tool>": 1, "plain": 0}

    config = PretrainedConfig(num_labels=3)
    assert all(type(key) is int for key in config.to_dict()["id2label"])
    model = SimpleNamespace(generation_config={"do_sample": True})
    backend = SimpleNamespace(
        _model=model,
        _tokenizer=Tokenizer(),
        _config=config,
    )
    monkeypatch.setattr(e0016, "_package_version", lambda name: f"{name}-test")

    identity = e0016.capture_environment_identity(
        backend="hf",
        provider=SimpleNamespace(_config={"hidden_size": 4}),
        hook_backend=backend,
    )

    assert identity["schema_version"] == 4
    assert identity["environment_identity_hash"].startswith("sha256:")
    assert identity["hf_runtime"]["tokenizer_config"]["bytes"] > 0


def test_artifact_identity_and_manifest_hash_chain_reject_forgery(tmp_path):
    args, manifest, artifact = _completed_artifact(tmp_path)
    forged = deepcopy(artifact)
    forged["artifact_identity"]["artifact_identity_sha256"] = e0016.config_hash(
        {"forged": True}
    )
    with pytest.raises(ValueError, match="identity"):
        e0016.reconstruct_test_from_generation_artifact(
            forged,
            seed=args.seed,
            expected_artifact_identity=manifest["artifact_identity"],
        )
    records_path = tmp_path / "e0016_generation_records.json"
    records_path.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(ValueError, match="file hash"):
        e0016.load_and_reconstruct_generation_artifact(
            records_path,
            manifest,
            seed=args.seed,
            expected_artifact_identity=manifest["artifact_identity"],
            expected_finalized_run_identity=manifest["finalized_run_identity"],
            expected_environment_identity=manifest["environment_identity"],
            expected_full_config_hash=manifest["pre_load_eligibility_config_hash"],
            expected_frozen_config_hash=manifest["frozen_config_hash"],
            expected_data_identity_hash=e0016.config_hash(
                manifest["frozen_config"]["data"]
            ),
        )


def test_complete_valid_artifact_reconstruction_is_unchanged(tmp_path):
    args, manifest, artifact = _completed_artifact(tmp_path)
    rebuilt = e0016.reconstruct_test_from_generation_artifact(
        deepcopy(artifact),
        seed=args.seed,
        expected_artifact_identity=manifest["artifact_identity"],
    )
    assert rebuilt["test"] == manifest["test"]


def test_production_entry_interruption_resume_and_source_mutation_rejection(
    tmp_path, monkeypatch
):
    token = f"pytest-{os.getpid()}-{tmp_path.name}"
    resume_dir = e0016._REPO / "results" / f"E-0016-{token}-resume"
    clean_dir = tmp_path / "clean"
    shutil.rmtree(resume_dir, ignore_errors=True)
    shutil.rmtree(clean_dir, ignore_errors=True)
    original_generate = e0016.SyntheticRegimeBBackend.generate
    calls = {"count": 0}

    def interrupt_once(self, item, condition, sample):
        calls["count"] += 1
        if calls["count"] == 3:
            raise RuntimeError("production-entry interruption")
        return original_generate(self, item, condition, sample)

    mutation = e0016._REPO / f"e0016_source_mutation_{os.getpid()}.py"
    try:
        clean = e0016.run(
            e0016.parse_args(
                ["--backend", "synthetic", "--out-dir", str(clean_dir)]
            )
        )
        monkeypatch.setattr(
            e0016.SyntheticRegimeBBackend, "generate", interrupt_once
        )
        args = e0016.parse_args(
            ["--backend", "synthetic", "--out-dir", str(resume_dir)]
        )
        with pytest.raises(RuntimeError, match="production-entry interruption"):
            e0016.run(args)
        checkpoints = list((resume_dir / "checkpoints").rglob("*.json"))
        assert checkpoints
        assert any(
            0 < len(json.loads(path.read_text(encoding="utf-8"))["records"])
            for path in checkpoints
        )

        monkeypatch.setattr(
            e0016.SyntheticRegimeBBackend, "generate", original_generate
        )
        resumed = e0016.run(args)
        resumed_artifact = json.loads(
            (resume_dir / "e0016_generation_records.json").read_text(
                encoding="utf-8"
            )
        )
        clean_artifact = json.loads(
            (clean_dir / "e0016_generation_records.json").read_text(
                encoding="utf-8"
            )
        )
        assert resumed_artifact == clean_artifact
        assert resumed["test"] == clean["test"]

        mutation.write_text("SOURCE_MUTATION = True\n", encoding="utf-8")
        with pytest.raises(ValueError, match="source state changed"):
            e0016.run(args)
    finally:
        mutation.unlink(missing_ok=True)
        shutil.rmtree(resume_dir, ignore_errors=True)
        shutil.rmtree(clean_dir, ignore_errors=True)
