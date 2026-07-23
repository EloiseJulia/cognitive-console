"""Run-lineage helpers: id minting is collision-safe under parallel same-config runs."""

import threading

from cognitive_console import lineage
from cognitive_console.registry import ExperimentRegistry


def test_sequential_same_config_ids_increment(tmp_path):
    reg = ExperimentRegistry(str(tmp_path / "registry.yaml"))
    ids = [
        lineage.register_run(
            registry=reg,
            prefix="conflict",
            hypothesis_id="H2",
            claim_ids=["C2b"],
            config_hash="sha256:aa",
            summary_metrics={"landing_fraction": 0.5},
            seed=i,
        )
        for i in range(3)
    ]
    assert len(set(ids)) == 3                 # all distinct
    assert reg.ids() == ids                   # all persisted in mint order


def test_parallel_same_config_runs_auto_increment_without_crash(tmp_path):
    # new_experiment_id reads the registry OUTSIDE the append lock, so parallel
    # same-prefix+config runs can mint the same NNNN. register_run must retry on
    # ExperimentExistsError so every run persists with a DISTINCT id instead of
    # one crashing. (m2 fix.)
    path = str(tmp_path / "registry.yaml")
    reg = ExperimentRegistry(path)
    n = 12
    barrier = threading.Barrier(n)
    minted = []
    errors = []
    lock = threading.Lock()

    def worker(i):
        try:
            barrier.wait()  # maximize contention: identical prefix + config_hash
            exp_id = lineage.register_run(
                registry=ExperimentRegistry(path),
                prefix="conflict",
                hypothesis_id="H2",
                claim_ids=["C2b"],
                config_hash="sha256:same",
                summary_metrics={"landing_fraction": 0.5},
                seed=i,
            )
            with lock:
                minted.append(exp_id)
        except Exception as exc:  # noqa: BLE001 - surface any failure to the assert
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"unexpected register_run errors: {errors}"
    assert len(set(minted)) == n, f"duplicate ids minted: {sorted(minted)}"
    persisted = reg.ids()
    assert len(persisted) == n
    assert set(persisted) == set(minted)      # every mint persisted, none dropped
