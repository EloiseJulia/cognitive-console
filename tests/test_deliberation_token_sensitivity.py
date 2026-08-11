import json
import math
import os
import shutil
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from cognitive_console.steering.generate import (
    GenerationTrace,
    generation_trace_from_token_ids,
)
from scripts import run_deliberation_token_sensitivity as S


class _Tokenizer:
    def decode(self, token_ids, skip_special_tokens=True):
        ids = [int(token_id) for token_id in token_ids]
        if skip_special_tokens:
            ids = [token_id for token_id in ids if token_id != 2]
        return " ".join(str(token_id) for token_id in ids)


def test_generation_trace_distinguishes_equal_cap_from_cap_stop():
    cap_stop = generation_trace_from_token_ids(
        list(range(64)),
        tokenizer=_Tokenizer(),
        max_new_tokens=64,
        eos_token_ids=[2],
    )
    assert cap_stop.generated_token_count == 3
    assert cap_stop.visible_token_count == 2
    assert cap_stop.raw_continuation_width == 64
    assert cap_stop.stop_reason == "eos"
    assert cap_stop.hit_max_new_tokens is False

    no_eos = generation_trace_from_token_ids(
        [100 + index for index in range(64)],
        tokenizer=_Tokenizer(),
        max_new_tokens=64,
        eos_token_ids=[2],
    )
    assert no_eos.generated_token_count == 64
    assert no_eos.visible_token_count == 64
    assert no_eos.stop_reason == "max_new_tokens"
    assert no_eos.hit_max_new_tokens is True

    eos_at_cap = generation_trace_from_token_ids(
        [100 + index for index in range(63)] + [2],
        tokenizer=_Tokenizer(),
        max_new_tokens=64,
        eos_token_ids=[2],
    )
    assert eos_at_cap.generated_token_count == 64
    assert eos_at_cap.visible_token_count == 63
    assert eos_at_cap.stop_reason == "eos"
    assert eos_at_cap.hit_max_new_tokens is False


def test_original_batch_composition_is_three_items_times_five_samples():
    items = [{"id": f"item-{index}"} for index in range(40)]
    chunks = list(S.iter_original_batches(items, batch_size=16))
    assert [len(chunk) for chunk in chunks[:-1]] == [3] * 13
    assert len(chunks[-1]) == 1
    assert all(len(chunk) * S.adj.K_SAMPLES <= 16 for chunk in chunks)


def _cfg(cell_key):
    method, model_label = cell_key.split("__", 1)
    return S.FrozenCellConfig(
        cell_key=cell_key,
        method=method,
        model_label=model_label,
        model_id=f"/models/{model_label}",
        layer=1,
        frozen_alpha=2.0,
        best_prompt_id="p1",
        best_prompt_text="Think.",
        neutral_prompt="Answer.",
        sigma=1.0,
        source_result_file=f"results/{cell_key}.json",
        source_result_sha256=f"sha-{cell_key}",
        source_config_fingerprint=f"fp-{cell_key}",
        source_mean_diff=0.0,
        source_ci_lo=0.0,
        source_ci_hi=0.0,
        source_passed=False,
        source_per_item_prompt=(0.0,) * 40,
        source_per_item_steer=(0.0,) * 40,
    )


def _record(
    cfg,
    cap,
    condition,
    item_id,
    *,
    correct,
    hit,
    answer,
    token_ids,
    explicit_answer=None,
):
    if explicit_answer is None:
        explicit_answer = answer is not None
    return {
        "cell": cfg.cell_key,
        "condition": condition,
        "max_new_tokens": cap,
        "item_id": item_id,
        "sample_index": 0,
        "generated_token_count": len(token_ids),
        "visible_token_count": len(token_ids),
        "raw_continuation_width": len(token_ids),
        "stop_reason": "max_new_tokens" if hit else "eos",
        "hit_max_new_tokens": hit,
        "token_ids": token_ids,
        "parsed_final_number": answer,
        "frozen_parser_number_present": answer is not None,
        "frozen_parser_failed": answer is None,
        "explicit_or_terminal_final_answer_present": explicit_answer,
        "correct": correct,
        "degeneracy": 0.0,
    }


