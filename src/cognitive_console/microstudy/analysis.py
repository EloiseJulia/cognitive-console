"""Strict, preregistered analysis and assumption-labelled MDE simulation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import itertools
import json
import math
import random
import statistics
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from cognitive_console.microstudy_materials import route_state

from .materials import material_hashes, planned_trials, validated_sources
from .server import canonical_bytes

BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 20_260_810


class ExportError(ValueError):
    def __init__(self, message: str, reason: str = "technical_corrupt"):
        super().__init__(message)
        self.reason = reason


def _check(condition: bool, message: str, reason: str = "technical_corrupt") -> None:
    if not condition:
        raise ExportError(message, reason)


def _is_bool(value: Any) -> bool:
    return type(value) is bool


def validate_export(data: dict[str, Any], verification_key: bytes) -> dict[str, Any]:
    stimuli, sequences = validated_sources()
    hashes = material_hashes()
    _check(isinstance(data, dict), "export must be an object")
    verification = data.get("verification")
    _check(
        isinstance(verification, dict)
        and set(verification) == {"algorithm", "key_id", "signature"},
        "missing or invalid verification block",
    )
    _check(verification["algorithm"] == "HMAC-SHA256", "wrong signature algorithm")
    _check(
        verification["key_id"] == hashlib.sha256(verification_key).hexdigest()[:16],
        "wrong verification key",
    )
    signature = hmac.new(verification_key, canonical_bytes(data), hashlib.sha256).hexdigest()
    _check(
        isinstance(verification["signature"], str)
        and hmac.compare_digest(verification["signature"], signature),
        "signature mismatch",
    )
    _check(data.get("export_schema_version") == "microstudy-export-v3-signed", "wrong export schema")
    _check(
        data.get("material_schema_version") == stimuli["schema_version"],
        "wrong material schema",
        "materials_version_mismatch",
    )
    _check(
        data.get("sequence_schema_version") == sequences["schema_version"],
        "wrong sequence schema",
        "sequence_mismatch",
    )
    _check(
        data.get("material_hashes") == hashes,
        "wrong material hashes",
        "materials_version_mismatch",
    )
    session_fields = stimuli["export_schema"]["session_fields"]
    expected_top = {
        "export_schema_version",
        "material_schema_version",
        "sequence_schema_version",
        "material_hashes",
        "verification",
        "trials",
        *session_fields,
    }
    _check(set(data) == expected_top, "unexpected or missing top-level export fields")
    for field in session_fields:
        _check(field in data, f"missing session field: {field}")
    for field in (
        "practice_presented", "practice_q1_submitted", "practice_q2_submitted",
        "practice_complete", "post_task_diagnostic_presented",
        "post_task_diagnostic_submitted", "mechanical_exclusion", "complete",
    ):
        _check(_is_bool(data[field]), f"{field} must be boolean")
    try:
        _check(uuid.UUID(data["attempt_id"]).version == 4, "attempt_id must be UUIDv4")
    except (ValueError, AttributeError, TypeError):
        raise ExportError("attempt_id must be UUIDv4") from None
    try:
        _check(uuid.UUID(data["run_id"]).version == 4, "run_id must be UUIDv4")
    except (ValueError, AttributeError, TypeError):
        raise ExportError("run_id must be UUIDv4") from None
    _check(
        type(data["attempt_serial"]) is int and data["attempt_serial"] >= 1,
        "attempt_serial must be a positive integer",
    )
    _check(
        isinstance(data["participant_code"], str)
        and 1 <= len(data["participant_code"]) <= 64
        and all(character.isalnum() or character in "._-" for character in data["participant_code"]),
        "invalid participant code",
    )
    _check(
        data["practice_complete"]
        == (data["practice_q1_submitted"] and data["practice_q2_submitted"]),
        "practice transition invalid",
        "impossible_state_transition",
    )
    _check(
        data["practice_presented"] and data["practice_complete"],
        "complete export requires presented, completed practice",
        "impossible_state_transition",
    )
    _check(
        not data["practice_q2_submitted"] or data["practice_q1_submitted"],
        "practice Q2 precedes Q1",
        "impossible_state_transition",
    )
    ease_keys = {row["key"] for row in stimuli["participant_materials"]["block_ease"]["options"]}
    _check(data["block_1_ease"] is None or data["block_1_ease"] in ease_keys, "invalid block 1 ease")
    _check(data["block_2_ease"] is None or data["block_2_ease"] in ease_keys, "invalid block 2 ease")
    diagnostic = stimuli["participant_materials"]["post_task_manipulation_diagnostic"]
    diagnostic_keys = {row["key"] for row in diagnostic["options"]}
    if data["post_task_diagnostic_submitted"]:
        _check(data["post_task_diagnostic_presented"], "diagnostic submitted before presentation")
        _check(data["post_task_diagnostic_response"] in diagnostic_keys, "invalid diagnostic response")
        _check(
            data["post_task_diagnostic_correct"]
            == (data["post_task_diagnostic_response"] == diagnostic["correct_key"]),
            "wrong diagnostic scoring",
        )
    else:
        _check(
            data["post_task_diagnostic_response"] is None
            and data["post_task_diagnostic_correct"] is None,
            "unsubmitted diagnostic populated",
        )
    _check(data["mechanical_exclusion"] is False, "client cannot set exclusions")
    _check(data["mechanical_exclusion_reason"] == "none", "client cannot set exclusion reason")
    trials = data.get("trials")
    _check(isinstance(trials, list) and len(trials) == 10, "exactly ten trial slots required")
    try:
        plan = planned_trials(data["sequence"])
    except ValueError:
        raise ExportError("unknown sequence", "sequence_mismatch") from None
    items = {item["stimulus_id"]: item for item in stimuli["items"]}
    allowed_q1 = {row["key"] for row in stimuli["q1"]["options"]}
    templates = {row["template_id"]: row for row in stimuli["q2_templates"]}
    trial_fields = stimuli["export_schema"]["trial_fields"]
    for expected, trial in zip(plan, trials):
        _check(set(trial) == set(trial_fields), "unexpected or missing trial fields")
        for field in trial_fields:
            _check(field in trial, f"missing trial field: {field}")
        for field in ("slot_index", "condition", "item", "pattern", "content_set", "block", "position"):
            _check(
                trial[field] == expected[field],
                f"sequence mismatch at {field}",
                "sequence_mismatch",
            )
        for field in (
            "planned", "presented", "q1_submitted", "q2_submitted", "complete",
            "submitted", "hypothetical", "q1_missing", "q2_missing",
            "q1_correct_missing", "q2_correct_missing", "cca_correct_missing",
            "rt_q1_missing", "rt_q2_missing", "rt_total_missing", "hidden_ms_missing",
        ):
            _check(_is_bool(trial[field]), f"{field} must be boolean")
        for field in ("q1_correct", "q2_correct", "cca_correct"):
            _check(trial[field] is None or _is_bool(trial[field]), f"{field} must be boolean or null")
        _check(trial["planned"] is True, "planned must be true")
        _check(
            trial["q2_submitted"] <= trial["q1_submitted"] <= trial["presented"],
            "impossible submit transition",
            "impossible_state_transition",
        )
        _check(
            trial["complete"] == (trial["q1_submitted"] and trial["q2_submitted"]),
            "complete invariant failed",
            "impossible_state_transition",
        )
        _check(
            trial["submitted"] == trial["complete"],
            "submitted invariant failed",
            "impossible_state_transition",
        )
        item = items[trial["item"]]
        derived_q1 = route_state(item["state_routing_inputs"])
        _check(derived_q1 == expected["q1_key"], "router mismatch")
        _check(expected["q2_key"] == item["q2"]["correct_key"], "Q2 key mismatch")
        if trial["q1_submitted"]:
            _check(trial["q1"] in allowed_q1, "invalid Q1 response")
            _check(trial["q1_correct"] == (trial["q1"] == derived_q1), "wrong Q1 scoring")
        else:
            _check(trial["q1"] is None and trial["q1_correct"] is None, "unsubmitted Q1 populated")
        if trial["q2_submitted"]:
            q2_keys = {row["key"] for row in templates[expected["q2_template_id"]]["options"]}
            _check(trial["q2"] in q2_keys, "invalid Q2 response")
            _check(trial["q2_correct"] == (trial["q2"] == expected["q2_key"]), "wrong Q2 scoring")
            _check(
                trial["cca_correct"] == (trial["q1_correct"] and trial["q2_correct"]),
                "wrong CCA scoring",
            )
        else:
            _check(trial["q2"] is None and trial["q2_correct"] is None, "unsubmitted Q2 populated")
        for field in ("rt_q1_ms", "rt_q2_ms", "rt_total_ms", "hidden_ms"):
            value = trial[field]
            _check(value is None or (type(value) is int and value >= 0), f"invalid {field}")
        for value_field, missing_field in (
            ("q1", "q1_missing"),
            ("q2", "q2_missing"),
            ("q1_correct", "q1_correct_missing"),
            ("q2_correct", "q2_correct_missing"),
            ("cca_correct", "cca_correct_missing"),
            ("rt_q1_ms", "rt_q1_missing"),
            ("rt_q2_ms", "rt_q2_missing"),
            ("rt_total_ms", "rt_total_missing"),
            ("hidden_ms", "hidden_ms_missing"),
        ):
            _check(
                trial[missing_field] == (trial[value_field] is None),
                f"missing flag mismatch for {value_field}",
            )
        if trial["complete"]:
            _check(
                trial["rt_total_ms"] == trial["rt_q1_ms"] + trial["rt_q2_ms"],
                "RT total mismatch",
            )
        _check(
            trial["materials_version"] == stimuli["materials_version"],
            "materials version mismatch",
            "materials_version_mismatch",
        )
        _check(trial["source_status"] == item["source_status"], "source status mismatch")
        _check(trial["source_note"] == item["source_note"], "source note mismatch")
        _check(trial["hypothetical"] == item["hypothetical"], "hypothetical mismatch")
    completed = sum(row["complete"] for row in trials)
    presented = sum(row["presented"] for row in trials)
    _check(
        [row["presented"] for row in trials]
        == [True] * presented + [False] * (10 - presented),
        "presented trials must form a prefix",
        "impossible_state_transition",
    )
    _check(
        [row["complete"] for row in trials]
        == [True] * completed + [False] * (10 - completed),
        "complete trials must form a prefix",
        "impossible_state_transition",
    )
    _check(
        presented in {completed, completed + 1},
        "at most one presented trial may be incomplete",
        "impossible_state_transition",
    )
    if data["post_task_diagnostic_presented"]:
        _check(
            completed == 10,
            "diagnostic cannot precede ten complete trials",
            "impossible_state_transition",
        )
    if data["complete"]:
        _check(completed == 10, "signed complete export must contain ten complete trials")
        _check(data["completion_status"] == "complete", "completion status mismatch")
        _check(
            data["post_task_diagnostic_presented"],
            "complete export requires diagnostic presentation",
            "impossible_state_transition",
        )
    else:
        _check(presented >= 1, "partial export requires a formal trial presentation")
        _check(data["completion_status"] == "partial", "completion status mismatch")
    return data


def _complete_count(data: dict[str, Any]) -> int:
    return sum(bool(row["complete"]) for row in data["trials"])


def load_exports(
    paths: Iterable[Path], verification_key: bytes
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid, rejected = [], []
    for path in paths:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            data = validate_export(raw, verification_key)
            data["_source_file"] = str(path)
            valid.append(data)
        except (OSError, json.JSONDecodeError, ExportError, KeyError, TypeError) as exc:
            rejected.append(
                {
                    "source_file": str(path),
                    "reason": getattr(exc, "reason", "technical_corrupt"),
                    "detail": str(exc),
                }
            )
    return valid, rejected


def load_attempt_order_manifest(path: Path) -> dict[str, int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    _check(isinstance(raw, dict), "attempt-order manifest must be an object")
    mapping = raw.get("attempt_order")
    _check(
        set(raw) == {"schema_version", "attempt_order"}
        and raw["schema_version"] == "microstudy-attempt-order-v1"
        and isinstance(mapping, dict),
        "invalid attempt-order manifest schema",
    )
    _check(
        all(
            isinstance(attempt_id, str)
            and type(order) is int and order >= 1
            for attempt_id, order in mapping.items()
        ),
        "invalid attempt-order manifest entries",
    )
    _check(len(set(mapping.values())) == len(mapping), "attempt-order values must be unique")
    return mapping


def resolve_duplicates(
    exports: list[dict[str, Any]],
    attempt_order: dict[str, int] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for data in exports:
        groups[data["participant_code"]].append(data)
    kept, excluded = [], []
    for attempts in groups.values():
        run_ids = {row["run_id"] for row in attempts}
        if len(run_ids) > 1:
            if attempt_order is None:
                raise ExportError(
                    "participant appears across run_ids; --attempt-order-manifest is required",
                    "duplicate_order_ambiguous",
                )
            missing = {row["attempt_id"] for row in attempts} - set(attempt_order)
            _check(not missing, f"attempt-order manifest missing attempts: {sorted(missing)}")
            order_key = lambda row: attempt_order[row["attempt_id"]]
        else:
            serials = [row["attempt_serial"] for row in attempts]
            _check(
                len(serials) == len(set(serials)),
                "duplicate attempt_serial within run",
                "duplicate_order_ambiguous",
            )
            order_key = lambda row: row["attempt_serial"]
        complete = [row for row in attempts if row["complete"]]
        if complete:
            winner = min(complete, key=order_key)
        else:
            winner = min(
                attempts, key=lambda row: (-_complete_count(row), order_key(row))
            )
        kept.append(winner)
        excluded.extend(
            {
                "attempt_id": row["attempt_id"],
                "participant_code": row["participant_code"],
                "reason": "duplicate_attempt",
            }
            for row in attempts
            if row is not winner
        )
    return kept, excluded


def apply_assignments(
    exports: list[dict[str, Any]], assignments_path: Path | None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if assignments_path is None:
        return exports, []
    if assignments_path.suffix.lower() == ".json":
        raw = json.loads(assignments_path.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else [
            {"participant_code": code, "sequence": sequence} for code, sequence in raw.items()
        ]
    else:
        with assignments_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    assignments = {row["participant_code"]: row["sequence"] for row in rows}
    excluded = []
    for data in exports:
        if assignments.get(data["participant_code"]) != data["sequence"]:
            excluded.append(
                {
                    "attempt_id": data["attempt_id"],
                    "participant_code": data["participant_code"],
                    "reason": "sequence_mismatch",
                }
            )
    return exports, excluded


def exact_sign_flip(differences: list[float], two_sided: bool = False) -> dict[str, Any]:
    nonzero = [value for value in differences if value != 0]
    ties = len(differences) - len(nonzero)
    if not nonzero:
        return {"n_eff": 0, "ties": ties, "p": 1.0}
    observed = sum(nonzero) / len(nonzero)
    permutations = [
        sum(sign * value for sign, value in zip(signs, nonzero)) / len(nonzero)
        for signs in itertools.product((-1, 1), repeat=len(nonzero))
    ]
    if two_sided:
        count = sum(abs(value) >= abs(observed) for value in permutations)
    else:
        count = sum(value >= observed for value in permutations)
    return {"n_eff": len(nonzero), "ties": ties, "p": count / len(permutations)}


def bootstrap_ci(differences: list[float]) -> list[float | None]:
    if not differences:
        return [None, None]
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(differences)
    samples = sorted(
        sum(rng.choice(differences) for _ in range(n)) / n for _ in range(BOOTSTRAP_B)
    )
    return [samples[math.floor(0.025 * BOOTSTRAP_B)], samples[math.ceil(0.975 * BOOTSTRAP_B) - 1]]


def _mean(values: list[float | int]) -> float | None:
    return statistics.fmean(values) if values else None


def analyze(
    exports: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    assignment_exclusions: list[dict[str, Any]] | None = None,
    *,
    duplicates_resolved: bool = False,
) -> dict[str, Any]:
    if duplicates_resolved:
        kept, duplicate_exclusions = exports, []
    else:
        kept, duplicate_exclusions = resolve_duplicates(exports)
    mechanical_ids = {
        row["attempt_id"] for row in (assignment_exclusions or [])
        if "attempt_id" in row
    }
    participants = []
    differences = []
    sensitivity_differences = []
    descriptive: dict[str, dict[str, list[float | int]]] = {
        condition: defaultdict(list) for condition in ("Contract", "Flat")
    }
    stratified: dict[str, dict[str, list[int]]] = {
        dimension: defaultdict(list)
        for dimension in ("pattern", "block", "sequence", "position")
    }
    for data in kept:
        complete = Counter(row["condition"] for row in data["trials"] if row["complete"])
        eligible = (
            data["attempt_id"] not in mechanical_ids
            and complete["Contract"] >= 4 and complete["Flat"] >= 4
            and sum(complete.values()) >= 8
        )
        scores: dict[str, float | None] = {}
        sensitivity: dict[str, float] = {}
        for condition in ("Contract", "Flat"):
            rows = [row for row in data["trials"] if row["condition"] == condition]
            completed = [row for row in rows if row["complete"]]
            scores[condition] = _mean([int(row["cca_correct"]) for row in completed])
            sensitivity[condition] = statistics.fmean(
                int(bool(row["complete"]) and bool(row["cca_correct"])) for row in rows
            )
            for row in completed:
                descriptive[condition]["q1_accuracy"].append(int(row["q1_correct"]))
                descriptive[condition]["q2_accuracy"].append(int(row["q2_correct"]))
                descriptive[condition]["cca_accuracy"].append(int(row["cca_correct"]))
                descriptive[condition]["rt_q1_ms"].append(row["rt_q1_ms"])
                descriptive[condition]["rt_q2_ms"].append(row["rt_q2_ms"])
                stratified["pattern"][row["pattern"]].append(int(row["cca_correct"]))
                stratified["block"][str(row["block"])].append(int(row["cca_correct"]))
                stratified["sequence"][data["sequence"]].append(int(row["cca_correct"]))
                stratified["position"][str(row["position"])].append(int(row["cca_correct"]))
        difference = (
            scores["Contract"] - scores["Flat"]
            if eligible and scores["Contract"] is not None and scores["Flat"] is not None
            else None
        )
        if difference is not None:
            differences.append(difference)
        sensitivity_difference = sensitivity["Contract"] - sensitivity["Flat"]
        sensitivity_differences.append(sensitivity_difference)
        participants.append(
            {
                "attempt_id": data["attempt_id"],
                "participant_code": data["participant_code"],
                "sequence": data["sequence"],
                "eligible_primary": eligible,
                "mechanical_exclusion": data["attempt_id"] in mechanical_ids,
                "mechanical_exclusion_reason": (
                    "sequence_mismatch" if data["attempt_id"] in mechanical_ids else "none"
                ),
                "complete_contract": complete["Contract"],
                "complete_flat": complete["Flat"],
                "contract_cca": scores["Contract"],
                "flat_cca": scores["Flat"],
                "paired_difference": difference,
                "missing_incorrect_difference": sensitivity_difference,
                "block_1_ease": data["block_1_ease"],
                "block_2_ease": data["block_2_ease"],
                "diagnostic_correct": data["post_task_diagnostic_correct"],
            }
        )
    desc_summary = {
        condition: {metric: _mean(values) for metric, values in metrics.items()}
        for condition, metrics in descriptive.items()
    }
    return {
        "analysis_version": "microstudy-analysis-v1",
        "status": "DRAFT_ANALYSIS_NOT_PAPER_EVIDENCE",
        "bootstrap": {"B": BOOTSTRAP_B, "seed": BOOTSTRAP_SEED},
        "input_attempts": len(exports) + len(rejected),
        "kept_attempts": len(kept),
        "eligible_primary_n": len(differences),
        "rejected": rejected + (assignment_exclusions or []) + duplicate_exclusions,
        "participants": participants,
        "primary": {
            "estimand": "mean participant paired Contract-minus-Flat CCA",
            "mean_difference": _mean(differences),
            "bootstrap_percentile_95_ci": bootstrap_ci(differences),
            "exact_one_sided_sign_flip": exact_sign_flip(differences),
        },
        "missing_as_incorrect_sensitivity": {
            "mean_difference": _mean(sensitivity_differences),
            "exact_two_sided_sign_flip": exact_sign_flip(sensitivity_differences, two_sided=True),
        },
        "descriptive": desc_summary,
        "descriptive_cca_by": {
            dimension: {level: _mean(values) for level, values in levels.items()}
            for dimension, levels in stratified.items()
        },
        "descriptive_ease_counts": {
            "block_1": dict(Counter(str(row["block_1_ease"]) for row in kept)),
            "block_2": dict(Counter(str(row["block_2_ease"]) for row in kept)),
        },
        "descriptive_diagnostic": {
            "submitted": sum(row["post_task_diagnostic_submitted"] for row in kept),
            "correct": sum(row["post_task_diagnostic_correct"] is True for row in kept),
        },
    }


def write_summary(summary: dict[str, Any], json_path: Path, csv_path: Path) -> None:
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = [
        "attempt_id", "participant_code", "sequence", "eligible_primary",
        "mechanical_exclusion", "mechanical_exclusion_reason",
        "complete_contract", "complete_flat", "contract_cca", "flat_cca",
        "paired_difference", "missing_incorrect_difference", "block_1_ease",
        "block_2_ease", "diagnostic_correct",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary["participants"])


def simulate_mde(n: int, simulations: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    grid = [round(value / 100, 2) for value in range(1, 51)]
    power = {}
    for effect in grid:
        rejections = 0
        for _ in range(simulations):
            differences = [
                max(-1.0, min(1.0, rng.gauss(effect, 0.5))) for _ in range(n)
            ]
            nonzero = [value for value in differences if value != 0]
            positive = sum(value > 0 for value in nonzero)
            sign_p = sum(
                math.comb(len(nonzero), k) * 0.5 ** len(nonzero)
                for k in range(positive, len(nonzero) + 1)
            )
            if sign_p <= 0.05:
                rejections += 1
        power[str(effect)] = rejections / simulations
    mde = next((float(effect) for effect, value in power.items() if value >= 0.8), None)
    return {
        "status": "DRAFT_ASSUMPTION_SENSITIVITY_NOT_PAPER_EVIDENCE",
        "assumptions": {
            "paired_difference_distribution": "clipped Normal(effect, 0.5)",
            "alpha": 0.05,
            "one_sided": True,
            "test_for_simulation": "exact positive-sign binomial sensitivity only; not the primary sign-flip test",
            "n": n,
            "simulations": simulations,
            "seed": seed,
        },
        "estimated_mde_80_percent_power": mde,
        "primary_mde_status": "UNVERIFIED_NOT_ESTIMATED",
        "power_by_effect": power,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    analyze_parser = sub.add_parser("analyze")
    analyze_parser.add_argument("exports", nargs="+", type=Path)
    analyze_parser.add_argument("--json-out", type=Path, default=Path("microstudy-summary.json"))
    analyze_parser.add_argument("--csv-out", type=Path, default=Path("microstudy-participants.csv"))
    analyze_parser.add_argument(
        "--assignments",
        type=Path,
        help="Frozen owner assignment JSON or CSV with participant_code and sequence.",
    )
    analyze_parser.add_argument(
        "--verification-key-file", type=Path, required=True,
        help="Owner-held HMAC verification key generated by the study server.",
    )
    analyze_parser.add_argument(
        "--attempt-order-manifest", type=Path,
        help=(
            "Required when one participant_code appears across server run_ids. "
            "JSON schema: {schema_version: microstudy-attempt-order-v1, "
            "attempt_order: {attempt_id: global_order}}."
        ),
    )
    mde_parser = sub.add_parser("mde")
    mde_parser.add_argument("--n", type=int, required=True)
    mde_parser.add_argument("--simulations", type=int, default=10_000)
    mde_parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    mde_parser.add_argument("--json-out", type=Path, default=Path("microstudy-mde-DRAFT.json"))
    args = parser.parse_args(argv)
    if args.command == "analyze":
        key = args.verification_key_file.read_bytes()
        valid, rejected = load_exports(args.exports, key)
        attempt_order = (
            load_attempt_order_manifest(args.attempt_order_manifest)
            if args.attempt_order_manifest else None
        )
        valid, duplicate_exclusions = resolve_duplicates(valid, attempt_order)
        valid, assignment_exclusions = apply_assignments(valid, args.assignments)
        summary = analyze(
            valid, rejected + duplicate_exclusions, assignment_exclusions,
            duplicates_resolved=True,
        )
        write_summary(summary, args.json_out, args.csv_out)
    else:
        args.json_out.write_text(
            json.dumps(simulate_mde(args.n, args.simulations, args.seed), indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
