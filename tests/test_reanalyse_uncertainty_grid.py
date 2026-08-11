import json
from pathlib import Path

import pytest

from cognitive_console.eval import scorers
from scripts import reanalyse_uncertainty_grid as G
from scripts import run_uncertainty_format_recheck as R
from scripts import run_uncertainty_grid_replay as P


def test_committed_manifest_reproduces_existing_cell_without_grid_claim():
    outputs, lineage = G.run_analysis(G.DEFAULT_MANIFEST, allow_incomplete=True)
    report = outputs["report"]

    assert report["grid_complete"] is False
    assert report["valid_for_paper"] is False
    assert report["missing_cells"] == [
        "caa__llama3-8b",
        "iti__llama3-8b",
        "iti__qwen2.5-7b",
    ]
    assert report["legacy_e0013_reproduction"]["matches_original_one_cell_result"]
    cell = report["cells"]["caa__qwen2.5-7b"]
    assert cell["conditions"]["prompt"]["format_compliance_exact"] == {
        "numerator": 118,
        "denominator": 265,
        "fraction": "118/265",
    }
    assert cell["sample_accounting"]["complete_case"]["both_compliant"] == 110
    assert cell["adversarial_missingness_guard"]["spans_zero"] is True
    assert (
        cell["adversarial_missingness_guard"]["all_generation_sign_claim_allowed"]
        is False
    )
    assert lineage["manual_edits_allowed"] is False


def test_incomplete_grid_fails_closed_without_explicit_inventory_mode():
    with pytest.raises(G.RecheckError, match="four-cell analysis is incomplete"):
        G.run_analysis(G.DEFAULT_MANIFEST, allow_incomplete=False)


def test_coverage_rejects_missing_rows():
    records = []
    for condition in G.EXPECTED_CONDITIONS:
        for item_id in ("i1", "i2"):
            for sample_index in range(2):
                records.append(
                    {
                        "split": "test",
                        "condition": condition,
                        "item_id": item_id,
                        "sample_index": sample_index,
                    }
                )
    records.pop()
    with pytest.raises(G.RecheckError, match="incomplete TEST grid"):
        G._validate_coverage(
            records, cell_key="caa__qwen2.5-7b", test_ids=["i1", "i2"], k=2
        )


def test_coverage_rejects_missing_duplicate_or_extra_dev_keys():
    records = []
    for split, item_ids in (("dev", ["d1"]), ("test", ["t1"])):
        for condition in G.EXPECTED_CONDITIONS:
            records.append(
                {
                    "split": split,
                    "condition": condition,
                    "item_id": item_ids[0],
                    "sample_index": 0,
                }
            )
    records.pop(0)
    with pytest.raises(G.RecheckError, match="incomplete DEV grid"):
        G._validate_coverage(
            records,
            cell_key="caa__qwen2.5-7b",
            dev_ids=["d1"],
            test_ids=["t1"],
            k=1,
        )
    complete = []
    for split, item_id in (("dev", "d1"), ("test", "t1")):
        for condition in G.EXPECTED_CONDITIONS:
            complete.append(
                {
                    "split": split,
                    "condition": condition,
                    "item_id": item_id,
                    "sample_index": 0,
                }
            )
    with pytest.raises(G.RecheckError, match="duplicate DEV"):
        G._validate_coverage(
            [*complete, complete[0]],
            cell_key="caa__qwen2.5-7b",
            dev_ids=["d1"],
            test_ids=["t1"],
            k=1,
        )
    extra = [dict(row) for row in complete]
    extra[0]["item_id"] = "extra"
    with pytest.raises(G.RecheckError, match="incomplete DEV grid"):
        G._validate_coverage(
            extra,
            cell_key="caa__qwen2.5-7b",
            dev_ids=["d1"],
            test_ids=["t1"],
            k=1,
        )


