"""Tests for the C2b adjudication RUNNER guardrails (offline, synthetic backend).

FIX 3: an underpowered bootstrap (--bootstrap-b < frozen 10000) must HARD-FAIL
(SystemExit) unless the explicit --allow-underpowered flag is passed.
"""

import json

import numpy as np
import pytest

from scripts import run_c2b_adjudication as R


def test_parser_has_allow_underpowered_defaulting_off():
    args = R.build_parser().parse_args(["--backend", "synthetic"])
    assert args.allow_underpowered is False
    assert args.steering_method == "caa"
    assert args.enable_stronger_prompt_optimizer is False
    assert args.prompt_opt_budget is None


def test_underpowered_bootstrap_hard_fails_without_flag():
    with pytest.raises(SystemExit):
        R.main(["--backend", "synthetic", "--bootstrap-b", "100"])


def test_full_bootstrap_default_does_not_hard_fail(tmp_path):
    # B defaults to the frozen 10000, so no underpowered SystemExit; a quick
    # synthetic run on the offline fixtures must complete with exit code 0.
    rc = R.main(["--backend", "synthetic", "--out-dir", str(tmp_path)])
    assert rc == 0


def test_allow_underpowered_flag_permits_small_bootstrap(tmp_path):
    rc = R.main(["--backend", "synthetic", "--bootstrap-b", "200",
                 "--allow-underpowered", "--out-dir", str(tmp_path)])
    assert rc == 0


