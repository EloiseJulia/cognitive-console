"""Config loading/hashing, artifact manifest writer, and lineage registration."""

import numpy as np
import pytest
import yaml

from cognitive_console.config import ExperimentConfig, config_hash, load_config
from cognitive_console.manifest import ArtifactManifest, MANIFEST_FIELDS, write_manifest
from cognitive_console.lineage import new_experiment_id, register_run
from cognitive_console.registry import ExperimentRegistry


# ---- config -------------------------------------------------------------
def test_config_hash_is_order_independent_and_deterministic():
    a = {"axes": ["x", "y"], "layers": [1, 2], "seed": 0}
    b = {"seed": 0, "layers": [1, 2], "axes": ["x", "y"]}
    assert config_hash(a) == config_hash(b)
    c = {"axes": ["x", "y"], "layers": [1, 2], "seed": 1}
    assert config_hash(a) != config_hash(c)


def test_load_config_roundtrip(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump({
        "axes": ["deliberation", "focus"],
        "layers": [4, 8],
        "seed": 3,
        "n_null": 200,
        "max_facade_ratio": 0.7,
        "model": "qwen2.5-7b-instruct",
    }), encoding="utf-8")
    cfg = load_config(p)
    assert isinstance(cfg, ExperimentConfig)
    assert cfg.axes == ["deliberation", "focus"]
    assert cfg.layers == [4, 8]
    assert cfg.seed == 3
    assert cfg.n_null == 200
    assert cfg.max_facade_ratio == 0.7
    assert cfg.hash.startswith("sha256:")


def test_load_config_missing_required_key(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.safe_dump({"layers": [1]}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(p)


def test_repo_config_loads():
    # The shipped experiment config must parse and hash.
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    cfg = load_config(root / "configs" / "phase0-pilot.yaml")
    assert cfg.axes and cfg.layers
    assert cfg.hash.startswith("sha256:")


# ---- manifest -----------------------------------------------------------
def test_manifest_requires_lineage_and_forbids_manual_edits():
    with pytest.raises(ValueError):
        ArtifactManifest(artifact_id="t1", supports_claims=["C1"],
                         source_experiments=[], aggregation_script="s.py",
                         output_file="t.csv")
    with pytest.raises(ValueError):
        ArtifactManifest(artifact_id="t1", supports_claims=["C1"],
                         source_experiments=["exp-1"], aggregation_script="s.py",
                         output_file="t.csv", manual_edits_allowed=True)


def test_manifest_write_roundtrip(tmp_path):
    m = ArtifactManifest(
        artifact_id="facade-table-1",
        supports_claims=["C1"],
        source_experiments=["facade-abcd1234-0001"],
        aggregation_script="scripts/build_facade_table.py",
        aggregation_commit="deadbeef",
        raw_data_hash="sha256:1234",
        output_file="reports/facade_table.csv",
        paper_location="Table 1",
        verdict="pending",
    )
    out = tmp_path / "manifest.yaml"
    row = write_manifest(str(out), m)
    assert list(row.keys()) == MANIFEST_FIELDS
    assert row["manual_edits_allowed"] is False
    on_disk = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert on_disk["artifact_id"] == "facade-table-1"
    assert on_disk["supports_claims"] == ["C1"]


# ---- lineage ------------------------------------------------------------
def test_experiment_ids_unique_per_registry(tmp_path):
    reg = ExperimentRegistry(str(tmp_path / "reg.yaml"))
    id1 = new_experiment_id(reg, "facade", "sha256:abcd1234ffff")
    assert id1 == "facade-abcd1234-0001"
    register_run(reg, "facade", hypothesis_id="H1", claim_ids=["C1"],
                 config_hash="sha256:abcd1234ffff", summary_metrics={"x": 1})
    id2 = new_experiment_id(reg, "facade", "sha256:abcd1234ffff")
    assert id2 == "facade-abcd1234-0002"


def test_register_run_writes_computed_metrics(tmp_path):
    reg = ExperimentRegistry(str(tmp_path / "reg.yaml"))
    exp_id = register_run(
        reg, "facade", hypothesis_id="H1", claim_ids=["C1", "C2a"],
        config_hash="sha256:cafe", summary_metrics={"facade_ratio": 0.31},
        seed=0,
    )
    row = reg.get(exp_id)
    assert row["claim_ids"] == ["C1", "C2a"]
    assert row["summary_metrics"] == {"facade_ratio": 0.31}
    assert row["hardware"] == "cpu-offline"
    assert row["status"] == "done"