def test_transcript_directory_schema_recomputes_frozen_outcomes(tmp_path):
    item = {
        "id": "triviaqa-00001",
        "prompt": "Capital of France?",
        "answer": "Paris",
        "aliases": [],
    }
    cfg = R.FrozenCellConfig(
        cell_key="caa__qwen2.5-7b",
        method="caa",
        model_label="qwen2.5-7b",
        model_id="Qwen/Qwen2.5-7B-Instruct",
        layer=3,
        frozen_alpha=8.0,
        best_prompt_id="unc-test",
        best_prompt_text="Answer and state confidence.",
        neutral_prompt="Neutral.",
        sigma=1.0,
        source_result_file="synthetic",
        source_config_fingerprint="abc",
        source_mean_diff=0.0,
    )
    text = "Answer: Paris. Confidence: 80%."
    score = scorers.per_item_brier(1, 0.8)
    generation = {
        "seed": R.DEFAULT_SEED,
        "k_samples": 1,
    }
    phase_map = {
        "prompt": ("test_prompt", "prompt=unc-test"),
        "steer": ("test_steer", "alpha=8.0"),
        "baseline": ("test_baseline", "alpha=0"),
    }
    for condition, (phase, cell_key) in phase_map.items():
        instruction, requested_alpha, effective_alpha = R._condition_instruction_and_alpha(
            cfg, condition
        )
        prompt = R.adj.format_task_input(R.AXIS, instruction, item)
        row = {
            "axis": R.AXIS,
            "item_id": item["id"],
            "alpha": effective_alpha,
            "layer": cfg.layer,
            "sample_index": 0,
            "sample_seed": R._call_seed(
                R.DEFAULT_SEED, item, effective_alpha, 0
            ),
            "instruction": instruction,
            "prompt_text": prompt,
            "generation_text": text,
            "prompt_truncated": False,
            "generation_truncated": False,
            "sample_outcome": score,
            "sample_degeneracy": 0.0,
            "parse": {
                "parsed_confidence": 0.8,
                "correctness": 1,
                "axis_parse_failed": False,
            },
            "meta": {
                "method": "caa",
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "backend": "hf",
            },
            "phase": phase,
            "cell_key": cell_key,
            "requested_alpha": requested_alpha,
        }
        path = tmp_path / f"{R.AXIS}__{phase}__{cell_key}.jsonl"
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    frozen_payload = {
        "axes": [
            {
                "axis": R.AXIS,
                "per_item_prompt": [score],
                "per_item_steer": [score],
            }
        ]
    }

    records, meta = G._load_c2b_transcript_dir(
        tmp_path,
        cell_key=cfg.cell_key,
        cfg=cfg,
        frozen_payload=frozen_payload,
        items_by_id={item["id"]: item},
        test_ids=[item["id"]],
        generation=generation,
    )

    assert len(records) == 3
    assert meta["schema"] == "c2b_transcript_dir_v1"
    assert meta["frozen_per_item_outcomes_reproduced"] is True


def test_valid_gitignored_recovered_source_skips_replay(tmp_path):
    cfg, item, frozen_payload, transcript_dir = _write_recovered_source(tmp_path)
    protocol = {
        "generation": {"seed": R.DEFAULT_SEED, "k_samples": 1},
        "cells": {
            cfg.cell_key: {
                "sources": [
                    {
                        "kind": "c2b_transcript_dir_v1",
                        "path": str(transcript_dir),
                        "origin": "restored_immutable_e0006_if_recovered",
                    }
                ]
            }
        },
    }
    recovered = P._validate_recovered_source(
        protocol,
        cell_key=cfg.cell_key,
        cfg=cfg,
        frozen_payload=frozen_payload,
        items_by_id={item["id"]: item},
        test_ids=[item["id"]],
    )
    assert recovered["gitignored_presence_was_validated"] is True
    assert (
        P._choose_replay_action(recovered, None)
        == "USE_VALID_RECOVERED_SOURCE_SKIP_REPLAY"
    )


