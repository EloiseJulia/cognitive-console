"""Tests for the Study B decoupled offline collector (generator + aggregator).

Verifies the hard participant-side contract (zero answer key / zero Q), schema
validation, submission_id de-duplication, timestamp monotonicity, complete vs.
partial handling, and that the owner-side aggregator emits EMPTY Q placeholder
columns without computing Q. Self-contained: does not import the V3 package.
"""

import csv
import importlib.util
import io
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


generator = _load("studyB_generator", "scripts/generate_studyB_offline.py")
aggregator = _load("studyB_aggregator", "scripts/aggregate_studyB_offline.py")


def _payload_from_html(html: str) -> dict:
    marker = '<script id="study-data" type="application/json">'
    raw = html.split(marker, 1)[1].split("</script>", 1)[0]
    return json.loads(raw.replace("<\\/", "</"))


def _task(task_id: str, condition_order: str = "slider_first", *, complete: bool = True) -> dict:
    return {
        "task_id": task_id,
        "condition_order": condition_order,
        "slider": {
            "final_setting": "s3" if complete else None,
            "settings_explored": 2 if complete else 0,
            "started_at_relative": 1000,
            "committed_at_relative": 1500 if complete else None,
        },
        "own_prompt": {
            "prompt_text": "Please rewrite it warmly and briefly." if complete else "",
            "char_count": 36 if complete else 0,
            "edit_count": 5 if complete else 0,
            "started_at_relative": 1600,
            "committed_at_relative": 2200 if complete else None,
        },
    }


def _base_export(*, complete: bool = True) -> dict:
    order = [
        {"task_id": "draftA-recipe-blurb", "condition_order": "slider_first"},
    ]
    return {
        "export_schema": aggregator.EXPORT_SCHEMA,
        "signed": False,
        "submission_id": str(uuid.uuid4()),
        "honesty_notice": "Fictional illustrative; exploratory pilot; not frozen.",
        "instrument_version": "studyB-collector-offline-0.1.0-draft",
        "selected_locale": "en",
        "consent_agreed": True,
        "consent_agreed_at": "2026-08-17T00:00:00.000Z",
        "consent_copy_version": "studyB-consent-draft-0.1",
        "client_started_at": "2026-08-17T00:00:00.000Z",
        "client_finished_at": "2026-08-17T00:10:00.000Z" if complete else None,
        "completion_status": "complete" if complete else "partial",
        "covariates": {
            "usage_frequency": "weekly",
            "tuned_parameters": "no",
            "understands_latent_control": "a_little",
            "self_rating": 3,
        },
        "probe": {
            "prompt_text": "Rewrite the notice in under 60 words, warm tone.",
            "started_at_relative": 100,
            "committed_at_relative": 800,
            "char_count": 48,
            "edit_count": 12,
        },
        "task_order": {
            "seed": 123456789,
            "sequence": order,
        },
        "tasks": [
            _task("draftA-recipe-blurb", "slider_first", complete=complete),
        ],
        "convenience": {
            "tlx_effort": 3,
            "likert_effort": 4,
            "likert_discoverability": 3,
            "willingness_choice": "own_prompt" if complete else None,
            "willingness_reason": "I trust my own wording.",
        },
        "attention": {"selected_id": "purple" if complete else None},
    }


def _read_csv(path: Path) -> tuple[list[str], list[dict]]:
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames or [], list(reader)


# --- Generator / participant-side contract ------------------------------------


def test_generated_html_contains_no_forbidden_terms(tmp_path):
    output = tmp_path / "studyB.html"
    generator.generate(output)
    html = output.read_text(encoding="utf-8")
    lowered = html.lower()
    for term in generator.FORBIDDEN_TERMS:
        assert term not in lowered


