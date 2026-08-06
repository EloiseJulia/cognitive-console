import importlib.util
import re
from pathlib import Path


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


def test_checklist_routes_each_condition_to_exact_state():
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    assert CHECKER.checklist_routes(paper) == CHECKER.EXPECTED_ROUTES


def test_state_consistency_parses_cross_line_textbf_from_latex_source():
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    assert r"\textbf{" + "\nwithheld-control}" in paper
    assert all(CHECKER.state_consistency(paper).values())


class _PaperSource:
    def __init__(self, text):
        self.text = text

    def read_text(self, encoding):
        assert encoding == "utf-8"
        return self.text


def _assert_main_rejects(monkeypatch, paper):
    monkeypatch.setattr(CHECKER, "PAPER", _PaperSource(paper))
    assert CHECKER.main([]) == 1


def _mutate_checklist_state(paper, condition_pattern, replacement):
    block = CHECKER.checklist_block(paper)
    mutated, count = re.subn(
        rf"(\\item\s+\\textbf\s*\{{[^}}]*{condition_pattern}[^}}]*\}}"
        rf".*?\\\(\\rightarrow\\\)\s+\\textsc\s*\{{)[^}}]+(\}})",
        rf"\g<1>{replacement}\2",
        block,
        count=1,
        flags=re.I | re.S,
    )
    assert count == 1
    return paper.replace(block, mutated, 1)


def test_main_accepts_current_paper(monkeypatch):
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    monkeypatch.setattr(CHECKER, "PAPER", _PaperSource(paper))
    assert CHECKER.main([]) == 0


def test_main_accepts_cross_line_textbf_in_checklist(monkeypatch):
    paper = CHECKER.PAPER.read_text(encoding="utf-8")
    block = CHECKER.checklist_block(paper)
    mutated = block.replace(
        r"\textbf{READ unsupported}",
        "\\textbf{\nREAD unsupported}",
        1,
    )
    assert mutated != block
    paper = paper.replace(block, mutated, 1)
    monkeypatch.setattr(CHECKER, "PAPER", _PaperSource(paper))
    assert CHECKER.main([]) == 0


def test_main_rejects_checklist_unsupported_mapping_mutation(monkeypatch):
    paper = _mutate_checklist_state(
        CHECKER.PAPER.read_text(encoding="utf-8"),
        r"READ\s+unsupported",
        "Diagnostic only",
    )
    _assert_main_rejects(monkeypatch, paper)


def test_main_rejects_checklist_read_only_mapping_mutation(monkeypatch):
    paper = _mutate_checklist_state(
        CHECKER.PAPER.read_text(encoding="utf-8"),
        r"READ\s+supported;\s+TRANSFER\s+not\s+yet\s+tested",
        "Unresolved",
    )
    _assert_main_rejects(monkeypatch, paper)


def test_main_rejects_checklist_failed_mapping_mutation(monkeypatch):
    paper = _mutate_checklist_state(
        CHECKER.PAPER.read_text(encoding="utf-8"),
        r"TRANSFER\s+tested\s+and\s+failed",
        "Diagnostic only",
    )
    _assert_main_rejects(monkeypatch, paper)


def test_main_rejects_checklist_underpowered_mapping_mutation(monkeypatch):
    paper = _mutate_checklist_state(
        CHECKER.PAPER.read_text(encoding="utf-8"),
        r"TRANSFER\s+underpowered\s+or\s+inconclusive",
        "Withheld control",
    )
    _assert_main_rejects(monkeypatch, paper)


def test_main_rejects_checklist_coherence_mapping_mutation(monkeypatch):
    paper = _mutate_checklist_state(
        CHECKER.PAPER.read_text(encoding="utf-8"),
        r"Comparative\s+pass\s+with\s+coherence",
        "Withheld control",
    )
    _assert_main_rejects(monkeypatch, paper)


def test_concept_figure_routes_each_branch_to_exact_state():
    source = CHECKER.CONCEPT_FIGURE.read_text(encoding="utf-8")
    assert CHECKER.concept_edges(source) == CHECKER.EXPECTED_FIGURE_EDGES


def test_concept_figure_uses_ordered_vertical_decision_layers():
    source = CHECKER.CONCEPT_FIGURE.read_text(encoding="utf-8")
    positions = CHECKER.concept_positions(source)
    assert positions["candidate"][1] > positions["read"][1]
    assert positions["read"][1] > positions["transfer"][1]
    assert positions["transfer"][1] > positions["outcome"][1]
    assert positions["outcome"][1] > positions["unresolved"][1]
    assert positions["unresolved"][1] > positions["annotation"][1]
    state_x = [
        positions[name][0]
        for name in ("unresolved", "diagnostic", "withheld", "supported")
    ]
    assert state_x == sorted(state_x)
    assert all(right - left >= 3.8 for left, right in zip(state_x, state_x[1:]))