def test_analysis_detects_same_seed_continuation_that_changes_comparison():
    configs = {cell_key: _cfg(cell_key) for cell_key in S.FROZEN_CELL_KEYS}
    records = []
    prefix = [100 + index for index in range(64)]
    for cfg in configs.values():
        for item_id in (f"item-{index:02d}" for index in range(40)):
            for condition in S.CONDITIONS:
                records.append(
                    _record(
                        cfg,
                        64,
                        condition,
                        item_id,
                        correct=0,
                        hit=(condition == "prompt"),
                        answer=None,
                        token_ids=prefix if condition == "prompt" else [10, 2],
                    )
                )
                for cap in (128, 256):
                    prompt_recovers = condition == "prompt"
                    records.append(
                        _record(
                            cfg,
                            cap,
                            condition,
                            item_id,
                            correct=int(prompt_recovers),
                            hit=False,
                            answer=42.0 if prompt_recovers else None,
                            token_ids=(
                                prefix + [999, 2]
                                if prompt_recovers
                                else [10, 2]
                            ),
                        )
                    )

    analysis = S.analyse(records, configs, bootstrap_b=200, seed=20260723)
    assert (
        analysis["overall_outcome_branch"]
        == "DISTORTION_AFFECTS_STEER_VS_PROMPT_COMPARISON"
    )
    row = analysis["cells"][S.FROZEN_CELL_KEYS[0]]
    assert row["cap_64_reproduction_gate"]["passed"] is True
    continuation = row["paired_cap_comparisons"]["128"][
        "continuation_materiality_among_64_cap_stops"
    ]["prompt"]
    assert continuation["all_prefixes_match"] is True
    assert (
        continuation["n_continuation_added_explicit_or_terminal_final_answer"]
        == 40
    )
    assert continuation["n_correctness_recovered"] == 40
    assert continuation["n_operational_semantic_truncation_evidence"] == 40
    assert (
        continuation["operational_semantic_truncation_evidence_present"] is True
    )
    assert math.isclose(
        row["paired_cap_comparisons"]["128"][
            "cap_by_condition_accuracy_interaction"
        ]["point"],
        -1.0,
    )
    assert analysis["estimand_contract"]["primary_family_size"] == 24
    assert (
        row["paired_cap_comparisons"]["128"][
            "cap_by_condition_accuracy_interaction"
        ]["multiplicity_method"]
        == "joint-item-cluster bootstrap max-T"
    )


def test_final_answer_diagnostic_is_independent_of_frozen_parser_fallback():
    item = {"id": "i", "answer": "3"}
    incidental = S.score_generation(
        "I first counted 3 cases, then continued reasoning without a conclusion",
        item,
    )
    assert incidental["frozen_parser_number_present"] is True
    assert incidental["explicit_or_terminal_final_answer_present"] is False

    terminal = S.score_generation("After checking the work, 3.", item)
    assert terminal["explicit_or_terminal_final_answer_present"] is True
    explicit = S.score_generation("Final answer: 3", item)
    assert explicit["explicit_or_terminal_final_answer_present"] is True


def test_continuation_ci_handles_zero_cap_stop_denominator():
    cfg = _cfg(S.FROZEN_CELL_KEYS[0])
    records = []
    for item_id in ("i1", "i2"):
        for cap in S.CAPS:
            for condition in S.CONDITIONS:
                records.append(
                    _record(
                        cfg,
                        cap,
                        condition,
                        item_id,
                        correct=0,
                        hit=False,
                        answer=None,
                        token_ids=[10, 2],
                    )
                )
    row = S._continuation_materiality(
        records,
        long_cap=128,
        bootstrap_b=50,
        seed=S.DEFAULT_SEED,
    )["prompt"]
    assert row["n_64_cap_stops_compared"] == 0
    assert row["all_prefixes_match"] is None
    rate = row["conditional_rates_ci_95_item_cluster"][
        "operational_semantic_evidence"
    ]
    assert rate["defined"] is False
    assert rate["zero_denominator"] is True
    assert rate["ci_lo"] is None


