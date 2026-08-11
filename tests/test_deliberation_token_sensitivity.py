import json
import math
import os
import shutil
import sys
import types
from datetime import datetime, timedelta, timezone
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


def test_prereg_status_rejects_unfrozen_substring():
    assert S._parse_prereg_status(
        S.PREREG_PATH.read_text(encoding="utf-8")
    )[0] == "DRAFT"
    assert S._parse_prereg_status(
        "Status: FROZEN / AUDIT-READY / NOT RUN"
    ) == (
        "FROZEN",
        "Status: FROZEN / AUDIT-READY / NOT RUN",
    )
    for contradictory in (
        "Status: FROZEN / NOT FROZEN / NOT RUN",
        "Status: FROZEN / DRAFT / NOT RUN",
        "Status: UNFROZEN / AUDIT-READY / NOT RUN",
    ):
        with pytest.raises(ValueError, match="unambiguous canonical"):
            S._parse_prereg_status(contradictory)


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


def test_parser_number_addition_is_semantically_material():
    cfg = _cfg(S.FROZEN_CELL_KEYS[0])
    prefix = list(range(64))
    records = [
        _record(
            cfg,
            64,
            "prompt",
            "i1",
            correct=0,
            hit=True,
            answer=None,
            token_ids=prefix,
            explicit_answer=False,
        ),
        _record(
            cfg,
            128,
            "prompt",
            "i1",
            correct=0,
            hit=False,
            answer=7.0,
            token_ids=prefix + [999, 2],
            explicit_answer=False,
        ),
    ]
    row = S._continuation_materiality(
        records,
        long_cap=128,
        bootstrap_b=50,
        seed=S.DEFAULT_SEED,
    )["prompt"]
    assert row["n_continuation_added_frozen_parser_number"] == 1
    assert row["n_continuation_changed_frozen_parser_number"] == 1
    assert row["n_operational_semantic_truncation_evidence"] == 1
    assert row["operational_semantic_truncation_evidence_present"] is True


def test_stop_accuracy_uses_item_means_not_pooled_samples():
    cfg = _cfg(S.FROZEN_CELL_KEYS[0])
    records = [
        _record(
            cfg,
            64,
            "prompt",
            "item-a",
            correct=1,
            hit=True,
            answer=1.0,
            token_ids=list(range(64)),
        )
    ]
    records.extend(
        _record(
            cfg,
            64,
            "prompt",
            "item-b",
            correct=0,
            hit=True,
            answer=0.0,
            token_ids=list(range(64)),
        )
        for _ in range(5)
    )
    records.extend(
        [
            _record(
                cfg,
                64,
                "prompt",
                "item-a",
                correct=0,
                hit=False,
                answer=0.0,
                token_ids=[10, 2],
            ),
            _record(
                cfg,
                64,
                "prompt",
                "item-b",
                correct=1,
                hit=False,
                answer=1.0,
                token_ids=[10, 2],
            ),
        ]
    )
    summary = S._condition_summary(
        records,
        64,
        bootstrap_b=100,
        seed=S.DEFAULT_SEED,
    )
    assert math.isclose(
        np.mean(
            [
                record["correct"]
                for record in records
                if record["hit_max_new_tokens"]
            ]
        ),
        1 / 6,
    )
    stop = summary["accuracy_by_cap_stop"]
    assert stop["hit_cap"]["defined"] is True
    assert math.isclose(stop["hit_cap"]["point"], 0.5)
    assert stop["hit_cap"]["n_items"] == 2
    assert stop["hit_cap"]["n_samples"] == 6
    assert stop["hit_cap"]["ci_lo"] is not None
    assert stop["hit_cap"]["ci_hi"] is not None
    assert stop["did_not_hit_cap"]["defined"] is True
    assert stop["hit_minus_did_not_hit"]["defined"] is True
    assert math.isclose(stop["hit_minus_did_not_hit"]["point"], 0.0)
    assert stop["hit_minus_did_not_hit"]["ci_level"] == 0.95

    only_hits = S._condition_summary(
        records[:6],
        64,
        bootstrap_b=100,
        seed=S.DEFAULT_SEED,
    )["accuracy_by_cap_stop"]
    assert only_hits["did_not_hit_cap"]["defined"] is False
    assert only_hits["did_not_hit_cap"]["zero_denominator"] is True
    assert only_hits["hit_minus_did_not_hit"]["defined"] is False


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


