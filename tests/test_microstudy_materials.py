import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from cognitive_console.microstudy_materials import (
    EXPORT_SCHEMA_VERSION,
    MATERIALS_PATH,
    MATERIALS_VERSION,
    MATERIAL_SCHEMA_VERSION,
    SEQUENCES_PATH,
    SEQUENCE_SCHEMA_VERSION,
    SOURCE_REGISTRY_PATH,
    TICKET_CODES,
    TICKET_STATE_BY_CODE,
    _ticket_definitions,
    canonical_locale_bytes,
    derive_policy_state,
    derive_ticket_keys,
    extract_real_evidence,
    generate_materials,
    generate_sequences,
    load_sources,
    locale_manifest,
    private_answer_keys,
    validate_materials,
    verified_source_payloads,
)


REPO = Path(__file__).resolve().parents[1]
REQUIRED_SOURCE_HASHES = {
    "C1_QWEN": "23dd0d3d58d9d47a9204a1d4226335232769b4669006f001c11bd8126a03b76e",
    "C1_LLAMA": "64a4a1d9cc4312ade3a9c231348403c7608d00eb942431d33286bf80cf52de46",
    "E0006_ARM": "4614ff8277f3f6eed485169b0b4a00d4bf3978d487976318416692689cc32d19",
    "E0006_CAA_QWEN": "bc75c3ec8d21ffa9037dab1c5e819fbac079985cdd9c8a5c9e5c858595ea1243",
    "E0006_CAA_LLAMA": "7eec31c535058d1fb57e2fb2c14fdffe7cf02b47cc2275c2692e09456a08ade6",
    "E0006_ITI_QWEN": "8ae205457c932c6417e37d546197ba609961b8accc6133bef0b51186fb3ec026",
    "E0006_ITI_LLAMA": "46606736c0d122a74a3c8deb7b89bbf68192457ba675cf33954034f9fdf84f43",
    "E0011_MULTI": "edcc3f4ce770bb10264e670b04afde9f84a2068e94a31c49a4c16bf382cc0927",
    "E0013_FORMAT": "6554565952f1b5f0334b37f1e78f9c2af66d951c380dc9f3c86f312f0f028884",
    "E0014_ENDPOINT": "8c0b9b65e872a888bcb8c62cac39515a8741a25634e7cec58f5d3dce901f445f",
    "E0015_SCALE": "9bc450a4184aa9bdc617953dba8acdd3c9e0ef25883f706d31142d9665fb89ec",
}


def test_authoritative_v9_sources_validate_with_exact_balance_report():
    report = validate_materials()
    assert report == {
        "status": "PASS",
        "schema_version": MATERIAL_SCHEMA_VERSION,
        "materials_version": MATERIALS_VERSION,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "locale_manifest": locale_manifest(load_sources()[0]),
        "source_count": 13,
        "ticket_count": 6,
        "state_distribution": {"W": 2, "S": 1, "U": 2, "D": 1},
        "q2_unique": True,
        "mde_status": "UNVERIFIED_NOT_ESTIMATED",
        "sequence_count": 12,
        "valid_order_count": 48,
        "exact_cover_cells": 72,
        "first_six_balanced": True,
        "last_six_balanced": True,
        "source_balanced": True,
        "state_balanced": True,
        "period_balanced": True,
    }


def test_source_registry_verifies_exact_canonical_git_blobs():
    registry = json.loads(SOURCE_REGISTRY_PATH.read_text(encoding="utf-8"))
    rows = {row["source_id"]: row for row in registry["sources"]}
    assert registry["hash_basis"] == "git_blob_bytes"
    assert len(rows) == 13
    for source_id, expected_hash in REQUIRED_SOURCE_HASHES.items():
        assert rows[source_id]["canonical_sha256"] == expected_hash
        blob = subprocess.run(
            ["git", "show", f"{rows[source_id]['commit']}:{rows[source_id]['path']}"],
            cwd=REPO,
            check=True,
            capture_output=True,
        ).stdout
        assert hashlib.sha256(blob).hexdigest() == expected_hash
    assert "EVIDENCE_LEDGER" not in rows
    assert "64171bfa860495b5be3151848c808af1deb70edab4afed1bdd93c9294677f669" not in (
        SOURCE_REGISTRY_PATH.read_text(encoding="utf-8")
    )
    payloads, lineage = verified_source_payloads()
    assert set(payloads) == set(rows)
    assert {row["source_id"] for row in lineage} == set(rows)