def test_loads_all_frozen_deliberation_configs():
    frozen_root = Path(__file__).resolve().parents[1] / "results" / "arm_full"
    configs = {
        cell_key: S.load_frozen_cell_config(frozen_root, cell_key)
        for cell_key in S.FROZEN_CELL_KEYS
    }
    assert all(len(cfg.source_per_item_prompt) == 40 for cfg in configs.values())
    assert all(len(cfg.source_per_item_steer) == 40 for cfg in configs.values())
    assert all(cfg.source_passed is False for cfg in configs.values())
    lineage = S.frozen_lineage_inventory(
        frozen_root, configs, seed=S.DEFAULT_SEED
    )
    assert lineage["original_decision"] == "0/12"
    assert lineage["arm_summary"]["n_passed"] == 0
    assert lineage["arm_summary"]["n_decisions"] == 12
    identity = S.load_item_identity()
    assert identity["identity_status"] == "ORDERED_IDS_PROVEN_CONTENT_RECONSTRUCTED"
    assert len(identity["ordered_pool_ids"]) == 60
    assert len(identity["ordered_test_ids"]) == 40


class _CheckpointBackend:
    def __init__(self, fail_on_call=None):
        self.calls = 0
        self.fail_on_call = fail_on_call

    def generate_batch_with_metadata(
        self,
        prompts,
        steer,
        *,
        max_new_tokens,
        seeds,
        do_sample,
        temperature,
    ):
        self.calls += 1
        if self.calls == self.fail_on_call:
            raise RuntimeError("synthetic interruption")
        return [
            GenerationTrace(
                text="Answer: 2",
                token_ids=[101, 2],
                generated_token_count=2,
                visible_token_count=1,
                raw_continuation_width=2,
                stop_reason="eos",
                hit_max_new_tokens=False,
                eos_token_id=2,
            )
            for _ in prompts
        ]


def _scratch_dir(name):
    path = Path(__file__).resolve().parent / f".e0017-{name}-{os.getpid()}"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


