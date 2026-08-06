import importlib.util
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
