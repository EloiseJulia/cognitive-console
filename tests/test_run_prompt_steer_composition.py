import json
from pathlib import Path

import pytest

from scripts import run_prompt_steer_composition as R


def _authorize(template_path: Path, auth_path: Path) -> None:
    payload = json.loads(template_path.read_text(encoding="utf-8"))
    payload.update(
        {
            "authorization_id": "audit-pass-test",
            "authorized_by": "hostile-auditor",
            "authorized_at": "2026-08-11T12:00:00Z",
            "hostile_audit_verdict": "PASS",
            "budget_status": "approved",
            "test_authorized": True,
        }
    )
    auth_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _paths(out_dir: Path):
    return R._run_paths(out_dir, "synthetic")


def test_parser_requires_explicit_phase():
    with pytest.raises(SystemExit):
        R.build_parser().parse_args([])


def test_test_rejects_unapproved_template(tmp_path):
    out_dir = tmp_path / "composition_locked"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    with pytest.raises(SystemExit, match="authorization invalid"):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--bootstrap-b",
                "100",
                "--out-dir",
                str(out_dir),
                "--test-authorization-file",
                str(paths.dev_sealed / "test_authorization.template.json"),
            ]
        )


def test_synthetic_dev_then_authorized_test_once(tmp_path):
    out_dir = tmp_path / "composition_e2e"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "200",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    assert selection["test_seen"] is False
    assert selection["eligible_axes"] == list(R.comp.AXES)
    assert selection["scientific_status"] == "SMOKE_ONLY"

    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    argv = [
        "--phase",
        "test",
        "--backend",
        "synthetic",
        "--bootstrap-b",
        "200",
        "--out-dir",
        str(out_dir),
        "--selection-json",
        str(paths.dev_sealed / "dev_selection.json"),
        "--test-authorization-file",
        str(auth_path),
    ]
    assert R.main(argv) == 0

    result = json.loads(
        (paths.test_sealed / "composition_test_results.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["phase"] == "TEST"
    assert result["valid_for_paper"] is False
    assert result["validation_status"] == "SMOKE_ONLY"
    assert result["overall_verdict"] == "SMOKE_ONLY"
    assert len(result["axes"]) == 3
    for axis in result["axes"]:
        assert set(axis["condition_means"]) == {
            "neutral",
            "prompt",
            "steer",
            "prompt_steer",
        }
        assert "primary_steer_at_prompt" in axis["estimands"]
        assert "interaction" in axis["estimands"]
        assert "does not establish" in axis["interaction_scope"]
        assert axis["verdict"] == "SMOKE_ONLY"

    assert not (paths.test_sealed / "composition_results.manifest.yaml").exists()
    registry = R.ExperimentRegistry(str(paths.registry)).load()
    smoke_records = [
        row for row in registry if row["experiment_id"].startswith("e0017-composition-smoke")
    ]
    assert len(smoke_records) == 1
    assert smoke_records[0]["type"] == "diagnostic"
    assert smoke_records[0]["claim_ids"] == []
    assert R.main(argv) == 0
    assert len(R.ExperimentRegistry(str(paths.registry)).load()) == len(registry)


def test_authorization_cannot_move_to_another_out_dir(tmp_path):
    out_dir = tmp_path / "composition_source"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    R.validate_test_authorization(auth_path, selection)
    fingerprint = R.test_config_fingerprint(selection, 100)
    marker = R.reserve_test_once(
        auth_path, selection, paths.backend_root, fingerprint
    )
    assert marker.exists()
    with pytest.raises(SystemExit, match="backend directory differs"):
        R.reserve_test_once(
            auth_path,
            selection,
            tmp_path / "other",
            fingerprint,
        )


def test_authorization_copy_cannot_bypass_fixed_out_dir_marker(tmp_path):
    out_dir = tmp_path / "copy"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = paths.backend_root / "test_authorization.json"
    copied_auth = paths.backend_root / "copied_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    copied_auth.write_bytes(auth_path.read_bytes())
    fingerprint = R.test_config_fingerprint(selection, 100)
    marker = R.reserve_test_once(
        auth_path, selection, paths.backend_root, fingerprint
    )
    R.update_test_marker(marker, "completed")

    with pytest.raises(SystemExit, match="already completed"):
        R.reserve_test_once(
            copied_auth, selection, paths.backend_root, fingerprint
        )


def test_checkpoint_fingerprint_is_part_of_test_once_identity(tmp_path):
    out_dir = tmp_path / "fp"
    assert R.main(
        [
            "--phase",
            "dev",
            "--backend",
            "synthetic",
            "--bootstrap-b",
            "100",
            "--out-dir",
            str(out_dir),
        ]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    R.reserve_test_once(
        auth_path,
        selection,
        paths.backend_root,
        R.test_config_fingerprint(selection, 100),
    )
    with pytest.raises(SystemExit, match="already consumed"):
        R.reserve_test_once(
            auth_path,
            selection,
            paths.backend_root,
            R.test_config_fingerprint(selection, 200),
        )


def test_synthetic_dev_resume_is_idempotent(tmp_path):
    out_dir = tmp_path / "resume"
    argv = [
        "--phase",
        "dev",
        "--backend",
        "synthetic",
        "--bootstrap-b",
        "100",
        "--out-dir",
        str(out_dir),
    ]
    assert R.main(argv) == 0
    paths = _paths(out_dir)
    first = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    raw_path = paths.dev_attempt / "checkpoints" / "raw_generations.jsonl"
    first_raw_lines = raw_path.read_text(encoding="utf-8").splitlines()

    assert R.main(argv) == 0
    second = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    second_raw_lines = raw_path.read_text(encoding="utf-8").splitlines()

    assert second["selection_hash"] == first["selection_hash"]
    assert second["direction_artifact"]["sha256"] == first["direction_artifact"]["sha256"]
    assert second_raw_lines == first_raw_lines


def test_operational_limits_are_frozen_and_not_cli_overridable():
    parser = R.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--phase", "dev", "--stall-timeout", "1"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--phase", "dev", "--disk-budget-gb", "1"])
    limits = R.frozen_operational_limits()
    assert limits["disk_budget_gb"] == 60.0
    assert limits["disk_ceiling_gb"] == 70.0
    assert limits["stall_timeout_seconds"] == 600.0
    assert limits["generation_retry_budget_per_backend_call"] == 1


def test_condition_shared_sample_rng_ignores_condition_and_alpha():
    sampler = object.__new__(R.CompositionTranscriptOutcomeSampler)
    sampler.seed = R.comp.SEED
    item = {"id": "paired-item"}
    assert sampler._call_seed("deliberation", item, 0.0, 3) == sampler._call_seed(
        "deliberation", item, 24.0, 3
    )
    assert sampler._call_seed("deliberation", item, 0.0, 3) != sampler._call_seed(
        "deliberation", item, 0.0, 4
    )


def test_physical_generation_budget_counts_retries_and_hard_caps(tmp_path):
    state = tmp_path / "budget.json"
    budget = R.PhysicalGenerationBudget(
        logical_limit=3,
        retry_budget=1,
        state_path=state,
        config_fingerprint="cfg",
    )
    budget.consume(3, retry=False)
    budget = R.PhysicalGenerationBudget(
        logical_limit=3,
        retry_budget=1,
        state_path=state,
        config_fingerprint="cfg",
    )
    budget.consume(3, retry=True)
    assert budget.to_dict()["physical_generations"] == 6
    assert budget.to_dict()["retry_backend_calls"] == 1
    with pytest.raises(RuntimeError, match="physical-generation cap exceeded"):
        budget.consume(1, retry=True)


def test_shared_parser_records_missing_fields_and_token_cap(tmp_path):
    collector = R.PersistentTranscriptCollector(
        tmp_path / "raw.jsonl",
        "cfg",
        model="m",
        method="caa",
        backend="hf",
        fresh=False,
    )
    item = {"id": "u1", "answer": "Paris", "aliases": ["Paris"]}
    diag = collector._parse_diag(
        "uncertainty_awareness",
        item,
        "Paris. Confidence: 80%",
        64,
        {
            "generated_token_count": 64,
            "finish_reason": "length",
            "contains_eos_token": False,
            "hit_max_new_tokens": True,
        },
    )
    assert diag["axis_parse_failed"] is True
    assert diag["missing_fields"] == ["answer"]
    assert diag["maybe_truncated"] is True
    not_capped = collector._parse_diag(
        "uncertainty_awareness",
        item,
        "Answer: Paris. Confidence: 80% " + ("word " * 100),
        64,
        {
            "generated_token_count": 12,
            "finish_reason": "eos_token",
            "contains_eos_token": True,
            "hit_max_new_tokens": False,
        },
    )
    assert not_capped["axis_parse_failed"] is False
    assert not_capped["maybe_truncated"] is False


def test_sealed_dev_directory_detects_tampering(tmp_path):
    out_dir = tmp_path / "sealed"
    argv = [
        "--phase",
        "dev",
        "--backend",
        "synthetic",
        "--bootstrap-b",
        "100",
        "--out-dir",
        str(out_dir),
    ]
    assert R.main(argv) == 0
    paths = _paths(out_dir)
    selection_path = paths.dev_sealed / "dev_selection.json"
    selection_path.write_text(
        selection_path.read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="sealed directory was modified"):
        R.main(argv)


def test_test_head_must_equal_dev_commit(tmp_path, monkeypatch):
    out_dir = tmp_path / "head"
    assert R.main(
        ["--phase", "dev", "--backend", "synthetic", "--out-dir", str(out_dir)]
    ) == 0
    paths = _paths(out_dir)
    selection = json.loads(
        (paths.dev_sealed / "dev_selection.json").read_text(encoding="utf-8")
    )
    changed = {
        "commit": "different-commit",
        "dirty": selection["dirty_tree_at_start"],
        "source_hashes": selection["source_hashes"],
    }
    monkeypatch.setattr(R, "_code_identity", lambda: changed)
    with pytest.raises(SystemExit, match="TEST HEAD must exactly equal"):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--out-dir",
                str(out_dir),
                "--test-authorization-file",
                str(paths.backend_root / "unused.json"),
            ]
        )