def test_locked_seal_rejects_preexisting_analysis_instead_of_blessing_it():
    root = _scratch_dir("locked-analysis")
    seal = root / "test_once_analysis.json"
    analysis_path = root / "analysis.json"
    summary_path = root / "analysis.md"
    manifest_path = root / "run_manifest.json"
    raw_inputs = {"sample_files": [{"path": "samples/a.jsonl", "sha256": "abc"}]}
    analysis_spec = {"bootstrap_b": 10000, "seed": S.DEFAULT_SEED}
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
        S._write_json(
            analysis_path,
            {
                "experiment_id": S.EXPERIMENT_ID,
                "tampered_before_seal_transition": True,
            },
        )
        with pytest.raises(ValueError, match="cannot adopt"):
            S._prepare_test_once_analysis(
                seal_path=seal,
                raw_inputs=raw_inputs,
                analysis_spec=analysis_spec,
                analysis_path=analysis_path,
                summary_path=summary_path,
                manifest_path=manifest_path,
            )
        locked = json.loads(seal.read_text(encoding="utf-8"))
        assert locked["status"] == "LOCKED"
        assert "analysis_json_sha256" not in locked
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


def _authorization(out_dir, authorization_id="AUTH-1"):
    return {
        "owner_authorization": {
            "authorization_id": authorization_id,
            "max_gpu_hours": 3.0,
            "approved_gpu_uuid": "GPU-1234",
        },
        "designated_host": {
            "hostname": "host",
            "canonical_out_dir": str(out_dir),
        },
    }


def test_global_attempt_registry_rejects_disjoint_authorization_bypass(monkeypatch):
    root = _scratch_dir("attempt-registry")
    monkeypatch.setattr(S, "_REPO", root / "repo-sentinel")
    monkeypatch.setattr(S, "HOST_CONTROL_ROOT", root / "host-control")
    frozen_root = root / "frozen-root"
    out_one = root / "out-one"
    out_two = root / "out-two"
    source_commit = "a" * 40
    registry_path = S._canonical_attempt_registry_path(source_commit)
    first = S.CanonicalAttemptRegistry(
        authorization=_authorization(out_one),
        authorization_sha256="auth-sha",
        source_commit=source_commit,
        out_dir=out_one,
        frozen_root=frozen_root,
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
        authorization=_authorization(out_one),
        authorization_sha256="auth-sha",
        source_commit=source_commit,
        out_dir=out_one,
        frozen_root=frozen_root,
    )
    try:
        resumed.acquire()
        resumed.start()
        resumed.mark_complete({"seal": "abc"})
        assert json.loads(registry_path.read_text(encoding="utf-8"))["status"] == "COMPLETE"
    finally:
        resumed.release()

    second = S.CanonicalAttemptRegistry(
        authorization=_authorization(out_two, authorization_id="AUTH-2"),
        authorization_sha256="other-auth-sha",
        source_commit=source_commit,
        out_dir=out_two,
        frozen_root=frozen_root,
    )
    try:
        second.acquire()
        with pytest.raises(RuntimeError, match="cross-out-dir"):
            second.start()
    finally:
        second.release()
        shutil.rmtree(root, ignore_errors=True)