def test_stronger_prompt_optimizer_runs_and_records_provenance(tmp_path):
    out_dir = tmp_path / "stronger_prompt"
    rc = R.main([
        "--backend", "synthetic",
        "--n-items", "6",
        "--bootstrap-b", "200",
        "--allow-underpowered",
        "--enable-stronger-prompt-optimizer",
        "--prompt-opt-budget", "8",
        "--prompt-opt-seed-prompts", "3",
        "--prompt-opt-rounds", "2",
        "--prompt-opt-candidates-per-round", "2",
        "--prompt-opt-keep-top-k", "2",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    payload = json.loads((out_dir / "c2b_adjudication_results.json").read_text(encoding="utf-8"))
    spo = payload["stronger_prompt_optimizer"]
    assert spo["enabled"] is True
    assert spo["budget"] == 8
    assert spo["compute_parity_target_n_strong"] == 16
    for axis in R.ADJ_AXES:
        row = spo["axes"][axis]
        assert row["leakage_guard_ok"] is True
        assert set(row["dev_item_ids"]).isdisjoint(set(row["test_item_ids"]))
        assert row["evaluations_used"] <= 8


# --------------------------------------------------------------------------- #
# MAJOR-1: batch_size (and do_sample) must be in the checkpoint config
# fingerprint, else a resume with a different --batch-size silently reuses a
# cache built at a different chunk composition -> non-reproducible sampled cells.
# --------------------------------------------------------------------------- #
def _fp_for_argv(argv):
    args = R.build_parser().parse_args(argv)
    specs = R.build_specs_synthetic(list(args.axes), True, args.n_items,
                                    args.n_strong)
    return R._config_fingerprint(args, "some-model", specs)


class _PromptLengthSampler:
    def sample_batch(self, axis, items, instruction, alpha, k, direction, layer):
        score = min(1.0, len(str(instruction)) / 200.0)
        return [R.adj.SampleBatch(outcomes=[float(score)] * int(k), degeneracies=[0.0] * int(k))
                for _ in items]


def _runtime_fp_for_argv(argv):
    args = R.build_parser().parse_args(argv)
    specs = R.build_specs_synthetic(list(args.axes), True, args.n_items, args.n_strong)
    if args.enable_stronger_prompt_optimizer:
        specs, _ = R.optimize_specs_with_stronger_prompt_baseline(
            specs,
            sampler_for_axis=lambda _axis: _PromptLengthSampler(),
            k=R.adj.K_SAMPLES,
            dev_fraction=R.adj.DEV_FRACTION,
            seed=int(args.seed),
            parity_target_n_strong=int(args.n_strong),
            total_budget=R._effective_prompt_opt_budget(args),
            seed_prompts=int(args.prompt_opt_seed_prompts),
            rounds=int(args.prompt_opt_rounds),
            candidates_per_round=int(args.prompt_opt_candidates_per_round),
            keep_top_k=int(args.prompt_opt_keep_top_k),
        )
    return R._config_fingerprint(args, "some-model", specs)


def test_fingerprint_changes_with_batch_size():
    fp16 = _fp_for_argv(["--backend", "hf", "--batch-size", "16"])
    fp8 = _fp_for_argv(["--backend", "hf", "--batch-size", "8"])
    assert fp16 != fp8, "different --batch-size MUST invalidate the resume cache"


def test_fingerprint_same_for_same_batch_size():
    fp_a = _fp_for_argv(["--backend", "hf", "--batch-size", "16"])
    fp_b = _fp_for_argv(["--backend", "hf", "--batch-size", "16"])
    assert fp_a == fp_b, "identical config MUST reuse the resume cache"


def test_fingerprint_encodes_do_sample_via_backend():
    # synthetic is greedy (do_sample=False), hf samples (do_sample=True): the
    # fingerprint payload must reflect that, so the two backends never share a
    # cache even at an otherwise-identical config.
    fp_syn = _fp_for_argv(["--backend", "synthetic", "--batch-size", "16"])
    fp_hf = _fp_for_argv(["--backend", "hf", "--batch-size", "16"])
    assert fp_syn != fp_hf


def test_fingerprint_changes_with_steering_method():
    fp_caa = _fp_for_argv(["--backend", "hf", "--steering-method", "caa"])
    fp_iti = _fp_for_argv(["--backend", "hf", "--steering-method", "iti"])
    assert fp_caa != fp_iti


def test_optimizer_runtime_fingerprint_changes_with_implicit_effective_budget():
    fp16 = _runtime_fp_for_argv([
        "--backend", "synthetic",
        "--enable-stronger-prompt-optimizer",
        "--n-items", "6",
        "--n-strong", "16",
    ])
    fp8 = _runtime_fp_for_argv([
        "--backend", "synthetic",
        "--enable-stronger-prompt-optimizer",
        "--n-items", "6",
        "--n-strong", "8",
    ])
    assert fp16 != fp8, "implicit budget=n_strong MUST invalidate resume fingerprint"


@pytest.mark.parametrize(
    "flag,a,b",
    [
        ("--prompt-opt-budget", "8", "9"),
        ("--prompt-opt-rounds", "2", "3"),
        ("--prompt-opt-candidates-per-round", "2", "3"),
    ],
)
def test_optimizer_runtime_fingerprint_changes_with_optimizer_knobs(flag, a, b):
    base = [
        "--backend", "synthetic",
        "--enable-stronger-prompt-optimizer",
        "--n-items", "6",
        "--n-strong", "8",
        "--prompt-opt-seed-prompts", "3",
    ]
    fp_a = _runtime_fp_for_argv([*base, flag, a])
    fp_b = _runtime_fp_for_argv([*base, flag, b])
    assert fp_a != fp_b


def test_optimizer_resume_invalidates_when_n_strong_changes_with_implicit_budget(tmp_path):
    out_dir = tmp_path / "resume_opt_nstrong"
    argv_base = [
        "--backend", "synthetic",
        "--n-items", "6",
        "--bootstrap-b", "200",
        "--allow-underpowered",
        "--enable-stronger-prompt-optimizer",
        "--prompt-opt-seed-prompts", "3",
        "--prompt-opt-rounds", "2",
        "--prompt-opt-candidates-per-round", "2",
        "--prompt-opt-keep-top-k", "2",
        "--out-dir", str(out_dir),
    ]
    assert R.main([*argv_base, "--n-strong", "8"]) == 0
    first = json.loads((out_dir / "c2b_adjudication_results.json").read_text(encoding="utf-8"))
    fp1 = str(first["config_fingerprint"])

    assert R.main([*argv_base, "--n-strong", "4"]) == 0
    second = json.loads((out_dir / "c2b_adjudication_results.json").read_text(encoding="utf-8"))
    fp2 = str(second["config_fingerprint"])
    assert fp1 != fp2

    seen = set()
    for fp in sorted((out_dir / "checkpoints").glob("*.jsonl")):
        with open(fp, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                seen.add(str(json.loads(line).get("config")))
    assert fp1 in seen and fp2 in seen


def test_optimizer_generation_accounting_is_reported_and_totals_match(tmp_path, capsys):
    out_dir = tmp_path / "opt_accounting"
    rc = R.main([
        "--backend", "synthetic",
        "--n-items", "6",
        "--n-strong", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
        "--enable-stronger-prompt-optimizer",
        "--prompt-opt-budget", "8",
        "--prompt-opt-seed-prompts", "3",
        "--prompt-opt-rounds", "2",
        "--prompt-opt-candidates-per-round", "2",
        "--prompt-opt-keep-top-k", "2",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PLANNED optimizer generations (used):" in out
    assert "PLANNED total generations (adjudication + optimizer):" in out

    payload = json.loads((out_dir / "c2b_adjudication_results.json").read_text(encoding="utf-8"))
    accounting = payload["generation_accounting"]
    assert accounting["optimizer"]["enabled"] is True
    assert int(accounting["optimizer"]["total_used"]) > 0
    assert int(accounting["total"]["used"]) == (
        int(accounting["adjudication"]["total"]) + int(accounting["optimizer"]["total_used"])
    )
    spo = payload["stronger_prompt_optimizer"]
    assert int(spo["generation_counts"]["total_used"]) == int(accounting["optimizer"]["total_used"])


def test_optimizer_adjudication_accounting_matches_optimizer_off_with_single_prompt(tmp_path):
    out_off = tmp_path / "adj_only"
    out_on = tmp_path / "adj_plus_opt"
    common = [
        "--backend", "synthetic",
        "--n-items", "6",
        "--n-strong", "1",
        "--bootstrap-b", "200",
        "--allow-underpowered",
    ]
    assert R.main([*common, "--out-dir", str(out_off)]) == 0
    assert R.main([
        *common,
        "--enable-stronger-prompt-optimizer",
        "--prompt-opt-budget", "1",
        "--prompt-opt-seed-prompts", "1",
        "--prompt-opt-rounds", "1",
        "--prompt-opt-candidates-per-round", "1",
        "--prompt-opt-keep-top-k", "1",
        "--out-dir", str(out_on),
    ]) == 0
    payload_off = json.loads((out_off / "c2b_adjudication_results.json").read_text(encoding="utf-8"))
    payload_on = json.loads((out_on / "c2b_adjudication_results.json").read_text(encoding="utf-8"))
    assert int(payload_on["generation_accounting"]["adjudication"]["total"]) == int(
        payload_off["generation_accounting"]["adjudication"]["total"]
    )
    assert int(payload_on["generation_accounting"]["optimizer"]["total_used"]) > 0


@pytest.mark.parametrize("axis", R.ADJ_AXES)
def test_load_axis_items_defaults_to_frozen_per_axis_n(monkeypatch, axis):
    frozen_n = R.adj.N_ITEMS_BY_AXIS[axis]
    fake_items = [{"id": f"{axis}-{i}", "prompt": f"q{i}"} for i in range(frozen_n + 11)]

    class FakeTask:
        def __init__(self, items):
            self.items = items

    def fake_load_c2b_task(axis_name, use_fixture):
        assert axis_name == axis
        assert use_fixture is True
        return FakeTask(fake_items)

    monkeypatch.setattr(R.c2b_tasks, "load_c2b_task", fake_load_c2b_task)
    got = R.load_axis_items(axis, use_fixture=True, n_items=None)
    assert len(got) == frozen_n
    assert got == fake_items[:frozen_n]


def test_load_axis_items_explicit_n_items_overrides_frozen_default(monkeypatch):
    axis = "uncertainty_awareness"
    frozen_n = R.adj.N_ITEMS_BY_AXIS[axis]
    fake_items = [{"id": f"{axis}-{i}", "prompt": f"q{i}"} for i in range(frozen_n + 21)]

    class FakeTask:
        def __init__(self, items):
            self.items = items

    monkeypatch.setattr(
        R.c2b_tasks,
        "load_c2b_task",
        lambda axis_name, use_fixture: FakeTask(fake_items),
    )
    got = R.load_axis_items(axis, use_fixture=True, n_items=5)
    assert len(got) == 5
    assert got == fake_items[:5]


# --------------------------------------------------------------------------- #
# MINOR-1: inactivity watchdog for the D-0029 SILENT-hang failure mode.
# --------------------------------------------------------------------------- #
def test_parser_has_stall_timeout_default_600():
    args = R.build_parser().parse_args(["--backend", "synthetic"])
    assert args.stall_timeout == 600.0


def test_watchdog_should_abort_pure_decision():
    import time
    now = time.time()
    # stale: last activity 100s ago, timeout 10s -> abort.
    assert R.watchdog_should_abort(now - 100.0, 10.0, now=now) is True
    # fresh: last activity 1s ago, timeout 10s -> no abort.
    assert R.watchdog_should_abort(now - 1.0, 10.0, now=now) is False
    # disabled (0 or negative) -> never abort even if very stale.
    assert R.watchdog_should_abort(now - 10_000.0, 0.0, now=now) is False
    assert R.watchdog_should_abort(now - 10_000.0, -1.0, now=now) is False


def test_watchdog_thread_fires_on_stale_heartbeat():
    # A synthetic "stalled" progress object whose last_activity never advances,
    # with a tiny timeout: the watchdog daemon must call on_abort (we capture the
    # decision instead of os._exit-ing the test process).
    import threading
    import time

    class StalledProgress:
        def __init__(self):
            self.last_activity = time.time() - 100.0  # already stale

    fired = threading.Event()
    captured = {}

    def on_abort(timeout, idle):
        captured["timeout"] = timeout
        captured["idle"] = idle
        fired.set()

    wd = R.InactivityWatchdog(StalledProgress(), stall_timeout=0.05,
                              check_interval=0.02, on_abort=on_abort)
    wd.start()
    assert fired.wait(timeout=5.0), "watchdog did not fire on a stale heartbeat"
    wd.stop()
    assert captured["timeout"] == 0.05
    assert captured["idle"] >= 0.0


def test_watchdog_does_not_fire_while_heartbeat_is_fresh():
    import threading
    import time

    class LiveProgress:
        def __init__(self):
            self.last_activity = time.time()
            self._stop = False

        def beat(self):
            while not self._stop:
                self.last_activity = time.time()
                time.sleep(0.01)

    fired = threading.Event()
    prog = LiveProgress()
    beater = threading.Thread(target=prog.beat, daemon=True)
    beater.start()
    wd = R.InactivityWatchdog(prog, stall_timeout=0.2, check_interval=0.02,
                              on_abort=lambda t, i: fired.set())
    wd.start()
    time.sleep(0.5)
    prog._stop = True
    wd.stop()
    assert not fired.is_set(), "watchdog fired despite a fresh heartbeat"


def test_looks_like_cuda_error_labeling():
    assert R._looks_like_cuda_error(RuntimeError("CUDA error: device-side assert")) is True
    assert R._looks_like_cuda_error(RuntimeError("cublas runtime error")) is True
    assert R._looks_like_cuda_error(RuntimeError("CUDA out of memory")) is True
    # a generic RuntimeError with no GPU vocabulary must NOT be mislabeled.
    assert R._looks_like_cuda_error(RuntimeError("list index out of range")) is False
    assert R._looks_like_cuda_error(ValueError("bad config")) is False


def _canonical_verdict_metrics(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    axes = {}
    for axis_row in data["axes"]:
        axes[axis_row["axis"]] = {
            "layer": axis_row["layer"],
            "passed": axis_row["passed"],
            "mean_diff": axis_row["mean_diff"],
            "ci_lo": axis_row["ci_lo"],
            "ci_hi": axis_row["ci_hi"],
            "ci_level": axis_row["ci_level"],
            "coherence_ok": axis_row["coherence_ok"],
            "test_steer_degeneracy": axis_row["test_steer_degeneracy"],
            "test_baseline_degeneracy": axis_row["test_baseline_degeneracy"],
            "per_item_prompt": axis_row["per_item_prompt"],
            "per_item_steer": axis_row["per_item_steer"],
            "per_item_diff": axis_row["per_item_diff"],
            "frozen_alpha": axis_row["dev_selection"]["frozen_alpha"],
            "best_prompt_id": axis_row["dev_selection"]["best_prompt_id"],
        }
    payload = {
        "verdict": data["verdict"],
        "axis_passes": data["axis_passes"],
        "axes": axes,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def test_transcript_side_output_is_metric_invariant(tmp_path):
    out_a = tmp_path / "with_tx"
    out_b = tmp_path / "without_tx"
    argv = [
        "--backend", "synthetic",
        "--n-items", "5",
        "--bootstrap-b", "200",
        "--allow-underpowered",
        "--seed", "20260723",
    ]
    assert R.main([*argv, "--save-transcripts", "--out-dir", str(out_a)]) == 0
    assert R.main([*argv, "--no-save-transcripts", "--out-dir", str(out_b)]) == 0

    a = _canonical_verdict_metrics(out_a / "c2b_adjudication_results.json")
    b = _canonical_verdict_metrics(out_b / "c2b_adjudication_results.json")
    assert a == b

    tx_dir = out_a / "transcripts"
    assert tx_dir.exists()
    assert (tx_dir / "paired_test_channels.jsonl").exists()
    assert not (out_b / "transcripts").exists()


def test_transcript_records_include_parse_diagnostics(tmp_path):
    out_dir = tmp_path / "tx_diag"
    rc = R.main([
        "--backend", "synthetic",
        "--n-items", "4",
        "--bootstrap-b", "200",
        "--allow-underpowered",
        "--save-transcripts",
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    tx_files = sorted((out_dir / "transcripts").glob("*.jsonl"))
    assert tx_files, "expected transcript jsonl files"
    row = None
    for fp in tx_files:
        if fp.name == "paired_test_channels.jsonl":
            continue
        with open(fp, "r", encoding="utf-8") as fh:
            line = fh.readline().strip()
        if line:
            row = json.loads(line)
            break
    assert row is not None
    assert "prompt_text" in row and isinstance(row["prompt_text"], str)
    assert "generation_text" in row and isinstance(row["generation_text"], str)
    assert "parse" in row and isinstance(row["parse"], dict)
    assert "numbers_extracted" in row["parse"]
    assert "parsed_confidence" in row["parse"]
    assert "axis_parse_failed" in row["parse"]


def test_transcript_alignment_uses_non_alpha_key_for_scaled_iti_flow(tmp_path):
    out_dir = tmp_path / "iti_alignment"
    collector = R.TranscriptCollector(out_dir, "fake-model", "iti", "hf")
    item = {"id": "u1", "prompt": "p"}
    for j in range(2):
        collector.record_generation(
            axis="uncertainty_awareness",
            item=item,
            instruction="neutral",
            alpha=0.2,  # effective alpha after scaling
            layer=1,
            sample_index=j,
            sample_seed=10 + j,
            prompt_text="Q?",
            generation_text="confidence: 0.80",
            outcome=0.8,
            degeneracy=0.0,
            max_new_tokens=16,
        )
    collector.attach_cell(
        axis="uncertainty_awareness",
        phase=R.adj.PHASE_TEST_STEER,
        cell_key="alpha=0.1",
        item_id="u1",
        alpha=0.1,  # requested grid alpha before scaling
        instruction="neutral",
        outcomes=[0.8, 0.8],
    )
    assert len(collector._all_records) == 2
    assert all(abs(float(r["alpha"]) - 0.2) < 1e-12 for r in collector._all_records)
    assert all(abs(float(r["requested_alpha"]) - 0.1) < 1e-12 for r in collector._all_records)


def test_transcript_text_is_truncated_with_explicit_marker(tmp_path):
    out_dir = tmp_path / "truncate"
    collector = R.TranscriptCollector(out_dir, "fake-model", "iti", "hf")
    item = {"id": "u1", "prompt": "p"}
    collector.record_generation(
        axis="uncertainty_awareness",
        item=item,
        instruction="neutral",
        alpha=0.1,
        layer=1,
        sample_index=0,
        sample_seed=1,
        prompt_text="P" * (R._TRANSCRIPT_MAX_PROMPT_CHARS + 50),
        generation_text="G" * (R._TRANSCRIPT_MAX_GENERATION_CHARS + 50),
        outcome=0.2,
        degeneracy=0.0,
        max_new_tokens=8,
    )
    collector.attach_cell(
        axis="uncertainty_awareness",
        phase=R.adj.PHASE_TEST_STEER,
        cell_key="alpha=0.1",
        item_id="u1",
        alpha=0.1,
        instruction="neutral",
        outcomes=[0.2],
    )
    rec = collector._all_records[0]
    assert rec["prompt_truncated"] is True
    assert rec["generation_truncated"] is True
    assert rec["prompt_text"].endswith("...[truncated]")
    assert rec["generation_text"].endswith("...[truncated]")


def test_hf_postrun_disk_over_ceiling_fails_explicitly(tmp_path, monkeypatch):
    class FakeAxisRow:
        axis = "uncertainty_awareness"
        per_item_prompt = [0.0]
        per_item_steer = [0.0]

    class FakeReport:
        verdict = "KILL_PLAN_D"
        axis_passes = {"uncertainty_awareness": False}
        axis_results = [FakeAxisRow()]

    spec = R.AxisAdjSpec(
        axis="uncertainty_awareness",
        items=[{"id": "u1", "prompt": "q"}],
        strong_prompts=[("p1", "strong prompt")],
        neutral_prompt="neutral prompt",
        direction=np.ones(8),
        layer=1,
    )

    monkeypatch.setattr(
        R,
        "build_specs_hf",
        lambda *a, **k: ([spec], {"alpha_scale_by_axis": {"uncertainty_awareness": 1.0}, "steering_method": "iti"}),
    )
    monkeypatch.setattr(R, "hf_sampler_factory", lambda *a, **k: (lambda axis: object()))
    monkeypatch.setattr(R.adj, "adjudicate", lambda *a, **k: FakeReport())
    monkeypatch.setattr(
        R,
        "write_results",
        lambda report, out_dir, meta: (out_dir / "c2b_adjudication_results.json"),
    )
    monkeypatch.setattr(R, "register", lambda *a, **k: "exp-test")

    class _Usage:
        message = "ok"

    calls = {"n": 0}

    def fake_check_disk_budget(paths, budget_gb, ceiling_gb, raise_on_over=True):
        calls["n"] += 1
        if calls["n"] == 3:
            raise R.DiskBudgetError("DISK OVER CEILING")
        return _Usage()

    monkeypatch.setattr(R, "check_disk_budget", fake_check_disk_budget)
    monkeypatch.setattr(R.p0, "_pick_device", lambda: "cpu")
    monkeypatch.setattr(R.p0, "_pick_dtype", lambda: "fp32")
    rc = R.main([
        "--backend", "hf",
        "--steering-method", "iti",
        "--use-fixture",
        "--allow-underpowered",
        "--bootstrap-b", "200",
        "--n-items", "1",
        "--axes", "uncertainty_awareness",
        "--out-dir", str(tmp_path / "hf_disk_guard"),
    ])
    assert rc == 4