def test_fixed_batch_checkpoint_resumes_without_regenerating_completed_batch():
    cfg = _cfg(S.FROZEN_CELL_KEYS[0])
    items = [
        {"id": f"item-{index}", "prompt": "What is 1+1?", "answer": "2"}
        for index in range(4)
    ]
    root = _scratch_dir("checkpoint")
    checkpoint = root / "condition.json"
    identity = {"run": "synthetic", "cell": cfg.cell_key}
    try:
        with pytest.raises(RuntimeError, match="synthetic interruption"):
            S.generate_condition(
                backend=_CheckpointBackend(fail_on_call=2),
                cfg=cfg,
                direction=np.ones(4),
                model_id=cfg.model_id,
                cap=64,
                condition="prompt",
                test_items=items,
                seed=S.DEFAULT_SEED,
                temperature=S.DEFAULT_TEMPERATURE,
                batch_size=S.DEFAULT_BATCH_SIZE,
                checkpoint_path=checkpoint,
                checkpoint_identity=identity,
            )
        partial = json.loads(checkpoint.read_text(encoding="utf-8"))
        assert partial["complete"] is False
        assert partial["record_count"] == 3 * S.adj.K_SAMPLES

        resumed_backend = _CheckpointBackend()
        records = S.generate_condition(
            backend=resumed_backend,
            cfg=cfg,
            direction=np.ones(4),
            model_id=cfg.model_id,
            cap=64,
            condition="prompt",
            test_items=items,
            seed=S.DEFAULT_SEED,
            temperature=S.DEFAULT_TEMPERATURE,
            batch_size=S.DEFAULT_BATCH_SIZE,
            checkpoint_path=checkpoint,
            checkpoint_identity=identity,
        )
        assert resumed_backend.calls == 1
        assert len(records) == 4 * S.adj.K_SAMPLES
        complete = json.loads(checkpoint.read_text(encoding="utf-8"))
        assert complete["complete"] is True
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_test_once_seal_reuses_completed_analysis_and_detects_mutation():
    root = _scratch_dir("test-once")
    seal = root / "test_once_analysis.json"
    analysis_path = root / "analysis.json"
    summary_path = root / "analysis.md"
    manifest_path = root / "run_manifest.json"
    raw_inputs = {"sample_files": [{"path": "samples/a.jsonl", "sha256": "abc"}]}
    analysis_spec = {"bootstrap_b": 10000, "seed": S.DEFAULT_SEED}
    analysis = {
        "experiment_id": S.EXPERIMENT_ID,
        "overall_outcome_branch": "INCONCLUSIVE_FIXED_N",
    }
    try:
        assert (
            S._prepare_test_once_analysis(
                seal_path=seal,
                raw_inputs=raw_inputs,
                analysis_spec=analysis_spec,
                analysis_path=analysis_path,
                summary_path=summary_path,
                manifest_path=manifest_path,
            )
            is None
        )
        S._write_json(analysis_path, analysis)
        S._mark_test_once_analysis_written(
            seal_path=seal,
            analysis_path=analysis_path,
        )
        S._write_text_atomic(summary_path, "# summary\n")
        S._write_json(manifest_path, {"experiment_id": S.EXPERIMENT_ID})
        S._complete_test_once_analysis(
            seal_path=seal,
            analysis_path=analysis_path,
            summary_path=summary_path,
            manifest_path=manifest_path,
        )
        assert (
            S._prepare_test_once_analysis(
                seal_path=seal,
                raw_inputs=raw_inputs,
                analysis_spec=analysis_spec,
                analysis_path=analysis_path,
                summary_path=summary_path,
                manifest_path=manifest_path,
            )
            == analysis
        )
        S._write_json(analysis_path, {**analysis, "tampered": True})
        with pytest.raises(ValueError, match="completed TEST-once output mismatch"):
            S._prepare_test_once_analysis(
                seal_path=seal,
                raw_inputs=raw_inputs,
                analysis_spec=analysis_spec,
                analysis_path=analysis_path,
                summary_path=summary_path,
                manifest_path=manifest_path,
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _write_model_metadata(snapshot):
    for name in (
        "config.json",
        "generation_config.json",
        "tokenizer_config.json",
        "tokenizer.json",
    ):
        (snapshot / name).write_text("{}", encoding="utf-8")


def test_model_snapshot_hashes_all_shards_and_rejects_index_path_attack():
    root = _scratch_dir("model-hash")
    revision = "a" * 40
    snapshot = root / revision
    snapshot.mkdir()
    _write_model_metadata(snapshot)
    (snapshot / "model-00001-of-00002.safetensors").write_bytes(b"one")
    (snapshot / "model-00002-of-00002.safetensors").write_bytes(b"two")
    index = {
        "weight_map": {
            "a": "model-00001-of-00002.safetensors",
            "b": "model-00002-of-00002.safetensors",
        }
    }
    (snapshot / "model.safetensors.index.json").write_text(
        json.dumps(index),
        encoding="utf-8",
    )
    try:
        identity = S._hash_model_snapshot(
            snapshot,
            repo_id="owner/model",
            revision=revision,
        )
        assert identity["all_weight_shards_hashed"] is True
        assert len(identity["weight_shards"]) == 2
        assert all(row["sha256"] for row in identity["weight_shards"])

        index["weight_map"]["b"] = "../model-00002-of-00002.safetensors"
        (snapshot / "model.safetensors.index.json").write_text(
            json.dumps(index),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="unsafe weight shard"):
            S._hash_model_snapshot(
                snapshot,
                repo_id="owner/model",
                revision=revision,
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_cli_rejects_same_basename_model_attack():
    args = S.build_parser().parse_args(
        [
            "--dry-run",
            "--qwen-model",
            r"C:\attacker\Qwen2.5-7B-Instruct",
        ]
    )
    with pytest.raises(SystemExit, match="qwen-model"):
        S._validate_args(args)


def _authorization(out_dir, registry_path):
    return {
        "owner_authorization": {
            "authorization_id": "AUTH-1",
            "max_gpu_hours": 3.0,
            "approved_gpu_uuid": "GPU-1234",
        },
        "designated_host": {
            "hostname": "host",
            "canonical_out_dir": str(out_dir),
            "attempt_registry_path": str(registry_path),
        },
    }


def test_global_attempt_registry_rejects_cross_out_dir_retry():
    root = _scratch_dir("attempt-registry")
    registry_path = root / "control" / "attempt.json"
    out_one = root / "out-one"
    out_two = root / "out-two"
    first = S.CanonicalAttemptRegistry(
        registry_path,
        authorization=_authorization(out_one, registry_path),
        authorization_sha256="auth-sha",
        source_commit="a" * 40,
        out_dir=out_one,
    )
    try:
        first.acquire()
        first.start()
        assert json.loads(registry_path.read_text(encoding="utf-8"))["status"] == "STARTED"
        first.mark_failed(RuntimeError("synthetic failure"))
        assert json.loads(registry_path.read_text(encoding="utf-8"))["status"] == "FAILED"
    finally:
        first.release()

    resumed = S.CanonicalAttemptRegistry(
        registry_path,
        authorization=_authorization(out_one, registry_path),
        authorization_sha256="auth-sha",
        source_commit="a" * 40,
        out_dir=out_one,
    )
    try:
        resumed.acquire()
        resumed.start()
        resumed.mark_complete({"seal": "abc"})
        assert json.loads(registry_path.read_text(encoding="utf-8"))["status"] == "COMPLETE"
    finally:
        resumed.release()

    second = S.CanonicalAttemptRegistry(
        registry_path,
        authorization=_authorization(out_one, registry_path),
        authorization_sha256="auth-sha",
        source_commit="a" * 40,
        out_dir=out_two,
    )
    try:
        second.acquire()
        with pytest.raises(RuntimeError, match="cross-out-dir"):
            second.start()
    finally:
        second.release()
        shutil.rmtree(root, ignore_errors=True)


def test_gpu_gate_rejects_busy_device_and_cpu_fallback(monkeypatch):
    authorization = {
        "owner_authorization": {
            "approved_gpu_uuid": "GPU-1234",
            "approved_gpu_name": "NVIDIA A800 80GB PCIe",
        }
    }
    gpu = {
        "index": 0,
        "uuid": "GPU-1234",
        "name": "NVIDIA A800 80GB PCIe",
        "memory_total_mib": 81920,
        "memory_used_mib": 0,
        "utilization_gpu_pct": 0,
    }
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "GPU-1234")
    monkeypatch.setenv("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "1")
    monkeypatch.setattr(S.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        S,
        "_query_gpu_state",
        lambda: (
            [gpu],
            [
                {
                    "gpu_uuid": "GPU-1234",
                    "pid": 99,
                    "process_name": "other",
                    "used_gpu_memory_mib": 1,
                }
            ],
        ),
    )
    with pytest.raises(RuntimeError, match="not idle"):
        S._verify_idle_a800(authorization)

    monkeypatch.setattr(S, "_query_gpu_state", lambda: ([gpu], []))
    fake_torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(
            is_available=lambda: False,
            device_count=lambda: 0,
            get_device_name=lambda _: "",
        )
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    with pytest.raises(RuntimeError, match="CPU fallback is forbidden|exactly one"):
        S._verify_idle_a800(authorization)
