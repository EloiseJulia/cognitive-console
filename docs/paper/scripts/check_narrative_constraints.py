"""Check paper-level narrative constraints for the IUI artifact-contract rewrite."""

from __future__ import annotations

import argparse
import re
import subprocess
from collections import Counter
from pathlib import Path


PAPER = Path(__file__).resolve().parents[1] / "main.tex"
RESULT_TERMS = re.compile(
    r"\b(no .*pass|failed-superiority|null|no method-model cell)\b", re.I
)
NUMERIC = re.compile(
    r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:\\?%|×|x)?"
)
NOT_BUT = re.compile(r"\bnot\b[^.!?\n]{0,180}\bbut\b", re.I)
INTERNAL = re.compile(
    r"\b[ED]-00\d+\b|valid_for_paper|(?:[\w.-]+/)+[\w.-]+\.(?:ya?ml|json|md)",
    re.I,
)
DISCLAIMER = re.compile(
    r"user (?:study|comprehension)|usability|reliance|disclaimer|"
    r"does not establish|not a (?:result|deployment)|post-hoc|exploratory|"
    r"not pre-registered|valid_for_paper|claim status",
    re.I,
)
NON_PROSE_ENVIRONMENTS = re.compile(
    r"\\begin\{(?:equation|align|figure|figure\*|table|table\*|tabular|enumerate|quote)\}"
)


def strip_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", text)


def environment(text: str, name: str) -> str:
    match = re.search(
        rf"\\begin\{{{name}\}}(.*?)\\end\{{{name}\}}", text, re.S
    )
    if not match:
        raise ValueError(f"missing {name} environment")
    return match.group(1).strip()


def prose(text: str) -> str:
    text = strip_comments(text)
    text = re.sub(r"\\(?:cite|ref|label|input|includegraphics)\{[^}]*\}", "", text)
    text = re.sub(r"\\[A-Za-z*]+(?:\[[^]]*\])?", "", text)
    text = text.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", text).strip()


def sentence_list(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose(text)) if s.strip()]


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def numeric_values(text: str) -> set[str]:
    clean = re.sub(r"\b[ED]-\d+\b", "", strip_comments(text))
    return {m.group(0) for m in NUMERIC.finditer(clean)}


def prose_paragraphs(text: str) -> list[tuple[int, str]]:
    """Return ordinary prose blocks with their starting source lines."""
    paragraphs: list[tuple[int, str]] = []
    for match in re.finditer(r"(?ms)(?:\A|\n\s*\n)(.*?)(?=\n\s*\n|\Z)", text):
        block = strip_comments(match.group(1)).strip()
        if not block or NON_PROSE_ENVIRONMENTS.search(block):
            continue
        if block.startswith(
            (
                r"\documentclass",
                r"\usepackage",
                r"\usetikzlibrary",
                r"\Declare",
                r"\newcolumntype",
                r"\AtBeginDocument",
                r"\setcopyright",
                r"\settopmatter",
                r"\renewcommand",
                r"\ccsdesc",
                r"\keywords",
                r"\title",
                r"\author",
                r"\affiliation",
                r"\email",
                r"\input",
                r"\bibliographystyle",
                r"\bibliography",
            )
        ):
            continue
        clean = re.sub(
            r"\\(?:section|subsection|paragraph|label)\{[^}]*\}", "", block
        ).strip()
        clean = prose(clean)
        if len(re.findall(r"\b[A-Za-z]{3,}\b", clean)) < 5:
            continue
        paragraphs.append((line_number(text, match.start(1)), clean))
    return paragraphs