def test_present_invalid_recovered_source_hard_fails(tmp_path):
    cfg, item, frozen_payload, transcript_dir = _write_recovered_source(tmp_path)
    prompt_file = next(transcript_dir.glob("*test_prompt*.jsonl"))
    row = json.loads(prompt_file.read_text(encoding="utf-8"))
    row["layer"] = 999
    prompt_file.write_text(json.dumps(row) + "\n", encoding="utf-8")
    protocol = {
        "generation": {"seed": R.DEFAULT_SEED, "k_samples": 1},
        "cells": {
            cfg.cell_key: {
                "sources": [
                    {
                        "kind": "c2b_transcript_dir_v1",
                        "path": str(transcript_dir),
                        "origin": "restored_immutable_e0006_if_recovered",
                    }
                ]
            }
        },
    }
    with pytest.raises(G.RecheckError, match="layer"):
        P._validate_recovered_source(
            protocol,
            cell_key=cfg.cell_key,
            cfg=cfg,
            frozen_payload=frozen_payload,
            items_by_id={item["id"]: item},
            test_ids=[item["id"]],
        )


def test_replay_default_plan_excludes_immutable_existing_cell():
    protocol = G.load_protocol(G.DEFAULT_MANIFEST)
    assert P._planned_cells(protocol, None) == [
        "caa__llama3-8b",
        "iti__llama3-8b",
        "iti__qwen2.5-7b",
    ]
    with pytest.raises(G.RecheckError, match="replay is forbidden"):
        P._planned_cells(protocol, ["caa__qwen2.5-7b"])
    argv = P._build_cell_argv(
        protocol_path=G.DEFAULT_MANIFEST,
        protocol=protocol,
        cell_key="iti__qwen2.5-7b",
        out_dir=Path("out"),
        qwen_model="Qwen/Qwen2.5-7B-Instruct",
        llama_model="meta-llama/Meta-Llama-3-8B-Instruct",
        qwen_revision="a09a35458c702b33eeacc393d103063234e8bc28",
        llama_revision="8afb486c1db24fe5011ec46dfbe5b5dccdb575c2",
        qwen_model_content_sha256=None,
        llama_model_content_sha256=None,
        expected_code_commit="a" * 40,
        authorization=protocol["execution"]["authorization_id"],
        scratch_dir=Path("scratch"),
        hf_cache_dir=Path("hf-cache"),
    )
    assert argv[argv.index("--experiment-id") + 1] == (
        "E-0013-grid-recheck-iti-qwen2p5-7b"
    )
    assert "--resume-incomplete" in argv
    assert argv[argv.index("--splits") + 1:argv.index("--seed")] == ["dev", "test"]


def test_cell_argv_binds_direct_hf_guard_identity(tmp_path):
    protocol = {
        "generation": {
            "item_artifact": {"path": str(tmp_path / "items.jsonl")},
            "frozen_root": str(tmp_path / "frozen"),
            "seed": R.DEFAULT_SEED,
            "n_extraction": R.DEFAULT_N_EXTRACTION,
            "max_new_tokens": R.DEFAULT_MAX_NEW_TOKENS,
            "temperature": R.DEFAULT_TEMPERATURE,
            "batch_size": 16,
            "raw_text_max_chars": 8000,
        },
        "analysis": {"bootstrap_b": 10000},
    }
    argv = P._build_cell_argv(
        protocol_path=tmp_path / "protocol.json",
        protocol=protocol,
        cell_key="caa__qwen2.5-7b",
        out_dir=tmp_path / "out",
        qwen_model="Qwen/Qwen2.5-7B-Instruct",
        llama_model="meta-llama/Meta-Llama-3-8B-Instruct",
        qwen_revision="a" * 40,
        llama_revision="b" * 40,
        qwen_model_content_sha256=None,
        llama_model_content_sha256=None,
        expected_code_commit="c" * 40,
        authorization="approved",
        scratch_dir=tmp_path / "external-scratch",
        hf_cache_dir=tmp_path / "external-hf",
    )
    assert argv[argv.index("--expected-code-commit") + 1] == "c" * 40
    assert argv[argv.index("--authorization") + 1] == "approved"
    assert argv[argv.index("--qwen-revision") + 1] == "a" * 40
    assert "--scratch-dir" in argv
    assert "--hf-cache-dir" in argv


