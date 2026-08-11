import json
import math
import os
import shutil
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


def _record(cfg, cap, condition, item_id, *, correct, hit, answer, token_ids):
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
        "final_answer_present": answer is not None,
        "parser_failed": answer is None,
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
    assert continuation["n_continuation_added_parseable_answer"] == 40
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