def test_generator_is_the_only_export_and_is_idempotent():
    generated_materials, _ = generate_materials()
    generated_sequences = generate_sequences()
    actual_materials, actual_sequences = load_sources()
    assert actual_materials == generated_materials
    assert actual_sequences == generated_sequences
    before = (MATERIALS_PATH.read_bytes(), SEQUENCES_PATH.read_bytes())
    subprocess.run(
        [sys.executable, "scripts/generate_microstudy_v9.py"],
        cwd=REPO,
        check=True,
    )
    assert before == (MATERIALS_PATH.read_bytes(), SEQUENCES_PATH.read_bytes())
    checked = subprocess.run(
        [sys.executable, "scripts/generate_microstudy_v9.py", "--check"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "current" in checked.stdout
    report = subprocess.run(
        [sys.executable, "scripts/validate_microstudy_materials.py"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(report.stdout)["schema_version"] == MATERIAL_SCHEMA_VERSION


def test_real_evidence_is_extracted_from_verified_payloads_with_required_caveats():
    payloads, _ = verified_source_payloads()
    evidence = extract_real_evidence(payloads)
    assert evidence["arm"] == {"n_cells": 4, "zero_pass_cells": 4}
    assert evidence["multiseed"] == {"n_seeds": 5, "same_pool": True}
    assert evidence["format"]["other_cells_unrechecked"] == 3
    assert evidence["format"]["complete_case_ci_high"] < 0
    assert evidence["format"]["missingness_low"] < 0 < evidence["format"]["missingness_high"]
    assert abs(evidence["format"]["compliance_delta_vs_baseline"]) < 0.02
    assert abs(evidence["format"]["brier_delta_vs_baseline"]) < 0.01
    assert evidence["scale"]["any_latent_pass"] is False
    assert evidence["deliberation"]["token_cap"] == 64
    assert all(
        value > evidence["skepticism"]["sesoi"]
        for value in evidence["skepticism"]["mdes"]
    )


def test_private_keys_have_exact_state_and_q2_distribution_without_public_leakage():
    keys = private_answer_keys()
    assert {ticket: row["state"] for ticket, row in keys.items()} == TICKET_STATE_BY_CODE
    assert {ticket: row["q1_code"] for ticket, row in keys.items()} == {
        "UNC-R": "C",
        "UNC-S": "D",
        "SKEP-R": "A",
        "SKEP-S": "B",
        "DELIB-R": "A",
        "DELIB-S": "C",
    }
    assert {ticket: row["q2_code"] for ticket, row in keys.items()} == dict(
        zip(TICKET_CODES, "ABCDEF")
    )
    assert Counter(row["state"] for row in keys.values()) == {
        "U": 2,
        "D": 1,
        "W": 2,
        "S": 1,
    }
    public = MATERIALS_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "expected_q1", "expected_q2", "correct_key", "q1_key", "q2_key",
        "Q2_COMPARATOR_MISSINGNESS", "Q2_SCOPE_BOUNDARY",
        "Q2_UNDERPOWERED_COMPARISON", "Q2_MISSING_PAIRED_COMPARISON",
        "Q2_DECISIVE_PAIRED_TEST", "Q2_QUALITY_COHERENCE_FAIL",
    ):
        assert forbidden not in public


def test_answer_derivation_is_invariant_to_every_nonkey_field():
    payloads, lineage = verified_source_payloads()
    definitions = _ticket_definitions(extract_real_evidence(payloads), lineage)
    for ticket in definitions:
        expected = derive_ticket_keys(ticket)
        assert derive_ticket_keys({
            "policy_inputs": copy.deepcopy(ticket["policy_inputs"]),
            "decisive_issue": ticket["decisive_issue"],
        }) == expected
        for field in set(ticket) - {"policy_inputs", "decisive_issue"}:
            changed = copy.deepcopy(ticket)
            del changed[field]
            assert derive_ticket_keys(changed) == expected
    assert derive_policy_state({
        "read_status": "usable",
        "paired_comparison": "decisive_positive",
        "quality_status": "pass",
        "scope_status": "exact",
    }) == "S"
    assert derive_policy_state({
        "read_status": "usable",
        "paired_comparison": "missing",
        "quality_status": "unverified",
        "scope_status": "bounded",
    }) == "D"


def test_bilingual_contract_flat_parity_and_visible_policy():
    materials, _ = load_sources()
    assert materials["locale_contract"] == {
        "version": "microstudy-v9-locale-contract-v1",
        "supported": ["en", "zh-Hans"],
        "fallback": None,
        "auto_detect": False,
        "stable_id_parity": True,
        "human_semantic_review": "UNVERIFIED_PRE_RECRUITMENT",
    }
    manifest = locale_manifest(materials)
    for locale in ("en", "zh-Hans"):
        assert manifest[locale]["locale_bundle_hash"] == hashlib.sha256(
            canonical_locale_bytes(materials["locales"][locale])
        ).hexdigest()
        bundle = materials["locales"][locale]
        assert len(bundle["contract_headings"]) == 4
        assert [row["id"] for row in bundle["q1"]["options"]] == list("ABCD")
        assert [row["id"] for row in bundle["q2"]["options"]] == list("ABCDEF")
        assert len(bundle["tickets"]) == 6
        for ticket in bundle["tickets"]:
            assert len(ticket["facts"]) == 6
            assert len(ticket["outputs"]) == 2
            assert sorted(ticket["flat_order"]) == list(range(6))
            assert ticket["source_badge"] in {"SOURCE-BACKED", "SIMULATED"}
    assert manifest["en"]["locale_bundle_hash"] != manifest["zh-Hans"]["locale_bundle_hash"]
    render = materials["nonlocalized"]["render_contract"]
    assert render["contract_group_sizes"] == [1, 2, 2, 1]
    assert render["only_badges"] == [
        "SOURCE-BACKED", "SIMULATED", "ILLUSTRATIVE OUTPUT"
    ]


def test_required_ticket_caveats_and_audio_practice_are_visible():
    materials, _ = load_sources()
    for locale in ("en", "zh-Hans"):
        tickets = {
            row["ticket_code"]: "\n".join(row["facts"])
            for row in materials["locales"][locale]["tickets"]
        }
        if locale == "en":
            assert all(marker in tickets["UNC-R"] for marker in (
                "4 had no passing axis", "approximately baseline", "complete-case",
                "bounds cross zero", "other 3 cells are unrechecked",
                "latent arms still had no pass",
            ))
            assert all(marker in tickets["SKEP-R"] for marker in (
                "underpowered", "MDEs", "target effect",
            ))
            assert all(marker in tickets["DELIB-R"] for marker in (
                "mixed near zero", "64-token cap", "decisive paired test",
            ))
        else:
            assert all(marker in tickets["UNC-R"] for marker in (
                "没有任何轴通过", "基本相当", "完整案例", "边界跨过零",
                "其余 3 个单元尚未复查", "仍没有潜在干预通过",
            ))
            assert all(marker in tickets["SKEP-R"] for marker in (
                "检验力不足", "MDE", "目标效应",
            ))
            assert all(marker in tickets["DELIB-R"] for marker in (
                "零附近呈混合结果", "64 个 token", "有判定力的配对检验",
            ))
        practice = materials["locales"][locale]["practice"]
        assert len(practice["facts"]) == 6
        assert [row["id"] for row in practice["q2_options"]] == list("ABCD")
        assert "router" not in json.dumps(practice, ensure_ascii=False).lower()
    assert "does not offer" in materials["locales"]["en"]["practice"]["facts"][-1]
    assert "W" in materials["locales"]["en"]["practice"]["feedback"]


def test_twelve_sequences_are_deterministic_exact_cover_and_complemented():
    sequences = generate_sequences()["sequences"]
    assert [row["code"] for row in sequences] == [
        f"V9-{index:02d}" for index in range(1, 13)
    ]
    cells = Counter()
    for sequence in sequences:
        slots = sequence["slots"]
        assert len(slots) == 6
        assert {row["ticket_code"] for row in slots} == set(TICKET_CODES)
        assert Counter(row["condition"] for row in slots) == {"C": 3, "F": 3}
        for scenario in ("UNC", "SKEP", "DELIB"):
            assert {
                row["condition"]
                for row in slots
                if row["ticket_code"].startswith(scenario)
            } == {"C", "F"}
            positions = [
                row["position"]
                for row in slots
                if row["ticket_code"].startswith(scenario)
            ]
            assert abs(positions[0] - positions[1]) >= 3
        for row in slots:
            cells[row["ticket_code"], row["condition"], row["position"]] += 1
    assert len(cells) == 72 and set(cells.values()) == {1}
    for first, second in zip(sequences[:6], sequences[6:]):
        assert [row["ticket_code"] for row in first["slots"]] == [
            row["ticket_code"] for row in second["slots"]
        ]
        assert all(
            left["condition"] != right["condition"]
            for left, right in zip(first["slots"], second["slots"])
        )


def test_v8_artifacts_remain_historical_and_separate():
    historical = REPO / "data" / "microstudy_contract_application" / "stimuli.json"
    old = json.loads(historical.read_text(encoding="utf-8"))
    assert old["schema_version"] == "microstudy-stimuli-v8-bilingual-novice-ux"
    assert MATERIALS_PATH != historical
    assert SEQUENCES_PATH.name == "sequences.json"
    assert SOURCE_REGISTRY_PATH.parent.name == "microstudy_scenario_v9"
