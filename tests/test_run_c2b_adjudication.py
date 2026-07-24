"""Tests for the C2b adjudication RUNNER guardrails (offline, synthetic backend).

FIX 3: an underpowered bootstrap (--bootstrap-b < frozen 10000) must HARD-FAIL
(SystemExit) unless the explicit --allow-underpowered flag is passed.
"""

import pytest

from scripts import run_c2b_adjudication as R


def test_parser_has_allow_underpowered_defaulting_off():
    args = R.build_parser().parse_args(["--backend", "synthetic"])
    assert args.allow_underpowered is False


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
