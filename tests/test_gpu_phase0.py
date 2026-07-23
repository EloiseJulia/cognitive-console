"""Offline tests for scripts/run_gpu_phase0.py audit fixes (no torch/model/network).

Covers:
* M3 — the prompt-ceiling default uses the FULL authored strong-prompt set (n_strong=16).
* m1 — the artifact manifest hashes the WRITTEN results JSON (lineage / tamper detection),
        not the config JSON.
* m3 — axes on an unstable/unconfirmed C1 layer are flagged and EXCLUDED from the
        "steer reaches beyond ceiling" headline count.
"""

import json

import yaml

import scripts.run_c1_facade as c1
import scripts.run_gpu_phase0 as g


# --------------------------------------------------------------------------- #
# M3 — full authored strong-prompt set by default
# --------------------------------------------------------------------------- #
def test_n_strong_default_is_full_authored_set():
    assert g.DEFAULT_N_STRONG == 16
    args = g.build_parser().parse_args([])
    assert args.n_strong == 16


def test_authored_strong_prompt_files_have_16():
    for axis in g.DEFAULT_AXES:
        sp = c1.load_strongest_prompts(axis)
        assert len(sp.ids) == 16, f"{axis}: expected 16 authored strong prompts"


# --------------------------------------------------------------------------- #
# m3 — unstable-layer flag + headline exclusion
# --------------------------------------------------------------------------- #
def test_is_unstable_axis():
    assert g._is_unstable_axis(False) is True      # explicit unstable (e.g. focus @1.5B)
    assert g._is_unstable_axis(None) is True        # unconfirmed / no C1
    assert g._is_unstable_axis(True) is False       # stable layer confirmed


def test_aggregate_excludes_unstable_axes_from_headline():
    rows = [
        {"axis": "a", "reaches_beyond_prompt_ceiling": True, "c2b_on_unstable_layer": False},
        {"axis": "b", "reaches_beyond_prompt_ceiling": True, "c2b_on_unstable_layer": True},
        {"axis": "c", "reaches_beyond_prompt_ceiling": False, "c2b_on_unstable_layer": False},
    ]
    agg = g._c2b_aggregate(rows)
    assert agg["n_axes"] == 3
    assert agg["n_axes_on_unstable_layer"] == 1
    assert agg["n_axes_counted_for_headline"] == 2
    # 'b' reaches beyond but is on an unstable layer -> NOT counted.
    assert agg["n_axes_steer_beyond_prompt_ceiling"] == 1
    assert agg["headline_excludes_unstable"] is True


# --------------------------------------------------------------------------- #
# m1 — artifact-lineage hash is of the written results JSON, not the config
# --------------------------------------------------------------------------- #
def _minimal_payload():
    row = {
        "axis": "deliberation",
        "layer": 12,
        "prompt_ceiling": 0.4,
        "steer_only_max": 0.6,
        "reaches_beyond_prompt_ceiling": True,
        "beyond_margin": 0.2,
        "conflict": [],
        "c2b_on_unstable_layer": False,
    }
    axes = [row]
    return {
        "kind": "c2b_reachability_pilot",
        "type": "EXPLORATORY",
        "valid_for_paper": False,
        "protocol_frozen": False,
        "model": "test/model",
        "alphas": [4.0, 8.0],
        "n_strong": 16,
        "max_new_tokens": 8,
        "neutral_prompt": "neutral",
        "prompt_ceiling_label": "prompt ceiling = best-of-16 static authored prompts, NOT OPRO",
        "c2b_honesty_caveat": g.C2B_HONESTY_CAVEAT,
        "behavior_proxy_note": "crude proxies",
        "axes": axes,
        "aggregate": g._c2b_aggregate(axes),
    }


def test_manifest_hashes_written_artifact_not_config(tmp_path):
    payload = _minimal_payload()
    out_dir = tmp_path / "c2b"
    json_path = g._write_c2b(payload, out_dir)
    g._register_c2b(payload, out_dir, json_path, seed=1, hardware="cpu-test")

    manifest = yaml.safe_load((out_dir / "c2b_reachability_table.manifest.yaml").read_text(encoding="utf-8"))
    artifact_hash = c1._sha256_file(json_path)

    assert manifest["raw_data_hash"] == artifact_hash
    # It must NOT be the old config-hash behaviour.
    cfg = {
        "kind": "c2b_reachability_pilot",
        "model": payload["model"],
        "axes": [r["axis"] for r in payload["axes"]],
        "alphas": payload["alphas"],
        "n_strong": payload["n_strong"],
        "max_new_tokens": payload["max_new_tokens"],
        "seed": 1,
    }
    config_hash_val = c1._sha256_str(json.dumps(cfg, sort_keys=True))
    assert manifest["raw_data_hash"] != config_hash_val


def test_manifest_hash_detects_artifact_tampering(tmp_path):
    payload = _minimal_payload()
    out_dir = tmp_path / "c2b"
    json_path = g._write_c2b(payload, out_dir)
    g._register_c2b(payload, out_dir, json_path, seed=1, hardware="cpu-test")
    recorded = yaml.safe_load(
        (out_dir / "c2b_reachability_table.manifest.yaml").read_text(encoding="utf-8")
    )["raw_data_hash"]

    # Tamper with the artifact after the manifest was written.
    json_path.write_text(json_path.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    assert c1._sha256_file(json_path) != recorded


# --------------------------------------------------------------------------- #
# honesty caveat carried on the summary
# --------------------------------------------------------------------------- #
def test_summary_carries_honesty_caveat_and_ceiling_label(tmp_path):
    payload = _minimal_payload()
    out_dir = tmp_path / "c2b"
    g._write_c2b(payload, out_dir)
    summary = (out_dir / "c2b_reachability_summary.md").read_text(encoding="utf-8")
    assert "HONESTY CAVEAT" in summary
    assert "NOT OPRO" in summary
    assert "best-of-16" in summary