def paragraph_opener(paragraph: str) -> str:
    words = re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)?", paragraph)
    return " ".join(words[:2])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Git revision used for numeric-value comparison")
    args = parser.parse_args()

    text = PAPER.read_text(encoding="utf-8")
    abstract = environment(text, "abstract")
    sentences = sentence_list(abstract)
    first_result = next(
        (index for index, sentence in enumerate(sentences, 1) if RESULT_TERMS.search(sentence)),
        None,
    )
    abstract_numbers = NUMERIC.findall(prose(abstract))

    registry_start = text.index(r"\section{Artifact Registry}")
    body = text[:registry_start]
    body_internal = list(INTERNAL.finditer(strip_comments(body)))
    not_but = list(NOT_BUT.finditer(prose(text)))

    captions = re.findall(r"\\caption\{(.*?)\}", strip_comments(text), re.S)
    caption_disclaimers = [caption for caption in captions if DISCLAIMER.search(caption)]

    scope_sentence = re.findall(
        r"no user study[^.]*comprehensibility[^.]*usability[^.]*"
        r"calibrated reliance[^.]*untested",
        prose(text),
        re.I,
    )
    paragraphs = prose_paragraphs(text)
    openers = [
        (line, paragraph_opener(paragraph))
        for line, paragraph in paragraphs
        if paragraph_opener(paragraph)
    ]
    opener_counts = Counter(opener for _, opener in openers)
    dense_openers = {
        opener: count for opener, count in opener_counts.items() if count > 4
    }
    consecutive_openers = [
        (line, opener)
        for (_, previous), (line, opener) in zip(openers, openers[1:])
        if opener == previous
    ]
    red_lines = {
        "missingness_bounds_cross_zero": "adversarial missingness bounds span zero" in prose(text),
        "other_three_not_rechecked": "other three cells were not format-rechecked" in prose(text),
        "skepticism_underpowered": bool(
            re.search(r"Skepticism[^.]*underpowered", prose(text), re.I)
        ),
        "no_user_study_once": len(scope_sentence) == 1,
    }

    print(f"Abstract sentences: {len(sentences)}")
    print(f"First null/failed-superiority sentence: {first_result}")
    print(f"Abstract numeric expressions: {len(abstract_numbers)} {abstract_numbers}")
    print(f"not-X-but-Y count: {len(not_but)}")
    for match in not_but:
        print(f"  {match.group(0)}")
    print(f"Body internal IDs/status/paths outside registry: {len(body_internal)}")
    for match in body_internal:
        print(f"  line {line_number(body, match.start())}: {match.group(0)}")
    print(f"Caption disclaimers: {len(caption_disclaimers)}")
    print(f"Scope red lines: {red_lines}")
    print(f"Over-dense two-word paragraph openers: {dense_openers}")
    print(f"Consecutive repeated paragraph openers: {len(consecutive_openers)}")
    for line, opener in consecutive_openers:
        print(f"  line {line}: {opener}")

    failures = []
    if first_result is None or first_result < 8:
        failures.append("abstract result appears before sentence 8")
    if len(abstract_numbers) > 3:
        failures.append("abstract contains more than three numeric expressions")
    if len(not_but) > 3:
        failures.append("more than three not-X-but-Y constructions")
    if body_internal:
        failures.append("internal identifiers/status/paths remain outside registry")
    if caption_disclaimers:
        failures.append("caption contains scope/disclaimer language")
    if not all(red_lines.values()):
        failures.append("scope red-line statement missing")
    if dense_openers:
        failures.append("a two-word paragraph opener appears more than four times")
    if consecutive_openers:
        failures.append("consecutive prose paragraphs repeat the same opener")

    if args.base:
        base = subprocess.run(
            ["git", "show", f"{args.base}:docs/paper/main.tex"],
            cwd=PAPER.parents[3],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
        candidate_without_registry = text[:registry_start]
        base_without_registry = base[: base.index(r"\section{Artifact Registry}")]
        removed = sorted(
            numeric_values(base_without_registry)
            - numeric_values(candidate_without_registry)
        )
        added = sorted(
            numeric_values(candidate_without_registry)
            - numeric_values(base_without_registry)
        )
        print(f"Quantitative values removed outside registry: {removed}")
        print(f"Quantitative values added outside registry: {added}")
        if removed or added:
            failures.append("paper-wide numeric value set drifted")

    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
