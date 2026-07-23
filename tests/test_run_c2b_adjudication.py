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