def _full_authorization(out_dir, *, auditor_id="audit-session-1"):
    now = datetime.now(timezone.utc)
    return {
        "schema_version": S.AUTHORIZATION_SCHEMA_VERSION,
        "experiment_id": S.EXPERIMENT_ID,
        "status": "AUTHORIZED_FOR_ONE_CANONICAL_ATTEMPT",
        "issued_at": (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "protocol_freeze": {
            "prereg_path": S._rel(S.PREREG_PATH),
            "prereg_sha256": "prereg-sha",
            "status": "FROZEN",
        },
        "independent_audit": {
            "audit_record_id": "AUDIT-1",
            "auditor_id": auditor_id,
            "auditor_role": "independent_hostile_auditor",
            "verdict": "FREEZE_RECOMMENDED",
            "audited_run_commit": "a" * 40,
        },
        "owner_authorization": {
            "authorization_id": "AUTH-1",
            "authorized_by": S.OWNER_IDENTITY,
            "authorized_at": now.isoformat().replace("+00:00", "Z"),
            "audited_run_commit": "a" * 40,
            "max_gpu_hours": 3.0,
            "approved_gpu_uuid": "GPU-1234",
            "approved_gpu_name": "NVIDIA A800 80GB PCIe",
        },
        "designated_host": {
            "hostname": S.socket.gethostname(),
            "canonical_out_dir": str(out_dir),
        },
        "model_pins": S.MODEL_SPECS,
        "frozen_artifacts": S._pinned_frozen_artifact_identity(),
        "dataset_pin": {
            "repo_id": "openai/gsm8k",
            "config": "main",
            "split": "test",
            "revision": S.GSM8K_REVISION,
            "item_identity_sha256": S._sha256_file(S.ITEM_IDENTITY_PATH),
        },
    }


def test_frozen_root_rejects_external_substitute():
    root = _scratch_dir("external-frozen-root")
    try:
        resolved, identity = S._verify_pinned_frozen_root(S.DEFAULT_FROZEN_ROOT)
        assert resolved == S.DEFAULT_FROZEN_ROOT.resolve()
        assert identity == S._pinned_frozen_artifact_identity()
        with pytest.raises(SystemExit, match="pinned.*results/arm_full"):
            S._verify_pinned_frozen_root(root / "substitute-arm")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_authorization_rejects_blank_auditor_and_registry_redirection(monkeypatch):
    root = _scratch_dir("authorization-adversarial")
    monkeypatch.setattr(S, "_REPO", root / "repo-sentinel")
    monkeypatch.setattr(S, "HOST_CONTROL_ROOT", root / "host-control")
    frozen_root = root / "frozen-root"
    out_dir = root / "run-output"
    registry_path = S._canonical_attempt_registry_path("a" * 40)
    auth_path = root / "authorization.json"
    preregistration = {"sha256": "prereg-sha", "frozen": True}
    try:
        blank = _full_authorization(out_dir, auditor_id=" ")
        S._write_json(auth_path, blank)
        with pytest.raises(SystemExit, match="auditor_id"):
            S._load_run_authorization(
                auth_path,
                source_commit="a" * 40,
                preregistration=preregistration,
                out_dir=out_dir,
                registry_path=registry_path,
                frozen_root=frozen_root,
            )

        blank_record = _full_authorization(out_dir)
        blank_record["independent_audit"]["audit_record_id"] = ""
        S._write_json(auth_path, blank_record)
        with pytest.raises(SystemExit, match="audit_record_id"):
            S._load_run_authorization(
                auth_path,
                source_commit="a" * 40,
                preregistration=preregistration,
                out_dir=out_dir,
                registry_path=registry_path,
                frozen_root=frozen_root,
            )

        redirected = _full_authorization(out_dir)
        redirected["designated_host"]["attempt_registry_path"] = str(
            root / "attacker-registry.json"
        )
        S._write_json(auth_path, redirected)
        with pytest.raises(SystemExit, match="designated-host schema"):
            S._load_run_authorization(
                auth_path,
                source_commit="a" * 40,
                preregistration=preregistration,
                out_dir=out_dir,
                registry_path=registry_path,
                frozen_root=frozen_root,
            )

        wrong_frozen_pin = _full_authorization(out_dir)
        wrong_frozen_pin["frozen_artifacts"]["files"][
            "arm_matrix_summary.json"
        ] = "0" * 64
        S._write_json(auth_path, wrong_frozen_pin)
        with pytest.raises(SystemExit, match="frozen-artifact pins"):
            S._load_run_authorization(
                auth_path,
                source_commit="a" * 40,
                preregistration=preregistration,
                out_dir=out_dir,
                registry_path=registry_path,
                frozen_root=frozen_root,
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize(
    "redirected",
    [
        lambda root: root / "repo-sentinel" / "run",
        lambda root: root / "results" / "run",
        lambda root: root / "frozen-root" / "run",
    ],
)
def test_control_paths_reject_repo_results_and_frozen_redirection(
    monkeypatch,
    redirected,
):
    root = _scratch_dir("path-redirection")
    monkeypatch.setattr(S, "_REPO", root / "repo-sentinel")
    monkeypatch.setattr(S, "HOST_CONTROL_ROOT", root / "host-control")
    try:
        with pytest.raises(SystemExit):
            S._validate_control_paths(
                out_dir=redirected(root),
                registry_path=S._canonical_attempt_registry_path("a" * 40),
                frozen_root=root / "frozen-root",
            )
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_fixed_registry_root_rejects_repo_redirection(monkeypatch):
    root = _scratch_dir("registry-root-redirection")
    monkeypatch.setattr(S, "_REPO", root / "repo-sentinel")
    monkeypatch.setattr(
        S,
        "HOST_CONTROL_ROOT",
        root / "repo-sentinel" / "redirected-control",
    )
    try:
        with pytest.raises(SystemExit, match="attempt registry.*outside"):
            S._validate_control_paths(
                out_dir=root / "safe-output",
                registry_path=S._canonical_attempt_registry_path("a" * 40),
                frozen_root=root / "frozen-root",
            )
    finally:
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
