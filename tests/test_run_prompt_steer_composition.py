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
                str(out_dir / "test_authorization.template.json"),
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
    selection = json.loads(
        (out_dir / "dev_selection.json").read_text(encoding="utf-8")
    )
    assert selection["test_seen"] is False
    assert selection["eligible_axes"] == list(R.comp.AXES)

    auth_path = out_dir / "test_authorization.json"
    _authorize(out_dir / "test_authorization.template.json", auth_path)
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
        str(out_dir / "dev_selection.json"),
        "--test-authorization-file",
        str(auth_path),
    ]
    assert R.main(argv) == 0

    result = json.loads(
        (out_dir / "composition_test_results.json").read_text(encoding="utf-8")
    )
    assert result["phase"] == "TEST"
    assert result["valid_for_paper"] is False
    assert result["validation_status"] == "PENDING_HOSTILE_RESULT_AUDIT"
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

    with pytest.raises(SystemExit, match="TEST already completed"):
        R.main(argv)


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
    selection = json.loads(
        (out_dir / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = out_dir / "test_authorization.json"
    _authorize(out_dir / "test_authorization.template.json", auth_path)
    R.validate_test_authorization(auth_path, selection)
    fingerprint = R.test_config_fingerprint(selection, 100)
    marker = R.reserve_test_once(auth_path, selection, out_dir, fingerprint)
    assert marker.exists()
    with pytest.raises(SystemExit, match="out-dir differs"):
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
    selection = json.loads(
        (out_dir / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = out_dir / "test_authorization.json"
    copied_auth = out_dir / "copied_authorization.json"
    _authorize(out_dir / "test_authorization.template.json", auth_path)
    copied_auth.write_bytes(auth_path.read_bytes())
    fingerprint = R.test_config_fingerprint(selection, 100)
    marker = R.reserve_test_once(auth_path, selection, out_dir, fingerprint)
    R.update_test_marker(marker, "completed")

    with pytest.raises(SystemExit, match="already completed"):
        R.reserve_test_once(copied_auth, selection, out_dir, fingerprint)


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
    selection = json.loads(
        (out_dir / "dev_selection.json").read_text(encoding="utf-8")
    )
    auth_path = out_dir / "test_authorization.json"
    _authorize(out_dir / "test_authorization.template.json", auth_path)
    R.reserve_test_once(
        auth_path,
        selection,
        out_dir,
        R.test_config_fingerprint(selection, 100),
    )
    with pytest.raises(SystemExit, match="already consumed"):
        R.reserve_test_once(
            auth_path,
            selection,
            out_dir,
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
    first = json.loads(
        (out_dir / "dev_selection.json").read_text(encoding="utf-8")
    )
    raw_path = out_dir / "dev_checkpoints" / "raw_generations.jsonl"
    first_raw_lines = raw_path.read_text(encoding="utf-8").splitlines()

    assert R.main(argv) == 0
    second = json.loads(
        (out_dir / "dev_selection.json").read_text(encoding="utf-8")
    )
    second_raw_lines = raw_path.read_text(encoding="utf-8").splitlines()

    assert second["selection_hash"] == first["selection_hash"]
    assert second["direction_artifact"]["sha256"] == first["direction_artifact"]["sha256"]
    assert second_raw_lines == first_raw_lines


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
