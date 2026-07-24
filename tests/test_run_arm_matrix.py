import json

from scripts import run_arm_matrix as M


def _frozen_cells_with_axes(axes_passed_by_key):
    return [{"cell_key": key, "axes_passed": int(axes_passed_by_key.get(key, 0))}
            for key in sorted(M.FROZEN_CELL_KEYS)]


def test_arm_summary_scope_narrowed_when_any_cell_passes():
    cells = _frozen_cells_with_axes({"iti__llama3-8b": 1})
    out = M.summarize_arm_verdict(cells)
    assert out["arm_verdict"] == M.ARM_SCOPE_NARROWED_POSITIVE


def test_arm_summary_generalized_when_all_cells_zero_pass():
    cells = _frozen_cells_with_axes({})
    out = M.summarize_arm_verdict(cells)
    assert out["arm_verdict"] == M.ARM_NON_TRANSFER_GENERALIZED


def test_arm_summary_requires_exact_frozen_4_cells():
    cells = _frozen_cells_with_axes({})
    bad_count = cells[:3]
    try:
        M.summarize_arm_verdict(bad_count)
        raise AssertionError("expected ValueError for non-4-cell summary")
    except ValueError:
        pass

    bad_keys = [dict(c) for c in cells]
    bad_keys[0]["cell_key"] = "caa__unknown-model"
    try:
        M.summarize_arm_verdict(bad_keys)
        raise AssertionError("expected ValueError for bad cell key set")
    except ValueError:
        pass


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
    args = M.build_parser().parse_args([
        "--backend", "hf",
        "--use-fixture",
        "--qwen-model", "qwen-x",
        "--llama-model", "llama-y",
        "--out-dir", str(out_dir),
    ])
    for cell in cells:
        cell_dir = out_dir / f"cell_{cell.key}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        fp = M._cell_fingerprint(args, cell, cell_dir)
        payload = {
            "verdict": "KILL_PLAN_D",
            "backend": "hf",
            "steering_method": cell.method,
            "model": cell.model_id,
            "config_fingerprint": fp,
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
    rc = M.main([
        "--backend", "hf",
        "--use-fixture",
        "--qwen-model", "qwen-x",
        "--llama-model", "llama-y",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    assert called["n"] == 0


def test_matrix_model_change_invalidates_resume_and_reruns(tmp_path, monkeypatch):
    out_dir = tmp_path / "resume_model_change"
    base_args = M.build_parser().parse_args([
        "--backend", "hf",
        "--use-fixture",
        "--qwen-model", "qwen-a",
        "--llama-model", "llama-y",
        "--out-dir", str(out_dir),
    ])
    for cell in M.matrix_cells("qwen-a", "llama-y"):
        cell_dir = out_dir / f"cell_{cell.key}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "verdict": "KILL_PLAN_D",
            "backend": "hf",
            "steering_method": cell.method,
            "model": cell.model_id,
            "config_fingerprint": M._cell_fingerprint(base_args, cell, cell_dir),
            "axis_passes": {axis: False for axis in M.single.ADJ_AXES},
            "axes": [],
        }
        (cell_dir / "c2b_adjudication_results.json").write_text(json.dumps(payload), encoding="utf-8")

    calls = {"n": 0}

    def fake_single_main(argv):
        calls["n"] += 1
        parsed = M.single.build_parser().parse_args(argv)
        result_path = M.Path(parsed.out_dir) / "c2b_adjudication_results.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        specs = M.single.build_specs_synthetic(
            list(parsed.axes),
            bool(parsed.use_fixture) or parsed.backend == "synthetic",
            parsed.n_items,
            parsed.n_strong,
        )
        fp_model = str(parsed.model or M.single.DEFAULT_MODEL)
        payload = {
            "verdict": "KILL_PLAN_D",
            "backend": parsed.backend,
            "steering_method": parsed.steering_method,
            "model": fp_model,
            "config_fingerprint": M.single._config_fingerprint(parsed, fp_model, specs),
            "axis_passes": {axis: False for axis in M.single.ADJ_AXES},
            "axes": [],
        }
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return 0

    monkeypatch.setattr(M.single, "main", fake_single_main)
    rc = M.main([
        "--backend", "hf",
        "--use-fixture",
        "--qwen-model", "qwen-b",
        "--llama-model", "llama-y",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    assert calls["n"] == 2  # two qwen cells rerun; llama cells still reused


def test_matrix_spoofed_result_is_not_accepted_as_completed(tmp_path, monkeypatch):
    out_dir = tmp_path / "spoofed"
    for cell in M.matrix_cells("qwen-x", "llama-y"):
        cell_dir = out_dir / f"cell_{cell.key}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "verdict": "KILL_PLAN_D",
            "backend": "hf",
            "steering_method": cell.method,
            "model": "tampered-model",
            "config_fingerprint": "forged",
            "axis_passes": {axis: False for axis in M.single.ADJ_AXES},
            "axes": [],
        }
        (cell_dir / "c2b_adjudication_results.json").write_text(json.dumps(payload), encoding="utf-8")

    def fail_rerun(argv):
        return 9

    monkeypatch.setattr(M.single, "main", fail_rerun)
    rc = M.main([
        "--backend", "hf",
        "--use-fixture",
        "--qwen-model", "qwen-x",
        "--llama-model", "llama-y",
        "--out-dir", str(out_dir),
    ])
    assert rc == 9