def test_generated_payload_has_no_answer_keys(tmp_path):
    output = tmp_path / "studyB.html"
    generator.generate(output)
    payload = _payload_from_html(output.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for term in ("expected", "answer_key", "rubric", "ground_truth", "correct_answer"):
        assert term not in serialized
    assert payload["export_schema"] == aggregator.EXPORT_SCHEMA
    assert payload["signed"] is False
    assert len(payload["tasks"]) == 1
    assert set(payload["honesty_notice"]) == {"en", "zh-Hans"}
    # No submission_id is baked into the static payload.
    assert "submission_id" not in payload


def test_html_generates_submission_id_at_runtime(tmp_path):
    output = tmp_path / "studyB.html"
    generator.generate(output)
    html = output.read_text(encoding="utf-8")
    assert "crypto.randomUUID" in html
    payload = _payload_from_html(html)
    assert "submission_id" not in payload


# --- Aggregator: acceptance & artifacts ---------------------------------------


def test_aggregate_accepts_valid_export_and_writes_bom(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    (inputs / "p1.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 1
    assert summary["task_row_count"] == 1
    assert (out / "participants.csv").read_bytes().startswith(b"\xef\xbb\xbf")
    assert (out / "tasks.csv").read_bytes().startswith(b"\xef\xbb\xbf")
    assert summary["q_scoring"]["computed_here"] is False


def test_tasks_csv_has_empty_q_placeholder_columns(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    (inputs / "p1.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    aggregator.aggregate(inputs, out)
    fields, rows = _read_csv(out / "tasks.csv")
    for column in aggregator.TASK_Q_PLACEHOLDER_COLUMNS:
        assert column in fields
        assert all(row[column] == "" for row in rows)


def test_participants_csv_carries_covariates_and_effort(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    (inputs / "p1.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    aggregator.aggregate(inputs, out)
    fields, rows = _read_csv(out / "participants.csv")
    row = rows[0]
    assert row["cov_self_rating"] == "3"
    assert row["willingness_choice"] == "own_prompt"
    assert row["probe_duration_ms"] == "700"
    assert row["n_tasks"] == "1"
    assert "confidence_own_prompt" not in fields
    assert "tlx_mental" not in fields


# --- Aggregator: de-duplication -----------------------------------------------


def test_aggregate_deduplicates_repeated_submission_id(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    (inputs / "a.json").write_text(json.dumps(export), encoding="utf-8")
    (inputs / "b.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 1
    assert {item["file"] for item in summary["skipped_files"]} == {"b.json"}
    assert any("duplicate" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_counts_distinct_submission_ids_separately(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    (inputs / "a.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    (inputs / "b.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 2
    assert summary["skipped_files"] == []


# --- Aggregator: rejections ---------------------------------------------------


def test_aggregate_rejects_missing_submission_id(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    del export["submission_id"]
    (inputs / "no-id.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert {item["file"] for item in summary["skipped_files"]} == {"no-id.json"}


def test_aggregate_rejects_signed_and_wrong_schema(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    signed = _base_export()
    signed["signed"] = True
    wrong = _base_export()
    wrong["export_schema"] = "microstudy-export-offline-stepwise-v1"
    (inputs / "signed.json").write_text(json.dumps(signed), encoding="utf-8")
    (inputs / "wrong.json").write_text(json.dumps(wrong), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert {item["file"] for item in summary["skipped_files"]} == {"signed.json", "wrong.json"}


def test_aggregate_rejects_injected_answer_key(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["tasks"][0]["answer_key"] = "s3"
    (inputs / "leak.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("private key" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_container_smuggled_into_scalar_field(tmp_path):
    """MAJOR-1 regression: an answer hidden in a harmless-keyed nested container
    (dict or list) inside a scalar field must be rejected, not accepted."""
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    dict_leak = _base_export()
    dict_leak["covariates"]["self_rating"] = {"winner": "s3"}
    (inputs / "dict_leak.json").write_text(json.dumps(dict_leak), encoding="utf-8")
    list_leak = _base_export()
    list_leak["convenience"]["willingness_choice"] = ["own_prompt", "s3"]
    (inputs / "list_leak.json").write_text(json.dumps(list_leak), encoding="utf-8")
    conv_leak = _base_export()
    conv_leak["convenience"]["tlx_effort"] = {"answer": "s3"}
    (inputs / "conv_leak.json").write_text(json.dumps(conv_leak), encoding="utf-8")
    attention_leak = _base_export()
    attention_leak["attention"]["selected_id"] = {"answer": "purple"}
    (inputs / "attention_leak.json").write_text(json.dumps(attention_leak), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    skipped = {item["file"] for item in summary["skipped_files"]}
    assert skipped == {
        "dict_leak.json",
        "list_leak.json",
        "conv_leak.json",
        "attention_leak.json",
    }
    assert all("scalar value" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_non_monotonic_timestamps(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["probe"]["committed_at_relative"] = 10  # before started_at_relative=100
    (inputs / "bad.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("precedes" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_task_order_disagreement(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["task_order"]["sequence"][0]["condition_order"] = "prompt_first"
    (inputs / "bad.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("condition order" in item["reason"] for item in summary["skipped_files"])


# --- Aggregator: partial completion -------------------------------------------


def test_aggregate_accepts_partial_completion(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export(complete=False)
    (inputs / "partial.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 1
    _, rows = _read_csv(out / "participants.csv")
    assert rows[0]["completion_status"] == "partial"


def test_aggregate_rejects_complete_status_without_evidence(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export(complete=False)
    export["completion_status"] = "complete"  # lie: not actually complete
    (inputs / "liar.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("complete export" in item["reason"] for item in summary["skipped_files"])


# --- Aggregator: simplified-schema regressions (D-0132) ------------------------


def test_aggregate_accepts_exactly_one_task(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    (inputs / "p1.json").write_text(json.dumps(_base_export()), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 1
    _, rows = _read_csv(out / "tasks.csv")
    assert len(rows) == 1


def test_aggregate_rejects_two_tasks(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["tasks"].append(_task("draftB-email-reply", "prompt_first"))
    export["task_order"]["sequence"].append(
        {"task_id": "draftB-email-reply", "condition_order": "prompt_first"}
    )
    (inputs / "two.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("exactly one task" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_reintroduced_reliance_field(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["reliance"] = {"confidence_slider": 3, "confidence_own_prompt": 4}
    (inputs / "reliance.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("top-level field" in item["reason"] for item in summary["skipped_files"])


def test_aggregate_rejects_extra_convenience_field(tmp_path):
    inputs = tmp_path / "in"
    out = tmp_path / "out"
    inputs.mkdir()
    export = _base_export()
    export["convenience"]["tlx_mental"] = 4
    (inputs / "extra.json").write_text(json.dumps(export), encoding="utf-8")
    summary = aggregator.aggregate(inputs, out)
    assert summary["participant_count"] == 0
    assert any("convenience" in item["reason"] for item in summary["skipped_files"])
