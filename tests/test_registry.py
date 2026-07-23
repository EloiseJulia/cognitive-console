"""Unit tests for the experiment-registry writer (identity + atomicity + locking)."""

import re
import threading
from pathlib import Path

import pytest
import yaml

from cognitive_console.registry import (
    ExperimentRecord,
    ExperimentRegistry,
    ExperimentExistsError,
    REGISTRY_FIELDS,
)


def _record(exp_id="exp-0001", **kw):
    base = dict(
        experiment_id=exp_id,
        hypothesis_id="H1",
        claim_ids=["C1"],
        type="exploratory",
        status="planned",
        seed=42,
        model="llama-3-8b-instruct",
        dataset="gsm8k",
    )
    base.update(kw)
    return ExperimentRecord(**base)


def test_record_has_all_schema_fields():
    row = _record().to_ordered_dict()
    assert list(row.keys()) == REGISTRY_FIELDS


def test_append_and_roundtrip(tmp_path):
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    written = reg.append(_record(seed=7, claim_ids=["C1", "C2b"]))
    got = reg.get("exp-0001")
    assert got == written
    assert got["seed"] == 7
    assert got["claim_ids"] == ["C1", "C2b"]
    assert got["hypothesis_id"] == "H1"
    # Persisted on disk as a valid registry with an 'experiments' list.
    with open(path, encoding="utf-8") as fh:
        on_disk = yaml.safe_load(fh)
    assert isinstance(on_disk["experiments"], list)
    assert on_disk["experiments"][0]["experiment_id"] == "exp-0001"


def test_refuses_silent_overwrite(tmp_path):
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    reg.append(_record("exp-0001", seed=1))
    with pytest.raises(ExperimentExistsError):
        reg.append(_record("exp-0001", seed=999))  # same id, different config
    # Atomicity: the failed append did NOT mutate the stored row.
    rows = reg.load()
    assert len(rows) == 1
    assert rows[0]["seed"] == 1


def test_distinct_ids_coexist(tmp_path):
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    reg.append(_record("exp-0001"))
    reg.append(_record("exp-0002"))
    assert reg.ids() == ["exp-0001", "exp-0002"]


def test_load_missing_file_is_empty(tmp_path):
    reg = ExperimentRegistry(str(tmp_path / "does-not-exist.yaml"))
    assert reg.load() == []
    assert reg.get("anything") is None


def test_update_status_known(tmp_path):
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    reg.append(_record("exp-0001", status="running"))
    updated = reg.update_status("exp-0001", "done", exit_code=0, summary_metrics={"acc": 0.9})
    assert updated["status"] == "done"
    assert updated["exit_code"] == 0
    assert updated["summary_metrics"] == {"acc": 0.9}
    assert reg.get("exp-0001")["status"] == "done"


def test_update_status_unknown_id_raises(tmp_path):
    reg = ExperimentRegistry(str(tmp_path / "registry.yaml"))
    with pytest.raises(KeyError):
        reg.update_status("nope", "done")


def test_update_rejects_unknown_field(tmp_path):
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    reg.append(_record("exp-0001"))
    with pytest.raises(ValueError):
        reg.update_status("exp-0001", "done", not_a_field=1)


def test_empty_experiment_id_rejected():
    with pytest.raises(ValueError):
        ExperimentRecord(experiment_id="")


def test_invalid_type_rejected():
    with pytest.raises(ValueError):
        _record(type="magical")


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        _record(status="halfway")


def test_matches_ledger_schema():
    # The record schema must match docs/ledgers/experiment-registry.yaml exactly,
    # in BOTH membership and ORDER, so silent field drift is caught.
    ledger = Path(__file__).resolve().parent.parent / "docs" / "ledgers" / "experiment-registry.yaml"
    text = ledger.read_text(encoding="utf-8")
    # Parse the commented schema block: lines like "# - experiment_id: ..." or
    # "#   parent: null". Capture the leading field name on each such line.
    fields = []
    for line in text.splitlines():
        m = re.match(r"^#\s*(?:-\s*)?([a-z_][a-z0-9_]*):", line)
        if m:
            fields.append(m.group(1))
    assert fields, "no schema fields parsed from the ledger comment block"
    # Set-equality (no missing/extra fields) AND order-equality (same sequence).
    assert set(fields) == set(REGISTRY_FIELDS), (
        f"field-set drift: only-in-ledger={set(fields) - set(REGISTRY_FIELDS)}, "
        f"only-in-code={set(REGISTRY_FIELDS) - set(fields)}"
    )
    assert fields == REGISTRY_FIELDS, (
        f"field-order drift:\n ledger={fields}\n code  ={REGISTRY_FIELDS}"
    )


def test_parallel_appends_do_not_drop_rows(tmp_path):
    # Cross-process/thread lock must serialize the load->check->write section so
    # concurrent appenders of DISTINCT ids all persist (the TOCTOU that silently
    # dropped runs). Without the lock, interleaved stale loads clobber rows.
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    n = 12
    barrier = threading.Barrier(n)
    errors = []

    def worker(i):
        try:
            barrier.wait()  # maximize contention: all fire together
            ExperimentRegistry(path).append(_record(f"exp-{i:04d}", seed=i))
        except Exception as exc:  # noqa: BLE001 - surface any failure to the assert
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"unexpected append errors: {errors}"
    ids = sorted(r["experiment_id"] for r in reg.load())
    assert ids == [f"exp-{i:04d}" for i in range(n)], f"rows were dropped: got {ids}"


def test_parallel_same_id_raises_not_silent_overwrite(tmp_path):
    # Two appenders that both load-before-write with the SAME id: exactly one
    # must persist and the other must raise ExperimentExistsError. Never a silent
    # overwrite, never a dropped/duplicated row.
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    barrier = threading.Barrier(2)
    outcomes = []

    def worker(seed):
        try:
            barrier.wait()
            ExperimentRegistry(path).append(_record("exp-dup", seed=seed))
            outcomes.append(("ok", seed))
        except ExperimentExistsError:
            outcomes.append(("exists", seed))

    threads = [threading.Thread(target=worker, args=(s,)) for s in (1, 2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    rows = reg.load()
    assert len(rows) == 1, f"expected exactly one persisted row, got {len(rows)}"
    assert sum(1 for o in outcomes if o[0] == "ok") == 1, outcomes
    assert sum(1 for o in outcomes if o[0] == "exists") == 1, outcomes