def test_protocol_binds_all_four_cells_and_exact_replay_job_counts():
    protocol = G.load_protocol(G.DEFAULT_MANIFEST)
    _, split, _ = G.load_frozen_items(protocol)
    frozen_root = G._resolve(protocol["generation"]["frozen_root"])
    plans = {}
    for cell_key in sorted(protocol["cells"]):
        cfg, _, _ = G.validate_cell_manifest(
            cell_key, protocol["cells"][cell_key], frozen_root
        )
        plans[cell_key] = P._cell_plan(
            protocol, cell_key=cell_key, cfg=cfg, split=split
        )

    assert set(plans) == {
        "caa__llama3-8b",
        "caa__qwen2.5-7b",
        "iti__llama3-8b",
        "iti__qwen2.5-7b",
    }
    assert {row["total_generations"] for row in plans.values()} == {1200}
    assert {row["total_batches"] for row in plans.values()} == {78}
    assert {row["splits"]["test"]["generations"] for row in plans.values()} == {795}
    assert {row["splits"]["dev"]["generations"] for row in plans.values()} == {405}
    assert all(row["test_use_policy"] == R.TEST_USE_POLICY for row in plans.values())
    assert plans["iti__qwen2.5-7b"]["requested_alpha"] == 12.0
    assert plans["iti__qwen2.5-7b"]["effective_steer_alpha"] == pytest.approx(
        12.0 * 4.546516468477585
    )


def test_frozen_replay_source_requires_hashed_completion(tmp_path):
    root = tmp_path / "cell"
    root.mkdir()
    samples = root / "samples.jsonl"
    samples.write_text("{}\n", encoding="utf-8")
    spec = {
        "sources": [{
            "kind": "e0013_samples_v1",
            "path": str(samples),
            "origin": "frozen_replay",
        }]
    }
    selected, inventory = G._select_source(spec)
    assert selected is None
    assert inventory[0]["raw_exists"] is True
    assert inventory[0]["completion_exists"] is False

    run_manifest = root / "run_manifest.json"
    execution_binding = {
        "dirty_tree": False,
        "code_commit": "a" * 40,
        "authorization": {"id": "approved"},
        "argv": ["python", "runner.py", "--same"],
    }
    execution_sha = R._canonical_hash(execution_binding)
    run_manifest.write_text(
        json.dumps({
            "evidence_scope": {
                "frozen_results_replaced": False,
                "new_scorer_result_created": False,
            },
            "execution_identity_sha256": execution_sha,
            "code_commit": "a" * 40,
            "dirty_tree_at_start": False,
            "execution_binding": execution_binding,
            "cells": {
                "caa__qwen2.5-7b": {
                    "resolved_model_identity": {
                        "kind": "test",
                        "model_label": "qwen2.5-7b",
                        "resolved_path": "model",
                        "content_sha256": "model",
                    },
                    "checkpoint": {
                        "model_identity_sha256": R._canonical_hash({
                            "kind": "test",
                            "model_label": "qwen2.5-7b",
                            "resolved_path": "model",
                            "content_sha256": "model",
                        }),
                        "execution_identity_sha256": execution_sha,
                    },
                }
            },
        }),
        encoding="utf-8",
    )
    completion = {
        "status": "COMPLETE_PENDING_INDEPENDENT_RESULTS_AUDIT",
        "authorization_id": "approved",
        "argv": ["--same"],
        "execution_identity_sha256": execution_sha,
        "samples_jsonl": {
            "path": G._rel(samples),
            "sha256": G.sha256_file(samples),
        },
        "run_manifest_json": {
            "path": G._rel(run_manifest),
            "sha256": G.sha256_file(run_manifest),
        },
    }
    (root / "completion.json").write_text(
        json.dumps(completion), encoding="utf-8"
    )
    selected, _ = G._select_source(spec)
    assert selected is not None
    assert selected["completion_identity"]["completion_sha256"] == G.sha256_file(
        root / "completion.json"
    )


