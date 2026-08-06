"""Check paper-level narrative constraints for the IUI artifact-contract rewrite."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


PAPER = Path(__file__).resolve().parents[1] / "main.tex"
ROOT = PAPER.parents[2]
RESULT_TERMS = re.compile(
    r"\b(no .*pass|failed-superiority|null|no method-model cell)\b", re.I
)
NUMERIC = re.compile(
    r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:\\?%|×|x)?"
)
MODEL_IDENTIFIER = re.compile(
    r"\b(?:Qwen\d+(?:\.\d+)*(?:-\d+B)?(?:-Instruct)?|"
    r"(?:Meta-)?Llama-\d+(?:\.\d+)*(?:-\d+B)?(?:-Instruct)?|CAA|ITI)\b",
    re.I,
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


def word_count(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z]+(?:-[A-Za-z]+)?\b", text))


def normalized_sentence(text: str) -> str:
    return " ".join(re.findall(r"[a-z]+", text.lower()))


def triad_candidates(text: str) -> list[str]:
    """Heuristic warning for list-like three-part prose, not a style gate."""
    candidates = []
    body = text.split(r"\appendix", 1)[0]
    for _, paragraph in prose_paragraphs(body):
        for sentence in sentence_list(paragraph):
            if (
                sentence.count(",") == 2
                and re.search(r",\s+(?:and|or)\s+", sentence, re.I)
                and not re.search(r"\d|\\", sentence)
                and word_count(sentence) <= 35
            ):
                candidates.append(sentence)
    return candidates


def verify_derived_summaries(abstract_text: str) -> dict[str, bool]:
    grid = json.loads(
        (ROOT / "results" / "arm_full" / "arm_matrix_summary.json").read_text(
            encoding="utf-8"
        )
    )
    aggregate = json.loads(
        (ROOT / "results" / "E-0011" / "multiseed_c2_aggregate.json").read_text(
            encoding="utf-8"
        )
    )
    axis_tests = sum(len(cell["axis_passes"]) for cell in grid["cells"])
    axis_passes = sum(
        sum(bool(value) for value in cell["axis_passes"].values())
        for cell in grid["cells"]
    )
    seed_records = aggregate["seed_records"]
    seed_no_pass = sum(
        record["arm_verdict"] == "NON_TRANSFER_GENERALIZED"
        and not record["any_cell_has_pass"]
        for record in seed_records
    )
    clean = prose(abstract_text)
    return {
        "zero_of_twelve_matches_artifact": axis_tests == 12
        and axis_passes == 0
        and "0 of 12 axis-cell passes" in clean,
        "five_of_five_matches_artifact": len(seed_records) == 5
        and seed_no_pass == 5
        and "all five preserve that verdict" in clean,
        "shared_pool_caveat_same_sentence": bool(
            re.search(
                r"previously observed seed[^.]*four prospectively frozen new "
                r"DEV/TEST split seeds[^.]*all five[^.]*shared item pool",
                clean,
                re.I,
            )
        ),
    }


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def numeric_values(text: str) -> set[str]:
    clean = re.sub(r"\b[ED]-\d+\b", "", strip_comments(text))
    return {m.group(0) for m in NUMERIC.finditer(clean)}


def abstract_numeric_expressions(text: str) -> list[str]:
    clean = MODEL_IDENTIFIER.sub("", prose(text))
    return NUMERIC.findall(clean)


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
    abstract_numbers = abstract_numeric_expressions(abstract)

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
    all_sentences = sentence_list(text)
    sentence_lengths = [word_count(sentence) for sentence in all_sentences]
    short_sentences = [n for n in sentence_lengths if n <= 7]
    long_sentences = [n for n in sentence_lengths if n >= 35]
    middle_sentences = [n for n in sentence_lengths if 12 <= n <= 24]
    middle_ratio = len(middle_sentences) / len(sentence_lengths)
    remain_count = len(re.findall(r"\bremains?\b", prose(text), re.I))
    triads = triad_candidates(text)
    base_triad_count = None
    repeated_sentences = {
        sentence: count
        for sentence, count in Counter(
            normalized_sentence(sentence) for sentence in all_sentences
        ).items()
        if sentence and count > 2
    }
    paragraph_length_warnings = []
    for line, paragraph in paragraphs:
        lengths = [word_count(sentence) for sentence in sentence_list(paragraph)]
        if len(lengths) >= 2 and (not any(n <= 7 for n in lengths) or not any(n >= 35 for n in lengths)):
            paragraph_length_warnings.append((line, lengths))
    derived = verify_derived_summaries(abstract)
    red_lines = {
        "missingness_bounds_cross_zero": "adversarial missingness bounds span zero" in prose(text),
        "other_three_not_rechecked": "other three cells were not format-rechecked" in prose(text),
        "skepticism_underpowered": bool(
            re.search(r"Skepticism[^.]*underpowered", prose(text), re.I)
        ),
        "no_user_study_once": len(scope_sentence) == 1,
    }

    print(f"Abstract sentences: {len(sentences)}")
    print(f"Abstract numeric expressions: {len(abstract_numbers)} {abstract_numbers}")
    print(f"Derived abstract summaries: {derived}")
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
    print(
        "Sentence lengths: "
        f"n={len(sentence_lengths)}, <=7={len(short_sentences)}, "
        f">=35={len(long_sentences)}, 12-24={len(middle_sentences)} "
        f"({middle_ratio:.1%})"
    )
    print(f"Triad-like sentences (warning heuristic): {len(triads)}")
    print(f"remain/remains count: {remain_count}")
    print(f"Repeated normalized sentences >2: {repeated_sentences}")
    print(
        "Paragraphs missing short/long sentence variation "
        f"(warning, multi-sentence only): {len(paragraph_length_warnings)}"
    )
    for line, lengths in paragraph_length_warnings[:20]:
        print(f"  line {line}: sentence lengths {lengths}")

    failures = []
    warnings = []
    if len(abstract_numbers) < 2:
        failures.append("abstract contains fewer than two numeric expressions")
    if not all(derived.values()):
        failures.append("abstract derived summaries do not match committed artifacts")
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
    if "—" in text:
        failures.append("em dash present")
    if remain_count > 10:
        failures.append("remain/remains appears more than ten times")
    if repeated_sentences:
        failures.append("a complete normalized sentence appears more than twice")
    if middle_ratio >= 0.40:
        warnings.append("12-24-word sentence ratio is at or above the 40% style target")
    if len(short_sentences) < max(1, len(sentence_lengths) // 5):
        warnings.append("fewer than roughly one in five sentences has seven words or fewer")
    if not long_sentences:
        warnings.append("no sentence has 35 or more words")
    if triads:
        warnings.append("triad-like sentence heuristic found list-like prose; review manually")
    if paragraph_length_warnings:
        warnings.append("some multi-sentence paragraphs lack both short and long sentence variation")

    if args.base:
        base = subprocess.run(
            ["git", "show", f"{args.base}:docs/paper/main.tex"],
            cwd=PAPER.parents[3],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout
        base_triad_count = len(triad_candidates(base))
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
        reduction = 1 - (len(triads) / base_triad_count) if base_triad_count else 0
        print(
            f"Triad-like prose vs base: {len(triads)}/{base_triad_count} "
            f"({reduction:.1%} reduction)"
        )
        if base_triad_count and len(triads) > base_triad_count * 0.6:
            warnings.append("triad-like prose has not fallen by roughly half from base")

    for warning in warnings:
        print(f"WARNING: {warning}")
    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
