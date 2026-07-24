import json

from scripts import run_arm_matrix as M


def test_arm_summary_scope_narrowed_when_any_cell_passes():
    cells = [
        {"cell_key": "c1", "axes_passed": 0},
        {"cell_key": "c2", "axes_passed": 0},
        {"cell_key": "c3", "axes_passed": 0},
        {"cell_key": "c4", "axes_passed": 1},
    ]
    out = M.summarize_arm_verdict(cells)
    assert out["arm_verdict"] == M.ARM_SCOPE_NARROWED_POSITIVE


def test_arm_summary_generalized_when_all_cells_zero_pass():
    cells = [{"cell_key": f"c{i}", "axes_passed": 0} for i in range(4)]
    out = M.summarize_arm_verdict(cells)
    assert out["arm_verdict"] == M.ARM_NON_TRANSFER_GENERALIZED


def test_matrix_dry_run_prints_plan_without_running(tmp_path):
    out_dir = tmp_path / "dry"
    rc = M.main(["--backend", "synthetic", "--dry-run", "--out-dir", str(out_dir)])
    assert rc == 0
    assert not list(out_dir.glob("**/c2b_adjudication_results.json"))


def test_matrix_end_to_end_synthetic_emits_4_cells_and_summary(tmp_path):
    out_dir = tmp_path / "matrix"
    rc = M.main([
        "--backend", "synthetic",
        "--n-items", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
        "--save-transcripts",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    result_files = sorted(out_dir.glob("cell_*/c2b_adjudication_results.json"))
    assert len(result_files) == 4
    for rf in result_files:
        assert (rf.parent / "transcripts").exists()
    summary = json.loads((out_dir / "arm_matrix_summary.json").read_text(encoding="utf-8"))
    assert len(summary["cells"]) == 4
    assert summary["arm_verdict"] in {
        M.ARM_SCOPE_NARROWED_POSITIVE,
        M.ARM_NON_TRANSFER_GENERALIZED,
        M.ARM_INCONCLUSIVE,
    }


def test_matrix_resume_skips_completed_cells(tmp_path, monkeypatch):
    out_dir = tmp_path / "resume"
    cells = M.matrix_cells("qwen-x", "llama-y")
    for cell in cells:
        cell_dir = out_dir / f"cell_{cell.key}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "verdict": "KILL_PLAN_D",
            "axis_passes": {axis: False for axis in M.single.ADJ_AXES},
            "axes": [],
        }
        (cell_dir / "c2b_adjudication_results.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        (cell_dir / "transcripts").mkdir(parents=True, exist_ok=True)

    called = {"n": 0}

    def fail_if_called(argv):
        called["n"] += 1
        raise AssertionError("single.main should not be called for completed cells")

    monkeypatch.setattr(M.single, "main", fail_if_called)
    rc = M.main(["--backend", "synthetic", "--out-dir", str(out_dir)])
    assert rc == 0
    assert called["n"] == 0
