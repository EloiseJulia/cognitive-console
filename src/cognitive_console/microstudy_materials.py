"""V9 scenario micro-study generation and fail-closed validation."""

from __future__ import annotations

import hashlib
import itertools
import json
import re
import subprocess
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "microstudy_scenario_v9"
SOURCE_REGISTRY_PATH = DATA_DIR / "source_registry.json"
MATERIALS_PATH = DATA_DIR / "materials.json"
SEQUENCES_PATH = DATA_DIR / "sequences.json"

MATERIAL_SCHEMA_VERSION = "microstudy-scenario-v9-bilingual"
MATERIALS_VERSION = "microstudy-scenario-release-20260811-v9-draft"
SEQUENCE_SCHEMA_VERSION = "microstudy-scenario-sequences-v2-exact-cover"
EXPORT_SCHEMA_VERSION = "microstudy-export-v5-scenario-bilingual-signed"
LOCALES = ("en", "zh-Hans")
TICKET_CODES = (
    "UNC-R",
    "UNC-S",
    "SKEP-R",
    "SKEP-S",
    "DELIB-R",
    "DELIB-S",
)
SCENARIO_PAIRS = (
    ("UNC-R", "UNC-S"),
    ("SKEP-R", "SKEP-S"),
    ("DELIB-R", "DELIB-S"),
)
Q1_CODE_BY_STATE = {"U": "A", "D": "B", "W": "C", "S": "D"}
Q2_ISSUE_ORDER = (
    "Q2_COMPARATOR_MISSINGNESS",
    "Q2_SCOPE_BOUNDARY",
    "Q2_UNDERPOWERED_COMPARISON",
    "Q2_MISSING_PAIRED_COMPARISON",
    "Q2_DECISIVE_PAIRED_TEST",
    "Q2_QUALITY_COHERENCE_FAIL",
)
Q2_CODE_BY_ISSUE = {
    issue: chr(ord("A") + index) for index, issue in enumerate(Q2_ISSUE_ORDER)
}
TICKET_STATE_BY_CODE = {
    "UNC-R": "W",
    "UNC-S": "S",
    "SKEP-R": "U",
    "SKEP-S": "D",
    "DELIB-R": "U",
    "DELIB-S": "W",
}


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def load_source_registry(path: Path = SOURCE_REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_bytes(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"canonical Git blob unavailable: {commit}:{path}: {detail}")
    return completed.stdout


def verified_source_payloads(
    registry_path: Path = SOURCE_REGISTRY_PATH,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    registry = load_source_registry(registry_path)
    if registry != {
        "schema_version": registry.get("schema_version"),
        "hash_basis": registry.get("hash_basis"),
        "sources": registry.get("sources"),
    }:
        raise ValueError("source registry has unknown fields")
    if registry["schema_version"] != "microstudy-v9-source-registry-v1":
        raise ValueError("wrong source registry schema")
    if registry["hash_basis"] != "git_blob_bytes":
        raise ValueError("source registry must use git_blob_bytes")
    payloads: dict[str, Any] = {}
    lineage: list[dict[str, str]] = []
    seen: set[str] = set()
    for source in registry["sources"]:
        required = {
            "source_id", "commit", "path", "canonical_sha256", "format"
        }
        if not isinstance(source, dict) or set(source) != required:
            raise ValueError("invalid source registry row")
        source_id = source["source_id"]
        if source_id in seen:
            raise ValueError(f"duplicate source_id: {source_id}")
        seen.add(source_id)
        blob = _git_blob_bytes(source["commit"], source["path"])
        digest = hashlib.sha256(blob).hexdigest()
        if digest != source["canonical_sha256"]:
            raise ValueError(
                f"canonical Git blob hash mismatch for {source_id}: "
                f"expected {source['canonical_sha256']}, got {digest}"
            )
        if source["format"] == "json":
            payloads[source_id] = json.loads(blob.decode("utf-8"))
        elif source["format"] == "markdown":
            payloads[source_id] = blob.decode("utf-8")
        else:
            raise ValueError(f"unsupported source format: {source['format']}")
        lineage.append(
            {
                "source_id": source_id,
                "commit": source["commit"],
                "path": source["path"],
                "canonical_sha256": digest,
                "hash_basis": "git_blob_bytes",
            }
        )
    required_ids = {
        "C1_QWEN", "C1_LLAMA", "E0006_ARM", "E0011_MULTI",
        "E0013_FORMAT", "E0014_ENDPOINT", "E0015_SCALE",
        "E0006_CAA_QWEN", "E0006_CAA_LLAMA",
        "E0006_ITI_QWEN", "E0006_ITI_LLAMA", "E0006_PREREG",
        "POSTHOC_E0006",
    }
    if seen != required_ids:
        raise ValueError(f"source registry IDs drifted: {sorted(seen)}")
    return payloads, lineage


def _axis_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload["axes"]
    if isinstance(rows, dict):
        return rows
    return {row["axis"]: row for row in rows}


def _fmt(value: float, digits: int = 3, *, signed: bool = False) -> str:
    return f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"


def _mean(values: Iterable[float]) -> float:
    rows = list(values)
    return sum(rows) / len(rows)


def extract_real_evidence(payloads: dict[str, Any]) -> dict[str, Any]:
    qwen = _axis_map(payloads["C1_QWEN"])
    llama = _axis_map(payloads["C1_LLAMA"])
    for axis in ("deliberation", "skepticism"):
        if qwen[axis]["facade_ratio_ci_hi"] >= 1 or llama[axis]["facade_ratio_ci_hi"] >= 1:
            raise ValueError(f"READ heterogeneity premise failed for {axis}")
    if not (
        qwen["uncertainty_awareness"]["facade_ratio_ci_hi"] < 1
        and llama["uncertainty_awareness"]["facade_ratio_ci_hi"] >= 1
        and qwen["focus"]["facade_ratio_ci_lo"] > 1
        and llama["focus"]["facade_ratio_ci_hi"] < 1
    ):
        raise ValueError("C1 Qwen/Llama heterogeneity no longer matches audited artifacts")

    arm = payloads["E0006_ARM"]
    if not (
        arm["n_cells"] == 4
        and arm["zero_pass_cells"] == 4
        and arm["any_cell_has_pass"] is False
        and all(
            cell["axes_passed"] == 0
            and not any(cell["axis_passes"].values())
            for cell in arm["cells"]
        )
    ):
        raise ValueError("E-0006 is not the audited four-cell no-pass artifact")
    raw_cells = {
        ("caa", "qwen2.5-7b-instruct"): payloads["E0006_CAA_QWEN"],
        ("caa", "meta-llama-3-8b-instruct"): payloads["E0006_CAA_LLAMA"],
        ("iti", "qwen2.5-7b-instruct"): payloads["E0006_ITI_QWEN"],
        ("iti", "meta-llama-3-8b-instruct"): payloads["E0006_ITI_LLAMA"],
    }
    for (method, model), cell in raw_cells.items():
        normalized_model = cell["model"].rsplit("/", 1)[-1].lower()
        if not (
            cell["steering_method"] == method
            and normalized_model == model
            and not any(cell["axis_passes"].values())
            and all(axis["passed"] is False for axis in cell["axes"])
        ):
            raise ValueError(f"E-0006 cell no-pass premise failed for {method}/{model}")

    multiseed = payloads["E0011_MULTI"]
    aggregation = multiseed["aggregation"]
    if not (
        aggregation["n_seeds"] == 5
        and aggregation["n_seeds_non_transfer_generalized"] == 5
        and aggregation["has_any_true_pass"] is False
        and aggregation["caveat_drop_rule"]["outcome"] == "DROP_SINGLE_SEED_CAVEAT"
    ):
        raise ValueError("E-0011 split robustness no longer matches audited status")

    prereg = payloads["E0006_PREREG"]
    token_match = re.search(r"max_new_tokens\s*=\s*([0-9]+)", prereg)
    if token_match is None:
        raise ValueError("generation token cap is absent from the evidence ledger")
    token_cap = int(token_match.group(1))

    format_recheck = payloads["E0013_FORMAT"]["test_split_only"]["caa__qwen2.5-7b"]
    conditions = format_recheck["conditions"]
    compliant = format_recheck["format_compliant_only_delta_steer_minus_prompt"]
    missingness = format_recheck["sensitivity"]["worst_case_imputation_bounds"]["bounds"]
    compliance_delta = (
        conditions["steer"]["format_compliance_rate"]
        - conditions["baseline"]["format_compliance_rate"]
    )
    brier_delta = (
        conditions["steer"]["mean_frozen_imputed_1minus_brier"]
        - conditions["baseline"]["mean_frozen_imputed_1minus_brier"]
    )
    if not (
        compliant["ci_hi"] < 0
        and min(row["delta"] for row in missingness) < 0
        and max(row["delta"] for row in missingness) > 0
    ):
        raise ValueError("E-0013 missingness caveat no longer holds")

    endpoint = payloads["E0014_ENDPOINT"]
    endpoint_pc3 = endpoint["pc3_steer_vs_best_of_n_prompt"]
    endpoint_prompt = _mean(endpoint_pc3["per_item_prompt"])
    endpoint_steer = _mean(endpoint_pc3["per_item_steer"])
    if endpoint_pc3["passed"] or endpoint_steer != 0:
        raise ValueError("E-0014 must not generate a positive latent pass")

    scale = payloads["E0015_SCALE"]
    coherent_max_ratios: list[float] = []
    for axis_name, axis_result in scale["axes"].items():
        for comparison_name in (
            "pc2a_steer_vs_neutral_baseline",
            "pc3_steer_vs_dev_selected_best_of_16_prompt",
        ):
            if axis_result[comparison_name]["passed"]:
                raise ValueError("E-0015 must not generate a positive latent pass")
        scale_rows = scale["direction_provenance"][axis_name]["scale_rows"]
        by_beta = {
            float(row["beta"]): row
            for row in axis_result["pc3_steer_vs_dev_selected_best_of_16_prompt"][
                "dev_selection"
            ]["alpha_grid"]
        }
        coherent_max_ratios.append(
            max(
                row["alpha_eff_over_mean_residual_l2"]
                for row in scale_rows
                if by_beta[float(row["beta"])]["coherence_ok"]
            )
        )
    refusal_rows = scale["direction_provenance"]["refusal_positive_control"]["scale_rows"]
    degenerate_ratio = max(
        row["alpha_eff_over_mean_residual_l2"] for row in refusal_rows
    )
    scale_mde = scale["axes"]["refusal_positive_control"][
        "pc3_steer_vs_dev_selected_best_of_16_prompt"
    ]["mde"]["minimum_detectable_effect"]

    posthoc = payloads["POSTHOC_E0006"]
    skepticism_mdes: list[float] = []
    deliberation: list[dict[str, Any]] = []
    for cell in posthoc["cells"]:
        axes = {axis["axis"]: axis for axis in cell["axes"]}
        skepticism_mdes.append(
            axes["skepticism"]["mde"]["mde_superiority_80pct_power"]
        )
        deliberation.append(
            {
                "method": cell["method"],
                "model": cell["model"],
                "point": axes["deliberation"]["prereg_mean_diff"],
                "ci_low": axes["deliberation"]["prereg_ci_lo"],
                "ci_high": axes["deliberation"]["prereg_ci_hi"],
                "posthoc_verdict": axes["deliberation"]["tost_verdict"],
                "mde": axes["deliberation"]["mde"]["mde_superiority_80pct_power"],
            }
        )
    if not all(value > posthoc["sesoi"] for value in skepticism_mdes):
        raise ValueError("skepticism comparison is no longer underpowered vs SESOI")
    if not all(
        row["posthoc_verdict"] == "UNDERPOWERED"
        for row in deliberation if row["method"] == "caa"
    ):
        raise ValueError("CAA deliberation underpower caveat drifted")

    return {
        "read": {
            "qwen": {
                axis: qwen[axis]["facade_ratio"]
                for axis in ("deliberation", "skepticism", "uncertainty_awareness", "focus")
            },
            "llama": {
                axis: llama[axis]["facade_ratio"]
                for axis in ("deliberation", "skepticism", "uncertainty_awareness", "focus")
            },
        },
        "arm": {
            "n_cells": arm["n_cells"],
            "zero_pass_cells": arm["zero_pass_cells"],
        },
        "multiseed": {"n_seeds": aggregation["n_seeds"], "same_pool": True},
        "format": {
            "steer_compliance": conditions["steer"]["format_compliance_rate"],
            "prompt_compliance": conditions["prompt"]["format_compliance_rate"],
            "baseline_compliance": conditions["baseline"]["format_compliance_rate"],
            "compliance_delta_vs_baseline": compliance_delta,
            "brier_delta_vs_baseline": brier_delta,
            "complete_case_point": compliant["point"],
            "complete_case_ci_low": compliant["ci_lo"],
            "complete_case_ci_high": compliant["ci_hi"],
            "missingness_low": min(row["delta"] for row in missingness),
            "missingness_high": max(row["delta"] for row in missingness),
            "other_cells_rechecked": 0,
            "other_cells_unrechecked": 3,
        },
        "endpoint": {
            "prompt_refusal": endpoint_prompt,
            "unit_caa_refusal": endpoint_steer,
        },
        "scale": {
            "coherent_ratio_low": min(coherent_max_ratios),
            "coherent_ratio_high": max(coherent_max_ratios),
            "degenerate_ratio": degenerate_ratio,
            "mde": scale_mde,
            "any_latent_pass": False,
        },
        "skepticism": {
            "mdes": skepticism_mdes,
            "sesoi": posthoc["sesoi"],
            "same_pool": True,
        },
        "deliberation": {
            "cells": deliberation,
            "token_cap": token_cap,
        },
    }


def derive_policy_state(policy_inputs: dict[str, Any]) -> str:
    required = {
        "read_status", "paired_comparison", "quality_status", "scope_status"
    }
    if set(policy_inputs) != required:
        raise ValueError("invalid policy input fields")
    read_status = policy_inputs["read_status"]
    comparison = policy_inputs["paired_comparison"]
    quality = policy_inputs["quality_status"]
    scope = policy_inputs["scope_status"]
    if read_status not in {"usable", "missing"}:
        raise ValueError("invalid read status")
    if comparison not in {
        "missing", "underpowered", "mixed", "decisive_negative", "decisive_positive"
    }:
        raise ValueError("invalid comparison status")
    if quality not in {"pass", "fail", "unverified"}:
        raise ValueError("invalid quality status")
    if scope not in {"exact", "bounded", "missing"}:
        raise ValueError("invalid scope status")
    if quality == "fail" or comparison == "decisive_negative":
        return "W"
    if comparison == "decisive_positive" and quality == "pass" and scope == "exact":
        return "S"
    if read_status == "usable" and comparison == "missing":
        return "D"
    return "U"


def derive_ticket_keys(ticket: dict[str, Any]) -> dict[str, str]:
    state = derive_policy_state(ticket["policy_inputs"])
    issue = ticket["decisive_issue"]
    if issue not in Q2_CODE_BY_ISSUE:
        raise ValueError("unknown decisive issue")
    return {
        "state": state,
        "q1_code": Q1_CODE_BY_STATE[state],
        "q2_issue": issue,
        "q2_code": Q2_CODE_BY_ISSUE[issue],
    }


def _source_details(
    lineage: list[dict[str, str]], source_ids: Iterable[str]
) -> list[dict[str, str]]:
    wanted = set(source_ids)
    rows = [row for row in lineage if row["source_id"] in wanted]
    if {row["source_id"] for row in rows} != wanted:
        raise ValueError("ticket references an unknown source")
    return rows


def _real_fact_copy(e: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    q = e["read"]["qwen"]
    l = e["read"]["llama"]
    f = e["format"]
    endpoint = e["endpoint"]
    scale = e["scale"]
    skep_mdes = e["skepticism"]["mdes"]
    delib = e["deliberation"]["cells"]
    caa_delib = [row for row in delib if row["method"] == "caa"]
    iti_delib = [row for row in delib if row["method"] == "iti"]
    return {
        "UNC-R": {
            "en": [
                (
                    "READ is heterogeneous across models: Qwen/Llama facade ratios "
                    f"are {_fmt(q['uncertainty_awareness'])}/{_fmt(l['uncertainty_awareness'])} "
                    "for uncertainty and "
                    f"{_fmt(q['focus'])}/{_fmt(l['focus'])} for focus; "
                    "deliberation and skepticism show the gap in both."
                ),
                (
                    f"Across {e['arm']['n_cells']} CAA/ITI × Qwen/Llama cells, "
                    f"{e['arm']['zero_pass_cells']} had no passing axis against the "
                    "bounded best-prompt comparison."
                ),
                (
                    "For Qwen CAA uncertainty, steering was approximately baseline: "
                    f"{_fmt(f['compliance_delta_vs_baseline'], signed=True)} format "
                    "compliance and "
                    f"{_fmt(f['brier_delta_vs_baseline'], 4, signed=True)} in 1−Brier."
                ),
                (
                    "The E-0013 format-compliant complete-case paired estimate was "
                    f"{_fmt(f['complete_case_point'], signed=True)} with 95% CI "
                    f"[{_fmt(f['complete_case_ci_low'], signed=True)}, "
                    f"{_fmt(f['complete_case_ci_high'], signed=True)}], but "
                    "adversarial missingness bounds cross zero and span "
                    f"[{_fmt(f['missingness_low'], signed=True)}, "
                    f"{_fmt(f['missingness_high'], signed=True)}]."
                ),
                (
                    f"Prompt refusal was {_fmt(endpoint['prompt_refusal'])}, while "
                    f"unit-direction CAA refusal was {_fmt(endpoint['unit_caa_refusal'])}; "
                    "scale-corrected latent arms still had no pass. Coherent perturbations "
                    f"reached about {_fmt(scale['coherent_ratio_low'], 2)}–"
                    f"{_fmt(scale['coherent_ratio_high'], 2)}× residual norm; "
                    f"about {_fmt(scale['degenerate_ratio'], 2)}× was degenerate and "
                    f"MDE was about {_fmt(scale['mde'], 2)}."
                ),
                (
                    f"The E-0013 recheck covers only Qwen CAA; the other "
                    f"{f['other_cells_unrechecked']} cells are unrechecked. "
                    "Illustrative outputs and missingness do not make this knob adjustable."
                ),
            ],
            "zh-Hans": [
                (
                    "不同模型的 READ 结果存在异质性：Qwen/Llama 在不确定性上的表征比为 "
                    f"{_fmt(q['uncertainty_awareness'])}/{_fmt(l['uncertainty_awareness'])}，"
                    "在聚焦上的表征比为 "
                    f"{_fmt(q['focus'])}/{_fmt(l['focus'])}；审慎思考和怀疑性在两个模型中"
                    "都显示出差距。"
                ),
                (
                    f"在 {e['arm']['n_cells']} 个 CAA/ITI × Qwen/Llama 单元中，"
                    f"{e['arm']['zero_pass_cells']} 个单元相对有界最优提示都没有任何轴通过。"
                ),
                (
                    "对于 Qwen CAA 不确定性，steering 与 baseline 基本相当："
                    f"格式合规率差 {_fmt(f['compliance_delta_vs_baseline'], signed=True)}，"
                    f"1−Brier 差 {_fmt(f['brier_delta_vs_baseline'], 4, signed=True)}。"
                ),
                (
                    "E-0013 仅看格式合规完整案例配对时，估计值为 "
                    f"{_fmt(f['complete_case_point'], signed=True)}，95% CI 为 "
                    f"[{_fmt(f['complete_case_ci_low'], signed=True)}, "
                    f"{_fmt(f['complete_case_ci_high'], signed=True)}]；但对缺失值作对抗性处理后"
                    "边界跨过零，范围为 "
                    f"[{_fmt(f['missingness_low'], signed=True)}, "
                    f"{_fmt(f['missingness_high'], signed=True)}]。"
                ),
                (
                    f"直接提示的拒答率为 {_fmt(endpoint['prompt_refusal'])}，单位方向 CAA 的"
                    f"拒答率为 {_fmt(endpoint['unit_caa_refusal'])}；按原始幅度校正后仍没有"
                    "潜在干预通过。保持连贯的扰动约为残差范数的 "
                    f"{_fmt(scale['coherent_ratio_low'], 2)}–"
                    f"{_fmt(scale['coherent_ratio_high'], 2)} 倍；约 "
                    f"{_fmt(scale['degenerate_ratio'], 2)} 倍时退化，MDE 约为 "
                    f"{_fmt(scale['mde'], 2)}。"
                ),
                (
                    f"E-0013 只复查了 Qwen CAA；其余 {f['other_cells_unrechecked']} 个单元"
                    "尚未复查。示意输出和缺失值分析都不能让该旋钮变成可调。"
                ),
            ],
        },
        "SKEP-R": {
            "en": [
                (
                    "READ is available for skepticism in both models: facade ratios are "
                    f"{_fmt(q['skepticism'])} for Qwen and {_fmt(l['skepticism'])} for Llama."
                ),
                (
                    f"All {e['arm']['n_cells']} steering cells failed the preregistered "
                    "superiority rule against the bounded prompt."
                ),
                (
                    f"The four skepticism comparisons are underpowered: their MDEs are "
                    f"{'/'.join(_fmt(value, 3) for value in skep_mdes)}, all above the "
                    f"{_fmt(e['skepticism']['sesoi'], 2)} target effect."
                ),
                (
                    "The uncertainty negative is robust across split seeds, but those "
                    f"{e['multiseed']['n_seeds']} seeds reuse the same item pool."
                ),
                (
                    "A non-detection with these MDEs is not evidence that meaningful "
                    "skepticism effects are absent."
                ),
                (
                    "This release judgment is limited to the tested Qwen/Llama, CAA/ITI, "
                    "bounded-prompt setup."
                ),
            ],
            "zh-Hans": [
                (
                    "两个模型的怀疑性 READ 都可用：Qwen 的表征比为 "
                    f"{_fmt(q['skepticism'])}，Llama 为 {_fmt(l['skepticism'])}。"
                ),
                (
                    f"全部 {e['arm']['n_cells']} 个 steering 单元相对有界提示都未通过"
                    "预先登记的优越性规则。"
                ),
                (
                    "四个怀疑性比较检验力不足：其 MDE 为 "
                    f"{'/'.join(_fmt(value, 3) for value in skep_mdes)}，均高于 "
                    f"{_fmt(e['skepticism']['sesoi'], 2)} 的目标效应。"
                ),
                (
                    f"不确定性负结果跨 {e['multiseed']['n_seeds']} 个划分种子保持一致，"
                    "但这些种子复用了同一项目池。"
                ),
                (
                    "在这些 MDE 下未检出差异，不能证明有意义的怀疑性效应不存在。"
                ),
                (
                    "该发布判断仅适用于已测试的 Qwen/Llama、CAA/ITI 与有界提示设置。"
                ),
            ],
        },
        "DELIB-R": {
            "en": [
                (
                    "READ is available for deliberation in both models: facade ratios are "
                    f"{_fmt(q['deliberation'])} for Qwen and {_fmt(l['deliberation'])} for Llama."
                ),
                (
                    "The four deliberation cells are mixed near zero: "
                    + "; ".join(
                        f"{row['method'].upper()} {row['model']} "
                        f"{_fmt(row['point'], signed=True)} "
                        f"[{_fmt(row['ci_low'], signed=True)}, "
                        f"{_fmt(row['ci_high'], signed=True)}]"
                        for row in delib
                    )
                    + "."
                ),
                (
                    "Both CAA deliberation comparisons are underpowered in the post-hoc "
                    "characterization."
                ),
                (
                    "ITI equivalence labels are post-hoc only; they were not the "
                    "preregistered superiority decision."
                ),
                (
                    f"Generation used a {e['deliberation']['token_cap']}-token cap, so "
                    "longer deliberative behavior was not tested."
                ),
                (
                    "A decisive paired test under a release-relevant response budget is "
                    "still required for this knob."
                ),
            ],
            "zh-Hans": [
                (
                    "两个模型的审慎思考 READ 都可用：Qwen 的表征比为 "
                    f"{_fmt(q['deliberation'])}，Llama 为 {_fmt(l['deliberation'])}。"
                ),
                (
                    "四个审慎思考单元在零附近呈混合结果："
                    + "；".join(
                        f"{row['method'].upper()} {row['model']} "
                        f"{_fmt(row['point'], signed=True)} "
                        f"[{_fmt(row['ci_low'], signed=True)}, "
                        f"{_fmt(row['ci_high'], signed=True)}]"
                        for row in delib
                    )
                    + "。"
                ),
                (
                    "事后刻画显示，两个 CAA 审慎思考比较都检验力不足。"
                ),
                (
                    "ITI 的等效标签仅来自事后分析，并不是预先登记的优越性判定。"
                ),
                (
                    f"生成上限为 {e['deliberation']['token_cap']} 个 token，因此没有测试"
                    "更长的审慎思考行为。"
                ),
                (
                    "该旋钮仍需要在符合发布场景的响应预算下完成有判定力的配对检验。"
                ),
            ],
        },
    }


def _ticket_definitions(
    evidence: dict[str, Any], lineage: list[dict[str, str]]
) -> list[dict[str, Any]]:
    real = _real_fact_copy(evidence)
    definitions = [
        {
            "ticket_code": "UNC-R",
            "source_kind": "SOURCE-BACKED",
            "policy_inputs": {
                "read_status": "usable",
                "paired_comparison": "decisive_negative",
                "quality_status": "unverified",
                "scope_status": "bounded",
            },
            "decisive_issue": "Q2_COMPARATOR_MISSINGNESS",
            "source_ids": (
                "C1_QWEN", "C1_LLAMA", "E0006_ARM", "E0013_FORMAT",
                "E0006_CAA_QWEN", "E0006_CAA_LLAMA",
                "E0006_ITI_QWEN", "E0006_ITI_LLAMA",
                "E0014_ENDPOINT", "E0015_SCALE",
            ),
            "facts": real["UNC-R"],
            "display": {
                "en": {
                    "title": "Uncertainty-awareness knob release",
                    "context": "Review whether the next product release should expose an uncertainty-awareness knob.",
                    "knob": "Uncertainty-awareness prototype",
                    "outputs": [
                        "Candidate: “I may be missing context; confidence is moderate.”",
                        "Reference: “The available record supports the following answer.”",
                    ],
                },
                "zh-Hans": {
                    "title": "不确定性感知旋钮发布单",
                    "context": "审核下一版产品是否应向用户提供不确定性感知旋钮。",
                    "knob": "不确定性感知原型",
                    "outputs": [
                        "候选输出：“我可能缺少部分背景；置信度中等。”",
                        "参照输出：“现有记录支持以下回答。”",
                    ],
                },
            },
        },
        {
            "ticket_code": "UNC-S",
            "source_kind": "SIMULATED",
            "policy_inputs": {
                "read_status": "usable",
                "paired_comparison": "decisive_positive",
                "quality_status": "pass",
                "scope_status": "exact",
            },
            "decisive_issue": "Q2_SCOPE_BOUNDARY",
            "source_ids": (),
            "facts": {
                "en": [
                    "A completed readout names the uncertainty-awareness behavior.",
                    "A matched comparison beats the existing preset in the stated workflow.",
                    "The comparator uses the same task, response budget, and scoring rule.",
                    "Speech/text quality and coherence checks pass.",
                    "The evidence does not cover other models, tasks, or response budgets.",
                    "Adjustment is supported only for the named support-triage workflow and preset range.",
                ],
                "zh-Hans": [
                    "已完成的读出明确对应不确定性感知行为。",
                    "在所述工作流中，匹配比较优于现有预设。",
                    "比较器使用相同任务、响应预算和评分规则。",
                    "语音/文本质量与连贯性检查均通过。",
                    "证据不覆盖其他模型、任务或响应预算。",
                    "仅支持在已命名的支持分诊工作流和预设范围内调节。",
                ],
            },
            "display": {
                "en": {
                    "title": "Simulated scoped uncertainty knob",
                    "context": "A synthetic release case with support limited to one named workflow.",
                    "knob": "Uncertainty-awareness prototype",
                    "outputs": [
                        "Candidate: “Confidence is limited because one record is missing.”",
                        "Reference: “The answer is provided without a confidence note.”",
                    ],
                },
                "zh-Hans": {
                    "title": "模拟的限定范围不确定性旋钮",
                    "context": "一个仅在单一命名工作流中获得支持的合成发布案例。",
                    "knob": "不确定性感知原型",
                    "outputs": [
                        "候选输出：“由于缺少一条记录，置信度有限。”",
                        "参照输出：“给出答案，但不附置信度说明。”",
                    ],
                },
            },
        },
        {
            "ticket_code": "SKEP-R",
            "source_kind": "SOURCE-BACKED",
            "policy_inputs": {
                "read_status": "usable",
                "paired_comparison": "underpowered",
                "quality_status": "pass",
                "scope_status": "bounded",
            },
            "decisive_issue": "Q2_UNDERPOWERED_COMPARISON",
            "source_ids": (
                "C1_QWEN", "C1_LLAMA", "E0006_ARM", "E0011_MULTI",
                "E0006_CAA_QWEN", "E0006_CAA_LLAMA",
                "E0006_ITI_QWEN", "E0006_ITI_LLAMA", "POSTHOC_E0006",
            ),
            "facts": real["SKEP-R"],
            "display": {
                "en": {
                    "title": "Skepticism knob release",
                    "context": "Review whether the next product release should expose a skepticism knob.",
                    "knob": "Skepticism prototype",
                    "outputs": [
                        "Candidate: “This claim needs a source check before acceptance.”",
                        "Reference: “The claim is accepted as written.”",
                    ],
                },
                "zh-Hans": {
                    "title": "怀疑性旋钮发布单",
                    "context": "审核下一版产品是否应向用户提供怀疑性旋钮。",
                    "knob": "怀疑性原型",
                    "outputs": [
                        "候选输出：“接受该主张前需要核查来源。”",
                        "参照输出：“按原文接受该主张。”",
                    ],
                },
            },
        },
        {
            "ticket_code": "SKEP-S",
            "source_kind": "SIMULATED",
            "policy_inputs": {
                "read_status": "usable",
                "paired_comparison": "missing",
                "quality_status": "unverified",
                "scope_status": "bounded",
            },
            "decisive_issue": "Q2_MISSING_PAIRED_COMPARISON",
            "source_ids": (),
            "facts": {
                "en": [
                    "A completed readout names a skepticism-related behavior.",
                    "The prototype changes diagnostic examples.",
                    "No matched comparison against the existing preset has been run.",
                    "A quality failure has not been observed, but quality is not release evidence here.",
                    "The diagnostic uses one fixed support workflow.",
                    "The record supports read-only diagnosis, not a user adjustment.",
                ],
                "zh-Hans": [
                    "已完成的读出明确对应一种怀疑性相关行为。",
                    "原型会改变诊断示例。",
                    "尚未完成与现有预设的匹配比较。",
                    "目前未观察到质量失败，但质量本身不能构成这里的发布证据。",
                    "诊断仅使用一个固定的支持工作流。",
                    "该记录支持只读诊断，不支持用户调节。",
                ],
            },
            "display": {
                "en": {
                    "title": "Simulated diagnostic skepticism knob",
                    "context": "A synthetic case with a usable diagnostic but no paired release comparison.",
                    "knob": "Skepticism prototype",
                    "outputs": [
                        "Candidate: “The cited evidence should be checked.”",
                        "Reference: “The cited evidence is accepted.”",
                    ],
                },
                "zh-Hans": {
                    "title": "模拟的诊断型怀疑性旋钮",
                    "context": "一个已有可用诊断但缺少发布配对比较的合成案例。",
                    "knob": "怀疑性原型",
                    "outputs": [
                        "候选输出：“应核查所引用的证据。”",
                        "参照输出：“接受所引用的证据。”",
                    ],
                },
            },
        },
        {
            "ticket_code": "DELIB-R",
            "source_kind": "SOURCE-BACKED",
            "policy_inputs": {
                "read_status": "usable",
                "paired_comparison": "mixed",
                "quality_status": "unverified",
                "scope_status": "bounded",
            },
            "decisive_issue": "Q2_DECISIVE_PAIRED_TEST",
            "source_ids": (
                "C1_QWEN", "C1_LLAMA", "E0006_ARM",
                "E0006_CAA_QWEN", "E0006_CAA_LLAMA",
                "E0006_ITI_QWEN", "E0006_ITI_LLAMA",
                "POSTHOC_E0006", "E0006_PREREG",
            ),
            "facts": real["DELIB-R"],
            "display": {
                "en": {
                    "title": "Deliberation knob release",
                    "context": "Review whether the next product release should expose a deliberation knob.",
                    "knob": "Deliberation prototype",
                    "outputs": [
                        "Candidate: “First, map the constraints; then compare two solutions.”",
                        "Reference: “Use the first feasible solution.”",
                    ],
                },
                "zh-Hans": {
                    "title": "审慎思考旋钮发布单",
                    "context": "审核下一版产品是否应向用户提供审慎思考旋钮。",
                    "knob": "审慎思考原型",
                    "outputs": [
                        "候选输出：“先梳理约束，再比较两个方案。”",
                        "参照输出：“采用第一个可行方案。”",
                    ],
                },
            },
        },
        {
            "ticket_code": "DELIB-S",
            "source_kind": "SIMULATED",
            "policy_inputs": {
                "read_status": "usable",
                "paired_comparison": "decisive_positive",
                "quality_status": "fail",
                "scope_status": "exact",
            },
            "decisive_issue": "Q2_QUALITY_COHERENCE_FAIL",
            "source_ids": (),
            "facts": {
                "en": [
                    "A completed readout names a deliberation-related behavior.",
                    "A matched comparison improves the task score over the existing preset.",
                    "The comparator uses the same workflow and response budget.",
                    "The candidate repeats phrases and loses speech/text coherence.",
                    "The registered quality gate fails.",
                    "The result applies only to the named planning workflow, where the failed quality gate blocks release.",
                ],
                "zh-Hans": [
                    "已完成的读出明确对应一种审慎思考相关行为。",
                    "匹配比较中的任务得分优于现有预设。",
                    "比较器使用相同工作流和响应预算。",
                    "候选输出出现重复措辞，并失去语音/文本连贯性。",
                    "预先登记的质量门未通过。",
                    "结果仅适用于已命名的规划工作流；失败的质量门阻止发布。",
                ],
            },
            "display": {
                "en": {
                    "title": "Simulated incoherent deliberation knob",
                    "context": "A synthetic case with a task gain but a failed quality/coherence gate.",
                    "knob": "Deliberation prototype",
                    "outputs": [
                        "Candidate: “Compare, compare the options, then then decide.”",
                        "Reference: “Compare the two options, then decide.”",
                    ],
                },
                "zh-Hans": {
                    "title": "模拟的失去连贯性的审慎思考旋钮",
                    "context": "一个任务得分提高但质量/连贯性门失败的合成案例。",
                    "knob": "审慎思考原型",
                    "outputs": [
                        "候选输出：“比较、比较方案，然后然后决定。”",
                        "参照输出：“比较两个方案，然后决定。”",
                    ],
                },
            },
        },
    ]
    for index, ticket in enumerate(definitions):
        ticket["flat_order"] = [
            (position + index) % 6 for position in range(6)
        ]
        ticket["source_details"] = _source_details(lineage, ticket.pop("source_ids"))
        keys = derive_ticket_keys(ticket)
        expected = {
            "UNC-R": ("W", "Q2_COMPARATOR_MISSINGNESS"),
            "UNC-S": ("S", "Q2_SCOPE_BOUNDARY"),
            "SKEP-R": ("U", "Q2_UNDERPOWERED_COMPARISON"),
            "SKEP-S": ("D", "Q2_MISSING_PAIRED_COMPARISON"),
            "DELIB-R": ("U", "Q2_DECISIVE_PAIRED_TEST"),
            "DELIB-S": ("W", "Q2_QUALITY_COHERENCE_FAIL"),
        }[ticket["ticket_code"]]
        if (keys["state"], keys["q2_issue"]) != expected:
            raise ValueError(f"normative key drift for {ticket['ticket_code']}")
    return definitions


def _common_copy() -> dict[str, dict[str, Any]]:
    q1_options = {
        "en": [
            {"id": "A", "text": "U — Pending; do not offer a user knob yet."},
            {"id": "B", "text": "D — Read-only diagnostic; no user adjustment."},
            {"id": "C", "text": "W — Hide; do not offer the knob."},
            {"id": "D", "text": "S — Adjustable only in the exact stated scope."},
        ],
        "zh-Hans": [
            {"id": "A", "text": "U — 待定；暂不向用户提供旋钮。"},
            {"id": "B", "text": "D — 只读诊断；用户不可调节。"},
            {"id": "C", "text": "W — 隐藏；不提供该旋钮。"},
            {"id": "D", "text": "S — 仅在明确写出的范围内可调。"},
        ],
    }
    q2_options = {
        "en": [
            {"id": "A", "text": "Comparator and missingness evidence."},
            {"id": "B", "text": "The exact applicability boundary."},
            {"id": "C", "text": "Whether the comparison is underpowered."},
            {"id": "D", "text": "A missing matched comparison."},
            {"id": "E", "text": "A decisive paired release test."},
            {"id": "F", "text": "The failed quality or coherence gate."},
        ],
        "zh-Hans": [
            {"id": "A", "text": "比较器与缺失值证据。"},
            {"id": "B", "text": "明确的适用边界。"},
            {"id": "C", "text": "比较是否检验力不足。"},
            {"id": "D", "text": "缺失的匹配比较。"},
            {"id": "E", "text": "有判定力的配对发布检验。"},
            {"id": "F", "text": "失败的质量或连贯性门。"},
        ],
    }
    headings = {
        "en": [
            "What evidence is named?",
            "How relative to prompt?",
            "What risk or measurement limit?",
            "Where applies?",
        ],
        "zh-Hans": [
            "证据是什么？",
            "与提示相比如何？",
            "有哪些风险或测量限制？",
            "适用于哪里？",
        ],
    }
    result: dict[str, dict[str, Any]] = {}
    for locale in LOCALES:
        en = locale == "en"
        result[locale] = {
            "language_name": "English" if en else "简体中文",
            "document_title": (
                "AI knob release review — local preview"
                if en else "AI 旋钮发布审核 — 本地预览"
            ),
            "badges": {
                "source_backed": "SOURCE-BACKED",
                "simulated": "SIMULATED",
                "illustrative_output": "ILLUSTRATIVE OUTPUT",
            },
            "chrome": {
                "header_title": (
                    "AI knob release review · local preview"
                    if en else "AI 旋钮发布审核 · 本地预览"
                ),
                "privacy_note": (
                    "Volatile loopback session; no participant data is persisted."
                    if en else "易失回环会话；不持久保存参与者数据。"
                ),
                "save_exit": (
                    "End & prepare partial export"
                    if en else "结束并生成部分导出"
                ),
                "footer": (
                    "DRAFT · owner-local · no human data"
                    if en else "DRAFT · 负责人本地 · 无人类数据"
                ),
            },
            "welcome": {
                "heading": "AI product release review" if en else "AI 产品发布审核",
                "subtitle": (
                    "Act as the release reviewer for six AI knob tickets."
                    if en else "请作为发布审核员处理六张 AI 旋钮工单。"
                ),
                "task_size": (
                    "You will complete 1 audio practice and 6 formal tickets."
                    if en else "你将完成 1 个音频练习和 6 张正式工单。"
                ),
                "warning": (
                    "DRAFT owner-local preview only · no recruitment · no ethics approval."
                    if en else "仅限负责人本地预览的 DRAFT · 不招募 · 未获伦理批准。"
                ),
                "no_resume": (
                    "There is no resume function. Refreshing or closing returns to the language gate."
                    if en else "本任务不能恢复。刷新或关闭后将返回语言选择页。"
                ),
                "participant_code": (
                    "Anonymous participant code" if en else "匿名参与者代码"
                ),
                "participant_code_help": (
                    "Use the owner-assigned code; do not enter a name."
                    if en else "请输入负责人分配的代码；请勿填写姓名。"
                ),
                "sequence": "Presentation sequence" if en else "呈现序列",
                "sequence_help": (
                    "The code controls balance only and is not an answer hint."
                    if en else "该代码仅用于平衡，不提供答案提示。"
                ),
                "details_summary": (
                    "Privacy and local-server details"
                    if en else "隐私与本地服务器详情"
                ),
                "details": [
                    (
                        "The server holds the attempt only in volatile memory."
                        if en else "服务器只在易失内存中保留本次尝试。"
                    ),
                    (
                        "Exports are prepared only after completion or confirmed early ending."
                        if en else "仅在完成任务或确认提前结束后生成导出。"
                    ),
                    (
                        "No account, cookie, browser storage, or recovery token is used."
                        if en else "不使用账户、Cookie、浏览器存储或恢复令牌。"
                    ),
                ],
                "start": "Start preview" if en else "开始预览",
                "switch_language": "简体中文" if en else "English",
            },
            "briefing": {
                "heading": "Release-review briefing" if en else "发布审核说明",
                "role": (
                    "Role: AI product release reviewer. You do not need to know latent mechanisms."
                    if en else "角色：AI 产品发布审核员。你不需要了解潜在机制。"
                ),
                "policy_heading": "Visible release policy" if en else "可见发布政策",
                "policy": q1_options[locale],
                "flow": [
                    (
                        "Read the product context, neutral prototype, illustrative outputs, and six evidence facts."
                        if en else "阅读产品背景、中性原型、示意输出和六条证据事实。"
                    ),
                    (
                        "Q1 decides how the next release should present the knob under the visible policy."
                        if en else "问题 1 按可见政策决定下一版如何呈现旋钮。"
                    ),
                    (
                        "After Q1 locks, Q2 asks which evidence most directly decides the ticket."
                        if en else "问题 1 锁定后，问题 2 询问哪项证据最直接决定该工单。"
                    ),
                ],
                "cca": (
                    "CCA means policy-consistent joint application of Q1 and Q2; it is not objective truth."
                    if en else "CCA 表示问题 1 与问题 2 的政策一致联合应用；它不是客观真理。"
                ),
                "continue_practice": (
                    "Continue to audio practice" if en else "继续音频练习"
                ),
            },
            "contract_headings": headings[locale],
            "flat_labels": [
                ("Evidence " if en else "证据 ") + letter for letter in "ABCDEF"
            ],
            "source_details": (
                "Method and source hash details" if en else "方法与来源哈希详情"
            ),
            "q1": {
                "text": (
                    "Q1. Under the visible policy, how should the next release present this knob?"
                    if en else "问题 1：按可见政策，下一版应如何呈现该旋钮？"
                ),
                "options": q1_options[locale],
            },
            "q2": {
                "text": (
                    "Q2. Which evidence most directly decides this release ticket?"
                    if en else "问题 2：哪项证据最直接决定这张发布工单？"
                ),
                "options": q2_options[locale],
            },
            "knob_unavailable": (
                "Unavailable prototype; the neutral position is not a recommendation."
                if en else "不可用的原型；中性位置不表示推荐。"
            ),
            "locked": (
                "Q1 locked: {choice}. This choice cannot be changed."
                if en else "问题 1 已锁定：{choice}。该选择不能更改。"
            ),
            "preview": {
                "heading": "Decision preview" if en else "决策预览",
                "body": (
                    "Your release choice: {choice}. This is only a neutral echo of your answer, not correctness feedback."
                    if en else "你的发布选择：{choice}。这里只中性回显你的答案，不提供正误反馈。"
                ),
                "continue": "Continue" if en else "继续",
            },
            "practice": {
                "heading": "Audio practice ticket" if en else "音频练习工单",
                "context": (
                    "Review a noise-reduction knob against the existing preset."
                    if en else "审核一个相对现有预设的降噪旋钮。"
                ),
                "knob": "Noise-reduction candidate" if en else "降噪候选",
                "preset": "Play existing preset" if en else "播放现有预设",
                "candidate": "Play candidate" if en else "播放候选",
                "facts": (
                    [
                        "The existing preset is the release comparator.",
                        "The candidate changes the listening preview.",
                        "The candidate has not beaten the existing preset.",
                        "The speech-quality check fails.",
                        "The comparison and quality result apply to this audio workflow.",
                        "The release policy therefore does not offer this candidate knob.",
                    ]
                    if en else
                    [
                        "现有预设是发布比较器。",
                        "候选设置会改变试听结果。",
                        "候选设置尚未优于现有预设。",
                        "语音质量检查未通过。",
                        "比较与质量结果适用于该音频工作流。",
                        "因此发布政策不提供该候选旋钮。",
                    ]
                ),
                "q1": (
                    "How should the candidate knob be presented?"
                    if en else "应如何呈现该候选旋钮？"
                ),
                "q2": (
                    "Which evidence is decisive?"
                    if en else "哪项证据具有决定性？"
                ),
                "q2_options": (
                    [
                        {"id": "A", "text": "The candidate changes the preview."},
                        {"id": "B", "text": "It does not beat the preset and fails speech quality."},
                        {"id": "C", "text": "The knob has a neutral midpoint."},
                        {"id": "D", "text": "The preview uses audio."},
                    ]
                    if en else
                    [
                        {"id": "A", "text": "候选设置改变了试听结果。"},
                        {"id": "B", "text": "候选未优于预设，且语音质量失败。"},
                        {"id": "C", "text": "旋钮有一个中性中点。"},
                        {"id": "D", "text": "预览使用音频。"},
                    ]
                ),
                "feedback": (
                    "Practice result: use W. A changed preview is not enough; the preset was not beaten and speech quality failed."
                    if en else "练习结论：选择 W。仅改变试听不足以发布；候选未优于预设，且语音质量失败。"
                ),
                "submit_q1": "Lock practice Q1" if en else "锁定练习问题 1",
                "submit_q2": "Submit practice Q2" if en else "提交练习问题 2",
                "begin_formal": "Begin 6 formal tickets" if en else "开始 6 张正式工单",
            },
            "buttons": {
                "submit_q1": "Lock Q1" if en else "锁定问题 1",
                "submit_q2": "Submit Q2" if en else "提交问题 2",
                "download_json": "Download signed JSON" if en else "下载签名 JSON",
                "download_csv": "Download signed CSV" if en else "下载签名 CSV",
                "finish": "Finish" if en else "完成",
            },
            "progress": {
                "ticket": "Ticket {current} of 6" if en else "第 {current}/6 张工单",
            },
            "save_exit": {
                "heading": (
                    "End this session and prepare a partial export?"
                    if en else "结束本次会话并生成部分导出？"
                ),
                "intro": (
                    "Confirm only if you want to end now."
                    if en else "仅在确定现在结束时确认。"
                ),
                "consequences": [
                    (
                        "This session cannot be resumed."
                        if en else "本次会话无法恢复。"
                    ),
                    (
                        "Submitted answers will be frozen; unfinished answers remain null and missing."
                        if en else "已提交答案将冻结；未完成答案保持 null 与缺失。"
                    ),
                    (
                        "All six planned slots remain in the signed partial export."
                        if en else "签名的部分导出始终保留全部六个计划槽位。"
                    ),
                    (
                        "No correctness feedback or automatic download is provided."
                        if en else "不提供正误反馈，也不会自动下载。"
                    ),
                ],
                "cancel": "Cancel" if en else "取消",
                "confirm": (
                    "End & prepare partial export"
                    if en else "结束并生成部分导出"
                ),
            },
            "export": {
                "complete_heading": "Preview complete" if en else "预览完成",
                "partial_heading": (
                    "Session ended — partial export prepared"
                    if en else "会话已结束 — 已生成部分导出"
                ),
                "complete_count": (
                    "Completed formal tickets: 6 of 6."
                    if en else "已完成正式工单：6/6。"
                ),
                "partial_ready": (
                    "The signed partial contains all six planned slots; unfinished fields remain null and marked missing."
                    if en else "签名部分导出包含全部六个计划槽位；未完成字段保持 null 并标记缺失。"
                ),
                "ready": (
                    "Export ready. Choose a format; files do not download automatically."
                    if en else "导出已准备好。请选择格式；文件不会自动下载。"
                ),
                "retry": (
                    "If a download fails, both buttons remain available while the volatile session is retained."
                    if en else "下载失败时，只要易失会话仍保留，两种下载按钮都会继续可用。"
                ),
                "download_started": (
                    "{format} download started."
                    if en else "{format} 下载已开始。"
                ),
                "finished_heading": "Finished" if en else "已完成",
                "finished": (
                    "The client view is cleared; the volatile signed export remains until TTL expiry."
                    if en else "客户端视图已清空；易失签名导出保留至 TTL 到期。"
                ),
            },
            "debrief": (
                "This DRAFT uses source-backed and simulated release tickets. Illustrative outputs are not experiment results. CCA is policy-consistent joint application, not objective truth. No response changes paper evidence."
                if en else "本 DRAFT 使用来源有据和模拟发布工单。示意输出不是实验结果。CCA 是政策一致联合应用，不是客观真理。任何回答都不会改变论文证据。"
            ),
            "errors": {
                "load": "Could not load materials." if en else "无法加载材料。",
                "state": "Study state error." if en else "任务状态错误。",
                "download": "Signed export download failed." if en else "签名导出下载失败。",
                "export_not_ready": "Signed export is not ready." if en else "签名导出尚未准备好。",
                "required_q1": "Choose a Q1 release action." if en else "请选择问题 1 的发布动作。",
                "required_q2": "Choose the decisive evidence." if en else "请选择决定性证据。",
            },
        }
    return result


def _strip_private_ticket(ticket: dict[str, Any], locale: str) -> dict[str, Any]:
    display = ticket["display"][locale]
    return {
        "ticket_code": ticket["ticket_code"],
        "source_badge": ticket["source_kind"],
        "title": display["title"],
        "context": display["context"],
        "knob": display["knob"],
        "outputs": list(display["outputs"]),
        "facts": list(ticket["facts"][locale]),
        "flat_order": list(ticket["flat_order"]),
        "source_details": deepcopy(ticket["source_details"]),
    }


def _valid_orders() -> list[tuple[str, ...]]:
    result = []
    for order in itertools.permutations(TICKET_CODES):
        positions = {ticket: index for index, ticket in enumerate(order)}
        if all(abs(positions[left] - positions[right]) >= 3 for left, right in SCENARIO_PAIRS):
            result.append(order)
    return result


def _select_latin_orders() -> list[tuple[str, ...]]:
    candidates = _valid_orders()
    constraints = {
        (ticket, position)
        for ticket in TICKET_CODES
        for position in range(6)
    }
    by_constraint: dict[tuple[str, int], list[tuple[str, ...]]] = {
        constraint: [] for constraint in constraints
    }
    for order in candidates:
        for position, ticket in enumerate(order):
            by_constraint[(ticket, position)].append(order)

    def search(
        remaining: set[tuple[str, int]],
        chosen: list[tuple[str, ...]],
        used: set[tuple[str, ...]],
    ) -> list[tuple[str, ...]] | None:
        if not remaining:
            return chosen
        constraint = min(
            sorted(remaining),
            key=lambda value: (
                sum(
                    candidate not in used
                    and all(
                        (ticket, pos) in remaining
                        for pos, ticket in enumerate(candidate)
                    )
                    for candidate in by_constraint[value]
                ),
                value,
            ),
        )
        for order in by_constraint[constraint]:
            covered = {(ticket, position) for position, ticket in enumerate(order)}
            if order in used or not covered <= remaining:
                continue
            found = search(remaining - covered, chosen + [order], used | {order})
            if found is not None:
                return found
        return None

    selected = search(set(constraints), [], set())
    if selected is None or len(selected) != 6:
        raise ValueError("no deterministic Latin order cover found")
    return selected


def generate_sequences() -> dict[str, Any]:
    orders = _select_latin_orders()
    condition_patterns = [
        pattern
        for pattern in itertools.product((0, 1), repeat=3)
        if pattern not in {(0, 0, 0), (1, 1, 1)}
    ]
    scenario_index = {"UNC": 0, "SKEP": 1, "DELIB": 2}

    def condition(ticket: str, pattern: tuple[int, int, int]) -> str:
        bit = pattern[scenario_index[ticket.split("-")[0]]]
        real_ticket = ticket.endswith("-R")
        return "C" if real_ticket == bool(bit) else "F"

    first_half = [
        [
            {
                "position": position + 1,
                "ticket_code": ticket,
                "condition": condition(ticket, pattern),
            }
            for position, ticket in enumerate(order)
        ]
        for order, pattern in zip(orders, condition_patterns)
    ]
    second_half = [
        [
            {
                **slot,
                "condition": "F" if slot["condition"] == "C" else "C",
            }
            for slot in row
        ]
        for row in first_half
    ]
    rows = first_half + second_half
    sequences = [
        {"code": f"V9-{index + 1:02d}", "slots": slots}
        for index, slots in enumerate(rows)
    ]
    return {
        "schema_version": SEQUENCE_SCHEMA_VERSION,
        "generator": {
            "version": "stdlib-exact-cover-v1",
            "valid_order_count": len(_valid_orders()),
            "pair_separation_minimum": 3,
            "selection": "exact cover over ticket×position, then complementary condition rows",
        },
        "sequences": sequences,
    }


def generate_materials() -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    payloads, lineage = verified_source_payloads()
    evidence = extract_real_evidence(payloads)
    definitions = _ticket_definitions(evidence, lineage)
    private_keys = {
        ticket["ticket_code"]: derive_ticket_keys(ticket) for ticket in definitions
    }
    materials = {
        "schema_version": MATERIAL_SCHEMA_VERSION,
        "materials_version": MATERIALS_VERSION,
        "status": "DRAFT_NOT_FROZEN_OWNER_LOCAL_PREVIEW_NO_HUMAN_DATA",
        "locale_contract": {
            "version": "microstudy-v9-locale-contract-v1",
            "supported": list(LOCALES),
            "fallback": None,
            "auto_detect": False,
            "stable_id_parity": True,
            "human_semantic_review": "UNVERIFIED_PRE_RECRUITMENT",
        },
        "nonlocalized": {
            "ticket_codes": list(TICKET_CODES),
            "q1_option_ids": list("ABCD"),
            "q2_option_ids": list("ABCDEF"),
            "source_registry": lineage,
            "render_contract": {
                "version": "microstudy-v9-render-contract-v1",
                "contract_group_sizes": [1, 2, 2, 1],
                "flat_labels": "neutral Latin Evidence A-F permutation",
                "body_parity": "same six localized fact strings in both conditions",
                "only_badges": [
                    "SOURCE-BACKED", "SIMULATED", "ILLUSTRATIVE OUTPUT"
                ],
                "forbidden_semantic_carriers": [
                    "condition IDs", "group IDs", "role IDs", "answer keys",
                    "correctness classes", "state colors", "recommendation icons",
                ],
                "desktop_minimum_width_px": 1280,
                "responsive_human_gate": "PENDING",
            },
            "export_schema": {
                "version": EXPORT_SCHEMA_VERSION,
                "session_fields": [
                    "attempt_id", "run_id", "attempt_serial", "participant_code",
                    "sequence", "ui_language", "locale_bundle_version",
                    "locale_bundle_hash", "completion_status", "complete",
                    "practice_presented", "practice_q1_submitted",
                    "practice_q2_submitted", "practice_complete",
                    "mechanical_exclusion", "mechanical_exclusion_reason",
                ],
                "trial_fields": [
                    "slot_index", "ticket_code", "position", "planned", "presented",
                    "q1_submitted", "q2_submitted", "complete", "submitted",
                    "q1", "q2", "q1_correct", "q2_correct", "cca_correct",
                    "rt_q1_ms", "rt_q2_ms", "rt_total_ms", "hidden_ms",
                    "q1_missing", "q2_missing", "q1_correct_missing",
                    "q2_correct_missing", "cca_correct_missing", "rt_q1_missing",
                    "rt_q2_missing", "rt_total_missing", "hidden_ms_missing",
                    "materials_version",
                ],
                "mechanical_exclusion_reasons": [
                    "none", "duplicate_attempt", "technical_corrupt",
                    "assignment_mismatch",
                ],
                "free_text_fields": [],
            },
            "analysis_contract": {
                "primary": "all six complete; paired mean C-minus-F CCA",
                "available": "at least two complete per condition and at least four total",
                "missing_as_incorrect": "all six planned slots",
                "mde_status": "UNVERIFIED_NOT_ESTIMATED",
                "sequence_consumption": (
                    "each valid six-complete export consumes its sequence slot, "
                    "including mechanically excluded complete exports; partial "
                    "and fewer-than-six-complete exports reuse the slot"
                ),
            },
            "tickets": [
                {
                    "ticket_code": ticket["ticket_code"],
                    "source_kind": ticket["source_kind"],
                    "flat_order": ticket["flat_order"],
                }
                for ticket in definitions
            ],
            "practice": {
                "source_kind": "SIMULATED",
                "q1_option_ids": list("ABCD"),
                "q2_option_ids": list("ABCD"),
            },
        },
        "locales": {
            locale: {
                **_common_copy()[locale],
                "tickets": [
                    _strip_private_ticket(ticket, locale) for ticket in definitions
                ],
            }
            for locale in LOCALES
        },
    }
    return materials, private_keys


def canonical_locale_bytes(bundle: dict[str, Any]) -> bytes:
    return canonical_json_bytes(bundle)


def locale_manifest(materials: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {
        locale: {
            "locale_bundle_version": f"{materials['materials_version']}-{locale}",
            "locale_bundle_hash": hashlib.sha256(
                canonical_locale_bytes(materials["locales"][locale])
            ).hexdigest(),
        }
        for locale in materials["locale_contract"]["supported"]
    }


def write_generated_materials() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    materials, _ = generate_materials()
    sequences = generate_sequences()
    MATERIALS_PATH.write_text(
        json.dumps(materials, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    SEQUENCES_PATH.write_text(
        json.dumps(sequences, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_sources(
    materials_path: Path = MATERIALS_PATH,
    sequences_path: Path = SEQUENCES_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    return (
        json.loads(materials_path.read_text(encoding="utf-8")),
        json.loads(sequences_path.read_text(encoding="utf-8")),
    )


def private_answer_keys() -> dict[str, dict[str, str]]:
    _, keys = generate_materials()
    return keys


def _participant_strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [
            text for child in value.values() for text in _participant_strings(child)
        ]
    if isinstance(value, list):
        return [
            text for child in value for text in _participant_strings(child)
        ]
    return [value] if isinstance(value, str) else []


def validate_sequences(sequences: dict[str, Any]) -> dict[str, Any]:
    expected = generate_sequences()
    if sequences != expected:
        raise ValueError("sequence artifact does not match deterministic generator")
    rows = sequences["sequences"]
    if len(rows) != 12:
        raise ValueError("exactly twelve sequences required")
    if [row["code"] for row in rows] != [
        f"V9-{index:02d}" for index in range(1, 13)
    ]:
        raise ValueError("sequence code set/order drifted")
    cells = Counter()
    half_ticket_position = {0: Counter(), 1: Counter()}
    half_ticket_condition = {0: Counter(), 1: Counter()}
    half_source_condition = {0: Counter(), 1: Counter()}
    half_state_condition = {0: Counter(), 1: Counter()}
    period_condition = Counter()
    period_source_condition = Counter()
    period_state_condition = Counter()
    for sequence_index, sequence in enumerate(rows):
        slots = sequence["slots"]
        if len(slots) != 6 or {slot["ticket_code"] for slot in slots} != set(TICKET_CODES):
            raise ValueError("each sequence must contain every ticket exactly once")
        if Counter(slot["condition"] for slot in slots) != {"C": 3, "F": 3}:
            raise ValueError("each sequence must contain three C and three F tickets")
        if Counter(
            "R" if slot["ticket_code"].endswith("-R") else "S"
            for slot in slots
        ) != {"R": 3, "S": 3}:
            raise ValueError("each sequence must contain three real and three simulated tickets")
        if Counter(
            TICKET_STATE_BY_CODE[slot["ticket_code"]] for slot in slots
        ) != {"U": 2, "D": 1, "W": 2, "S": 1}:
            raise ValueError("each sequence state distribution drifted")
        for left, right in SCENARIO_PAIRS:
            scenario_conditions = {
                slot["condition"]
                for slot in slots
                if slot["ticket_code"] in {left, right}
            }
            if scenario_conditions != {"C", "F"}:
                raise ValueError("each scenario must contribute one C and one F ticket")
        positions = {slot["ticket_code"]: slot["position"] for slot in slots}
        if not all(
            abs(positions[left] - positions[right]) >= 3
            for left, right in SCENARIO_PAIRS
        ):
            raise ValueError("scenario-pair separation is below three")
        half = 0 if sequence_index < 6 else 1
        for slot in slots:
            cells[(slot["ticket_code"], slot["condition"], slot["position"])] += 1
            half_ticket_position[half][
                (slot["ticket_code"], slot["position"])
            ] += 1
            half_ticket_condition[half][
                (slot["ticket_code"], slot["condition"])
            ] += 1
            source = "R" if slot["ticket_code"].endswith("-R") else "S"
            state = TICKET_STATE_BY_CODE[slot["ticket_code"]]
            half_source_condition[half][(source, slot["condition"])] += 1
            half_state_condition[half][(state, slot["condition"])] += 1
            period_condition[(slot["position"], slot["condition"])] += 1
            period_source_condition[
                (slot["position"], source, slot["condition"])
            ] += 1
            period_state_condition[
                (slot["position"], state, slot["condition"])
            ] += 1
    expected_cells = {
        (ticket, condition, position)
        for ticket in TICKET_CODES
        for condition in ("C", "F")
        for position in range(1, 7)
    }
    if set(cells) != expected_cells or set(cells.values()) != {1}:
        raise ValueError("ticket×condition×position exact cover failed")
    for half in (0, 1):
        if set(half_ticket_position[half].values()) != {1}:
            raise ValueError("first-six/last-six ticket-position balance failed")
        if set(half_ticket_condition[half].values()) != {3}:
            raise ValueError("first-six/last-six ticket-condition balance failed")
        if half_source_condition[half] != Counter({
            (source, condition): 9
            for source in ("R", "S")
            for condition in ("C", "F")
        }):
            raise ValueError("first-six/last-six source-condition balance failed")
        if half_state_condition[half] != Counter({
            (state, condition): count * 3
            for state, count in {"U": 2, "D": 1, "W": 2, "S": 1}.items()
            for condition in ("C", "F")
        }):
            raise ValueError("first-six/last-six state-condition balance failed")
    if period_condition != Counter({
        (position, condition): 6
        for position in range(1, 7)
        for condition in ("C", "F")
    }):
        raise ValueError("condition-period balance failed")
    if period_source_condition != Counter({
        (position, source, condition): 3
        for position in range(1, 7)
        for source in ("R", "S")
        for condition in ("C", "F")
    }):
        raise ValueError("source-condition-period balance failed")
    if period_state_condition != Counter({
        (position, state, condition): count
        for position in range(1, 7)
        for state, count in {"U": 2, "D": 1, "W": 2, "S": 1}.items()
        for condition in ("C", "F")
    }):
        raise ValueError("state-condition-period balance failed")
    for first, second in zip(rows[:6], rows[6:]):
        if [row["ticket_code"] for row in first["slots"]] != [
            row["ticket_code"] for row in second["slots"]
        ]:
            raise ValueError("second-six ticket-order complement failed")
        if any(
            left["condition"] == right["condition"]
            for left, right in zip(first["slots"], second["slots"])
        ):
            raise ValueError("second-six condition complement failed")
    return {
        "sequence_count": len(rows),
        "valid_order_count": sequences["generator"]["valid_order_count"],
        "exact_cover_cells": len(cells),
        "first_six_balanced": True,
        "last_six_balanced": True,
        "source_balanced": True,
        "state_balanced": True,
        "period_balanced": True,
    }


def validate_materials(
    materials_path: Path = MATERIALS_PATH,
    sequences_path: Path = SEQUENCES_PATH,
) -> dict[str, Any]:
    materials, sequences = load_sources(materials_path, sequences_path)
    generated, private_keys = generate_materials()
    if materials != generated:
        raise ValueError("public materials do not match the structured generator")
    if materials["schema_version"] != MATERIAL_SCHEMA_VERSION:
        raise ValueError("wrong V9 material schema")
    if materials["materials_version"] != MATERIALS_VERSION:
        raise ValueError("wrong V9 materials version")
    if set(materials["locales"]) != set(LOCALES):
        raise ValueError("locale set mismatch")
    if materials["locale_contract"]["fallback"] is not None:
        raise ValueError("locale fallback is forbidden")
    if materials["locale_contract"]["auto_detect"] is not False:
        raise ValueError("locale auto-detection is forbidden")
    if set(private_keys) != set(TICKET_CODES):
        raise ValueError("private key ticket coverage failed")
    if Counter(row["state"] for row in private_keys.values()) != {
        "U": 2, "D": 1, "W": 2, "S": 1
    }:
        raise ValueError("state distribution drifted")
    if Counter(row["q2_issue"] for row in private_keys.values()) != {
        issue: 1 for issue in Q2_ISSUE_ORDER
    }:
        raise ValueError("Q2 issue uniqueness drifted")
    source_payloads, source_lineage = verified_source_payloads()
    definitions = _ticket_definitions(
        extract_real_evidence(source_payloads), source_lineage
    )
    for ticket in definitions:
        expected_key = derive_ticket_keys(ticket)
        minimal = {
            "policy_inputs": deepcopy(ticket["policy_inputs"]),
            "decisive_issue": ticket["decisive_issue"],
        }
        if derive_ticket_keys(minimal) != expected_key:
            raise ValueError("minimal key derivation failed")
        for field in set(ticket) - {"policy_inputs", "decisive_issue"}:
            without_nonkey = deepcopy(ticket)
            del without_nonkey[field]
            if derive_ticket_keys(without_nonkey) != expected_key:
                raise ValueError(f"non-key field affects answer derivation: {field}")
    encoded = json.dumps(materials, ensure_ascii=False)
    for forbidden in (
        "expected_q1", "expected_q2", "correct_key", "q1_key", "q2_key",
        "Q2_COMPARATOR_MISSINGNESS", "Q2_SCOPE_BOUNDARY",
        "Q2_UNDERPOWERED_COMPARISON", "Q2_MISSING_PAIRED_COMPARISON",
        "Q2_DECISIVE_PAIRED_TEST", "Q2_QUALITY_COHERENCE_FAIL",
    ):
        if forbidden in encoded:
            raise ValueError(f"private key leakage: {forbidden}")
    for locale in LOCALES:
        bundle = materials["locales"][locale]
        if len(bundle["tickets"]) != 6:
            raise ValueError("localized ticket coverage failed")
        if bundle["badges"] != {
            "source_backed": "SOURCE-BACKED",
            "simulated": "SIMULATED",
            "illustrative_output": "ILLUSTRATIVE OUTPUT",
        }:
            raise ValueError("badge vocabulary drifted")
        if [row["id"] for row in bundle["q1"]["options"]] != list("ABCD"):
            raise ValueError("Q1 option IDs drifted")
        if [row["id"] for row in bundle["q2"]["options"]] != list("ABCDEF"):
            raise ValueError("Q2 option IDs drifted")
        for ticket in bundle["tickets"]:
            if len(ticket["facts"]) != 6 or len(ticket["outputs"]) != 2:
                raise ValueError("ticket fact/output shape drifted")
            if ticket["source_badge"] not in {"SOURCE-BACKED", "SIMULATED"}:
                raise ValueError("invalid source badge")
        unc = next(row for row in bundle["tickets"] if row["ticket_code"] == "UNC-R")
        unc_text = "\n".join(unc["facts"])
        required_unc = (
            (
                "4 CAA/ITI", "4 had no passing axis", "approximately baseline",
                "complete-case", "bounds cross zero", "other 3 cells are unrechecked",
                "latent arms still had no pass",
            )
            if locale == "en"
            else (
                "4 个 CAA/ITI", "4 个单元", "基本相当", "完整案例",
                "边界跨过零", "其余 3 个单元尚未复查", "仍没有潜在干预通过",
            )
        )
        if not all(marker in unc_text for marker in required_unc):
            raise ValueError("mandatory UNC caveat is not visible")
        skep = next(
            row for row in bundle["tickets"] if row["ticket_code"] == "SKEP-R"
        )
        skep_text = "\n".join(skep["facts"])
        required_skep = (
            ("underpowered", "MDEs", "target effect")
            if locale == "en"
            else ("检验力不足", "MDE", "目标效应")
        )
        if not all(marker in skep_text for marker in required_skep):
            raise ValueError("mandatory skepticism power caveat is not visible")
        deliberation = next(
            row for row in bundle["tickets"] if row["ticket_code"] == "DELIB-R"
        )
        deliberation_text = "\n".join(deliberation["facts"])
        required_deliberation = (
            ("mixed near zero", "64-token cap", "decisive paired test")
            if locale == "en"
            else ("零附近呈混合结果", "64 个 token", "有判定力的配对检验")
        )
        if not all(marker in deliberation_text for marker in required_deliberation):
            raise ValueError("mandatory deliberation caveat is not visible")
        practice = bundle["practice"]
        comparator_marker_present = (
            "preset" in practice["facts"][0].lower()
            if locale == "en"
            else "预设" in practice["facts"][0]
        )
        if (
            len(practice["facts"]) != 6
            or [row["id"] for row in practice["q2_options"]] != list("ABCD")
            or not comparator_marker_present
        ):
            raise ValueError("audio practice contract drifted")
        visible = "\n".join(_participant_strings(bundle))
        if "PASS" in visible or "FAIL" in visible:
            raise ValueError("participant copy uses forbidden correctness badges")
    english = {
        row["ticket_code"]: row for row in materials["locales"]["en"]["tickets"]
    }
    chinese = {
        row["ticket_code"]: row
        for row in materials["locales"]["zh-Hans"]["tickets"]
    }
    for ticket_code in TICKET_CODES:
        if len(english[ticket_code]["facts"]) != len(chinese[ticket_code]["facts"]):
            raise ValueError("bilingual fact parity failed")
        if english[ticket_code]["flat_order"] != chinese[ticket_code]["flat_order"]:
            raise ValueError("bilingual Flat-order parity failed")
        if english[ticket_code]["source_badge"] != chinese[ticket_code]["source_badge"]:
            raise ValueError("bilingual badge parity failed")
    for position in range(6):
        if Counter(
            ticket["flat_order"][position]
            for ticket in materials["nonlocalized"]["tickets"]
        ) != Counter(range(6)):
            raise ValueError("Flat Latin permutation failed")
    sequence_metrics = validate_sequences(sequences)
    return {
        "status": "PASS",
        "schema_version": materials["schema_version"],
        "materials_version": materials["materials_version"],
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "locale_manifest": locale_manifest(materials),
        "source_count": len(materials["nonlocalized"]["source_registry"]),
        "ticket_count": 6,
        "state_distribution": dict(Counter(
            row["state"] for row in private_keys.values()
        )),
        "q2_unique": True,
        "mde_status": "UNVERIFIED_NOT_ESTIMATED",
        **sequence_metrics,
    }


def main() -> int:
    print(json.dumps(validate_materials(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
