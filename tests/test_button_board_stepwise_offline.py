import importlib.util
import json
from pathlib import Path

from cognitive_console.button_board_stepwise import materials
from cognitive_console.button_board_stepwise.server import EXPORTED_TRIAL_FIELDS
from cognitive_console.button_board_stepwise_materials import MATERIALS_VERSION

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


generator = _load("offline_generator", "scripts/generate_stepwise_offline.py")
aggregator = _load("offline_aggregator", "scripts/aggregate_stepwise_offline.py")


def _payload_from_html(html: str) -> dict:
    marker = '<script id="study-data" type="application/json">'
    raw = html.split(marker, 1)[1].split("</script>", 1)[0]
    return json.loads(raw.replace("<\\/", "</"))


def _base_export(cell: int = 0) -> dict:
    sequence_id = f"BBS11-{cell // 2 + 1:02d}"
    ab_variant = "A" if cell % 2 == 0 else "B"
    metadata = materials.locale_bundle_metadata("en")
    hashes = materials.material_hashes()
    _, _, keys = materials.validated_sources()
    return {
        "export_schema": aggregator.OFFLINE_SCHEMA,
        "signed": False,
        "honesty_notice": "Fictional unsigned exploratory pilot; protocol not frozen.",
        "materials_version": MATERIALS_VERSION,
        "canonical_materials_hash": hashes["canonical_materials_hash"],
        "locale_bundle_version": metadata["locale_bundle_version"],
        "locale_bundle_hash": metadata["locale_bundle_hash"],
        "ab_invariance_hash": keys["ab_invariance_hash"],
        "selected_locale": "en",
        "allocation_cell": cell,
        "sequence_id": sequence_id,
        "ab_variant": ab_variant,
        "participant_label": "P-1",
        "client_started_at": "2026-08-15T00:00:00Z",
        "client_finished_at": "2026-08-15T00:10:00Z",
        "demonstration_status": "acknowledged",
        "attention_selected_id": "INFO",
        "reflection_choice_ids": {
            "hardest": None,
            "confusing": None,
            "amount": None,
            "pace": None,
        },
        "completion_status": "complete",
        "trials": [],
    }


def _trial(slot: dict, answers: list[str], *, corrupt_route: bool = False) -> dict:
    steps = list(range(1, len(answers) + 1))
    route = aggregator.route_participant(
        [{"step": step, "answer": answer} for step, answer in zip(steps, answers)]
    )
    orders = []
    by_step = {
        1: ["INFO", "CONTROL"],
        2: ["COMPARED", "NOT_COMPARED"],
        3: ["BETTER", "NOT_BETTER"],
        4: ["HARM", "NO_HARM"],
        5: ["SCOPE_WRITTEN", "SCOPE_MISSING"],
        6: slot["scope_order_ids"],
    }
    for step in steps:
        orders.append(by_step[step])
    trial = {
        "slot_index": slot["slot_index"],
        "scene_id": slot["scene_id"],
        "variant_id": slot["scene_id"].split("-", 1)[1] if slot["scene_id"].startswith("AB1-") else None,
        "position": slot["position"],
        "planned": True,
        "presented": True,
        "step_presented": steps,
        "step_selected_option_id": answers,
        "step_presented_option_order": orders,
        "step_shown_at_relative": [step * 100 for step in steps],
        "step_answered_at_relative": [step * 100 + 50 for step in steps],
        "participant_exit_step": steps[-1],
        "participant_derived_state": route["state"],
        "scope_selected_id": answers[-1] if steps[-1] == 6 else None,
        "completion_status": "complete",
        "materials_version": MATERIALS_VERSION,
    }
    if corrupt_route:
        trial["participant_derived_state"] = "SUPPORTED"
    assert set(trial) == set(EXPORTED_TRIAL_FIELDS)
    return trial


def _perfect_export() -> dict:
    export = _base_export()
    plan = materials.planned_trials(export["sequence_id"], export["ab_variant"], "0")
    for slot in plan:
        answers = [answer for _, answer in sorted(slot["expected_answer_by_step"].items(), key=lambda x: int(x[0]))]
        export["trials"].append(_trial(slot, answers))
    return export


def test_generated_html_contains_no_answer_keys(tmp_path):
    output = tmp_path / "offline.html"
    generator.generate(output)
    html = output.read_text(encoding="utf-8")
    for blocked in generator.PRIVATE_KEY_PARTS:
        assert blocked.lower() not in html.lower()
    payload = _payload_from_html(html)
    forbidden_keys = set()
    for sequence in ("BBS11-01", "BBS11-12"):
        for variant in ("A", "B"):
            for slot in materials.planned_trials(sequence, variant, "test"):
                forbidden_keys.update(key for key in slot if key not in {"slot_index", "position", "scene_slot", "scene_id", "scope_order_ids"})
    serialized = json.dumps(payload, ensure_ascii=False)
    assert not any(f'"{key}"' in serialized for key in forbidden_keys)


def test_generated_html_has_24_packets_and_integrity_fields(tmp_path):
    output = tmp_path / "offline.html"
    generator.generate(output)
    payload = _payload_from_html(output.read_text(encoding="utf-8"))
    assert len(payload["packets"]) == 24
    assert [packet["allocation_cell"] for packet in payload["packets"]] == list(range(24))
    assert payload["canonical_materials_hash"] == materials.material_hashes()["canonical_materials_hash"]
    assert set(payload["locales"]) == {"en", "zh-Hans"}
    assert all(len(packet["locales"]["en"]) == 6 for packet in payload["packets"])


def test_aggregate_scores_perfect_and_known_wrong_path(tmp_path):
    inputs = tmp_path / "inputs"
    out = tmp_path / "out"
    inputs.mkdir()
    perfect = _perfect_export()
    (inputs / "perfect.json").write_text(json.dumps(perfect), encoding="utf-8")
    wrong = _perfect_export()
    first_slot = materials.planned_trials("BBS11-01", "A", "0")[0]
    wrong["participant_label"] = "wrong"
    wrong["trials"][0] = _trial(first_slot, ["INFO"], corrupt_route=True)
    (inputs / "wrong.json").write_text(json.dumps(wrong), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    rows = {row["participant_label"]: row for row in summary["participants"]}
    assert rows["P-1"]["gaa_rate"] == 1.0
    assert rows["wrong"]["gaa_rate"] < 1.0
    assert any(item["file"] == "wrong.json" for item in summary["warnings"])
    assert (out / "participants.csv").read_bytes().startswith(b"\xef\xbb\xbf")
    assert (out / "per_trial.csv").read_bytes().startswith(b"\xef\xbb\xbf")


def test_aggregate_rejects_signed_v8_and_hash_mismatch(tmp_path):
    inputs = tmp_path / "inputs"
    out = tmp_path / "out"
    inputs.mkdir()
    signed = _perfect_export()
    signed["export_schema"] = "microstudy-export-v8-stepwise-demonstration-signed"
    signed["signed"] = True
    mismatch = _perfect_export()
    mismatch["canonical_materials_hash"] = "0" * 64
    (inputs / "signed.json").write_text(json.dumps(signed), encoding="utf-8")
    (inputs / "mismatch.json").write_text(json.dumps(mismatch), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert {item["file"] for item in summary["skipped_files"]} == {"signed.json", "mismatch.json"}
    assert (out / "participants.csv").exists()
    assert (out / "per_trial.csv").exists()