def test_finalization_failure_is_recorded_and_resumable(tmp_path, monkeypatch):
    out_dir = tmp_path / "finalize"
    assert R.main(
        ["--phase", "dev", "--backend", "synthetic", "--out-dir", str(out_dir)]
    ) == 0
    paths = _paths(out_dir)
    auth_path = paths.backend_root / "test_authorization.json"
    _authorize(paths.dev_sealed / "test_authorization.template.json", auth_path)
    original = R._publish_sealed_directory

    def fail_test_publish(staging, sealed, **kwargs):
        if sealed == paths.test_sealed:
            raise OSError("injected finalization failure")
        return original(staging, sealed, **kwargs)

    monkeypatch.setattr(R, "_publish_sealed_directory", fail_test_publish)
    rc = R.main(
        [
            "--phase",
            "test",
            "--backend",
            "synthetic",
            "--out-dir",
            str(out_dir),
            "--test-authorization-file",
            str(auth_path),
        ]
    )
    assert rc == 5
    failure = json.loads(
        (paths.test_attempt / "finalization_failure.json").read_text(
            encoding="utf-8"
        )
    )
    assert "injected finalization failure" in failure["failure_reason"]
    marker = json.loads(
        (paths.backend_root / "test" / "test_authorization.used.json").read_text(
            encoding="utf-8"
        )
    )
    assert marker["status"] == "failed"
    assert not paths.test_sealed.exists()
    monkeypatch.setattr(R, "_publish_sealed_directory", original)
    assert R.main(
        [
            "--phase",
            "test",
            "--backend",
            "synthetic",
            "--out-dir",
            str(out_dir),
            "--test-authorization-file",
            str(auth_path),
        ]
    ) == 0
    assert paths.test_sealed.exists()


def test_test_phase_forbids_fresh_checkpoint_deletion(tmp_path):
    with pytest.raises(SystemExit, match="--fresh is forbidden"):
        R.main(
            [
                "--phase",
                "test",
                "--backend",
                "synthetic",
                "--fresh",
                "--out-dir",
                str(tmp_path / "never_started"),
            ]
        )