def test_protected_snapshot_covers_original_and_four_frozen_cells():
    protocol = G.load_protocol(G.DEFAULT_MANIFEST)
    snapshot = P._protected_snapshot(protocol)
    assert len(snapshot) == 7
    assert "results/E-0013-uncertainty-recheck/samples.jsonl" in snapshot
    assert "results/E-0013-uncertainty-recheck/reanalysis.json" in snapshot
    assert "results/E-0013-uncertainty-recheck/run_manifest.json" in snapshot
    assert all(
        snapshot[path] == G.sha256_file(G._resolve(path)) for path in snapshot
    )


def test_gpu_execute_requires_explicit_audited_commit_before_runner(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("GPU cell runner must not be reached")

    monkeypatch.setattr(P.runner, "main", fail_if_called)
    with pytest.raises(G.RecheckError, match="expected-code-commit is mandatory"):
        P.main(["--execute"])


def test_frozen_item_snapshot_loader_avoids_network(tmp_path):
    path = tmp_path / "items.jsonl"
    rows = [
        {"id": "i1", "prompt": "Q1", "answer": "A1", "aliases": []},
        {"id": "i2", "prompt": "Q2", "answer": "A2", "aliases": ["Alias"]},
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    loaded = R.load_uncertainty_items(
        use_fixture=False, n_items=None, frozen_items_path=path
    )
    assert loaded == rows


def test_generation_runner_refuses_to_overwrite_completed_artifact(tmp_path):
    out_dir = tmp_path / "existing"
    out_dir.mkdir()
    (out_dir / "samples.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        R.main(["--backend", "synthetic", "--out-dir", str(out_dir)])


def _write_recovered_source(tmp_path):
    item = {
        "id": "triviaqa-00001",
        "prompt": "Capital of France?",
        "answer": "Paris",
        "aliases": [],
    }
    cfg = R.FrozenCellConfig(
        cell_key="caa__qwen2.5-7b",
        method="caa",
        model_label="qwen2.5-7b",
        model_id="Qwen/Qwen2.5-7B-Instruct",
        layer=3,
        frozen_alpha=8.0,
        best_prompt_id="unc-test",
        best_prompt_text="Answer and state confidence.",
        neutral_prompt="Neutral.",
        sigma=1.0,
        source_result_file="synthetic",
        source_config_fingerprint="abc",
        source_mean_diff=0.0,
    )
    transcript_dir = tmp_path / "gitignored-transcripts"
    transcript_dir.mkdir()
    text = "Answer: Paris. Confidence: 80%."
    score = scorers.per_item_brier(1, 0.8)
    for condition, phase, cell_key in (
        ("prompt", R.adj.PHASE_TEST_PROMPT, "prompt=unc-test"),
        ("steer", R.adj.PHASE_TEST_STEER, "alpha=8.0"),
        ("baseline", R.adj.PHASE_TEST_BASELINE, "alpha=0"),
    ):
        instruction, requested_alpha, effective_alpha = (
            R._condition_instruction_and_alpha(cfg, condition)
        )
        prompt = R.adj.format_task_input(R.AXIS, instruction, item)
        row = {
            "axis": R.AXIS,
            "item_id": item["id"],
            "alpha": effective_alpha,
            "layer": cfg.layer,
            "sample_index": 0,
            "sample_seed": R._call_seed(
                R.DEFAULT_SEED, item, effective_alpha, 0
            ),
            "instruction": instruction,
            "prompt_text": prompt,
            "generation_text": text,
            "prompt_truncated": False,
            "generation_truncated": False,
            "sample_outcome": score,
            "sample_degeneracy": 0.0,
            "parse": {
                "parsed_confidence": 0.8,
                "correctness": 1,
                "axis_parse_failed": False,
            },
            "meta": {
                "method": "caa",
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "backend": "hf",
            },
            "phase": phase,
            "cell_key": cell_key,
            "requested_alpha": requested_alpha,
        }
        path = transcript_dir / f"{R.AXIS}__{phase}__{cell_key}.jsonl"
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    frozen_payload = {
        "axes": [
            {
                "axis": R.AXIS,
                "per_item_prompt": [score],
                "per_item_steer": [score],
            }
        ]
    }
    return cfg, item, frozen_payload, transcript_dir
