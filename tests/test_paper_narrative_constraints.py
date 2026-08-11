import importlib.util
from pathlib import Path

import yaml
from pypdf import PdfReader

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "paper"
    / "scripts"
    / "check_narrative_constraints.py"
)
SPEC = importlib.util.spec_from_file_location("check_narrative_constraints", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECKER)

TAXONOMY_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "paper"
    / "scripts"
    / "make_failure_taxonomy.py"
)
TAXONOMY_SPEC = importlib.util.spec_from_file_location(
    "make_failure_taxonomy", TAXONOMY_SCRIPT
)
TAXONOMY = importlib.util.module_from_spec(TAXONOMY_SPEC)
assert TAXONOMY_SPEC.loader is not None
TAXONOMY_SPEC.loader.exec_module(TAXONOMY)


def test_abstract_counter_excludes_model_identifiers():
    text = (
        "CAA/ITI across Qwen2.5-7B and Llama-3-8B produced "
        "0/12 passes and 5/5 split verdicts."
    )
    assert CHECKER.abstract_numeric_expressions(text) == ["0", "12", "5", "5"]


def test_abstract_counter_retains_decimal_ci_and_percent_values():
    text = (
        r"The margin was 0.05, with 95\% CI [-0.51, -0.17], "
        "and Qwen2.5-7B changed by +0.0008."
    )
    assert CHECKER.abstract_numeric_expressions(text) == [
        "0.05",
        r"95\%",
        "-0.51",
        "-0.17",
        "+0.0008",
    ]


def test_numeric_values_ignore_includegraphics_crop_and_layout_coordinates():
    base = (
        r"\includegraphics[trim=1 2 3 4,clip,width=0.8\linewidth]{figure.pdf}"
        "\n"
        r"\draw (1.5,2.5) -- (3.5,4.5);"
        "\n"
        r"\vspace{-0.7em}"
    )
    changed = (
        r"\includegraphics[trim=9 8 7 6,clip,width=0.9\linewidth]{figure.pdf}"
        "\n"
        r"\draw (5.5,6.5) -- (7.5,8.5);"
        "\n"
        r"\vspace{-1.2em}"
    )
    assert CHECKER.numeric_values(base) == CHECKER.numeric_values(changed) == set()


def test_numeric_values_detect_body_margin_ci_and_mde_changes():
    base = r"The margin is \(0.05\), CI [-0.51,-0.17], and MDE is 0.19."
    changed = r"The margin is \(0.06\), CI [-0.50,-0.16], and MDE is 0.20."
    assert CHECKER.numeric_values(base) != CHECKER.numeric_values(changed)


def test_numeric_values_detect_scientific_number_in_figure_caption():
    base = r"\caption{The registered margin is 0.05.}"
    changed = r"\caption{The registered margin is 0.06.}"
    assert CHECKER.numeric_values(base) != CHECKER.numeric_values(changed)


def test_failure_taxonomy_scopes_direct_near_baseline_to_rechecked_cell():
    rendered = TAXONOMY.render()
    assert "direct steer-vs-baseline is near zero only in the rechecked CAA" in rendered
    assert "Four-cell support is limited to the steer-vs-prompt comparator-negative contrast" in rendered


def test_checklist_maps_result_reason_and_action_with_complete_tier():
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    assert all(CHECKER.checklist_mapping(paper).values())


def test_mapping_consistency_uses_approved_direct_vocabulary():
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    assert all(CHECKER.mapping_consistency(paper).values())


class _PaperSource:
    def __init__(self, text):
        self.text = text

    def read_text(self, encoding):
        assert encoding == "utf-8"
        return self.text


def _assert_main_rejects(monkeypatch, paper):
    monkeypatch.setattr(CHECKER, "PAPER", _PaperSource(paper))
    assert CHECKER.main([]) == 1


def test_main_accepts_current_paper(monkeypatch):
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    monkeypatch.setattr(CHECKER, "PAPER", _PaperSource(paper))
    assert CHECKER.main([]) == 0


def test_main_rejects_missing_exact_tier_identity(monkeypatch):
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    mutated = paper.replace(
        "model, method, direction and layer, task and outcome, protocol and version, and comparator",
        "model and method",
    )
    assert mutated != paper
    _assert_main_rejects(monkeypatch, mutated)


def test_main_rejects_missing_direct_mapping_term(monkeypatch):
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    mutated = paper.replace("write the specific blocking reason", "write the result note", 1)
    assert mutated != paper
    _assert_main_rejects(monkeypatch, mutated)


def test_main_rejects_abstract_without_steer_vs_prompt_qualifier(monkeypatch):
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    mutated = paper.replace(
        "All four steer-vs-prompt uncertainty contrasts",
        "All four uncertainty contrasts",
        1,
    )
    assert mutated != paper
    _assert_main_rejects(monkeypatch, mutated)


def test_main_rejects_abstract_without_direct_mapping(monkeypatch):
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    mutated = paper.replace("blocking reason and record-specific interface action", "record", 1)
    assert mutated != paper
    _assert_main_rejects(monkeypatch, mutated)


def test_canonical_main_and_handoff_reject_stale_formal_taxonomy():
    assert CHECKER.stale_taxonomy_hits() == {}


def test_stale_taxonomy_pattern_catches_cross_surface_regression():
    for stale in (
        "diagnostic-only",
        "Diagnostic only",
        "withheld-control",
        "evidence-supported control",
        "formal four-state taxonomy",
        "Four states: Read-only, Unresolved, Unstable, Eligible",
        "Interface labels: Eligible, Read-only, Unstable, and Unresolved",
    ):
        assert CHECKER.STALE_TAXONOMY.search(stale)


def test_c3_claim_and_reverse_map_include_console_figure():
    claim_map = yaml.safe_load(
        (CHECKER.PAPER.parent / "claim-map.yaml").read_text(encoding="utf-8")
    )
    assert "fig-console-ui-contract" in claim_map["claims"]["C3"]["main_artifacts"]
    reverse = claim_map["reverse_artifact_map"]["fig-console-ui-contract"]
    assert reverse["supports_claims"] == ["C2", "C3"]
    assert reverse["manifest"] == "docs/paper/figure-manifests/console-ui-contract.yaml"


def test_handoff_build_page_count_matches_committed_pdf():
    handoff = CHECKER.PAPER.parent / "reconstruction-handoff-2026-08-11"
    page_count = len(PdfReader(str(handoff / "reframed.pdf")).pages)
    build_notes = (handoff / "pipeline" / "BUILD.md").read_text(encoding="utf-8")
    readme = (handoff / "README.md").read_text(encoding="utf-8")
    assert page_count == 17
    assert f"{page_count} pages" in build_notes
    assert f"{page_count} pages" in readme


def test_concept_figure_uses_direct_mapping_edges():
    source = CHECKER.CONCEPT_FIGURE.read_text(encoding="utf-8")
    assert CHECKER.concept_edges(source) == CHECKER.EXPECTED_FIGURE_EDGES


def test_concept_figure_uses_ordered_vertical_decision_layers():
    source = CHECKER.CONCEPT_FIGURE.read_text(encoding="utf-8")
    positions = CHECKER.concept_positions(source)
    assert positions["candidate"][1] > positions["result"][1]
    assert positions["result"][1] > positions["reason"][1]
    assert positions["reason"][1] > positions["action"][1]
    assert positions["action"][1] > positions["annotation"][1]
