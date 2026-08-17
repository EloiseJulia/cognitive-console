"""Generate simulated-novice prompt candidates from licensed few-shot anchors.

This creates the prompt set only. It does not run any C2b outcome generation and
must be committed/frozen before the comparator arm is executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from cognitive_console.lineage import git_commit, utcnow

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
AXES = ("deliberation", "skepticism", "uncertainty_awareness")
AXIS_BRIEFS = {
    "deliberation": (
        "Write a short instruction a non-expert user might put before a math or "
        "reasoning question when they want the assistant to slow down, check the "
        "work, and give the final numeric answer."
    ),
    "skepticism": (
        "Write a short instruction a non-expert user might put before a multiple-"
        "choice truthfulness question when they want the assistant not to accept "
        "a shaky premise and to pick the best answer carefully."
    ),
    "uncertainty_awareness": (
        "Write a short instruction a non-expert user might put before a question "
        "when they want the assistant to answer and include an honest confidence "
        "percentage at the end."
    ),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _render_instruction(axis: str, few_shots: List[Dict[str, object]], index: int, n: int) -> str:
    examples = "\n".join(f"- {row['text']}" for row in few_shots)
    return (
        "You are generating candidate instruction prefixes for an experiment.\n"
        "Use the examples only for casual novice wording style, not for content.\n"
        "Few-shot examples of ordinary user wording:\n"
        f"{examples}\n\n"
        f"Target axis: {axis}\n"
        f"Task: {AXIS_BRIEFS[axis]}\n\n"
        "Return exactly one candidate instruction prefix. Requirements:\n"
        "- one or two sentences only;\n"
        "- plain everyday English, like a novice user;\n"
        "- no numbering, no bullets, no quotes, no explanation;\n"
        "- do not include any answer to a task item;\n"
        "- do not mention this experiment, axes, latent steering, or prompts.\n"
        f"Candidate {index} of {n}:"
    )


def _clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:text)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        text = lines[0]
    text = re.sub(r"^(candidate\s*\d+\s*[:.)-]\s*)", "", text, flags=re.I).strip()
    text = re.sub(r"^(prompt|instruction)\s*[:.)-]\s*", "", text, flags=re.I).strip()
    text = text.strip(" \"'“”")
    return re.sub(r"\s+", " ", text)


def _validate_prompt(axis: str, text: str, seen: set[str]) -> None:
    low = text.lower()
    if not (20 <= len(text) <= 260):
        raise ValueError(f"{axis}: prompt length outside [20,260]: {text!r}")
    forbidden = ["latent", "steering", "axis", "experiment", "candidate prompt"]
    if any(tok in low for tok in forbidden):
        raise ValueError(f"{axis}: generated prompt leaks experiment wording: {text!r}")


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fewshot", default=str(_REPO / "data" / "novice_prompt_sources" / "oasst1_fewshot_20260817.json"))
    ap.add_argument("--out", default=str(_REPO / "results" / "novice_prompt_comparator_20260817" / "novice_prompt_set.json"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--revision", default=DEFAULT_REVISION)
    ap.add_argument("--seed", type=int, default=20260817)
    ap.add_argument("--n-per-axis", type=int, default=16)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--top-p", type=float, default=0.9)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    ap.add_argument("--cache-dir", default=None)
    args = ap.parse_args(argv)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    fewshot_path = Path(args.fewshot)
    fewshot_doc = json.loads(fewshot_path.read_text(encoding="utf-8"))
    few_shots = list(fewshot_doc["few_shot_examples"])

    tokenizer = AutoTokenizer.from_pretrained(
        args.model, revision=args.revision, cache_dir=args.cache_dir, trust_remote_code=False
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        revision=args.revision,
        cache_dir=args.cache_dir,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        trust_remote_code=False,
    )
    model.eval()

    axes: Dict[str, List[Dict[str, object]]] = {}
    generation_instruction_full: Dict[str, str] = {}
    seen: set[str] = set()
    with torch.inference_mode():
        for axis in AXES:
            axes[axis] = []
            for i in range(1, int(args.n_per_axis) + 1):
                prompt = _render_instruction(axis, few_shots, i, int(args.n_per_axis))
                generation_instruction_full.setdefault(axis, prompt)
                messages = [{"role": "user", "content": prompt}]
                rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = tokenizer(rendered, return_tensors="pt").to(model.device)
                torch.manual_seed(int(args.seed) + 1000 * AXES.index(axis) + i)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(int(args.seed) + 1000 * AXES.index(axis) + i)
                output = model.generate(
                    **inputs,
                    do_sample=True,
                    temperature=float(args.temperature),
                    top_p=float(args.top_p),
                    max_new_tokens=int(args.max_new_tokens),
                    pad_token_id=tokenizer.eos_token_id,
                )
                decoded = tokenizer.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
                text = _clean(decoded)
                _validate_prompt(axis, text, seen)
                duplicate_of_prior = text in seen
                seen.add(text)
                axes[axis].append({
                    "prompt_id": f"novice-{axis}-{i:02d}",
                    "text": text,
                    "raw_generation": decoded,
                    "seed": int(args.seed) + 1000 * AXES.index(axis) + i,
                    "duplicate_of_prior": duplicate_of_prior,
                })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utcnow(),
        "code_commit": git_commit(str(_REPO)),
        "valid_for_paper": False,
        "anchor_calibration_gate": "NOT passed; exploratory only",
        "threat": "AI-generated novice prompts are not validated against real novices.",
        "generator": {
            "model": args.model,
            "revision": args.revision,
            "temperature": float(args.temperature),
            "top_p": float(args.top_p),
            "max_new_tokens": int(args.max_new_tokens),
            "seed": int(args.seed),
            "n_per_axis": int(args.n_per_axis),
        },
        "source_corpus": fewshot_doc["source_corpus"],
        "few_shot_examples": few_shots,
        "fewshot_file": str(fewshot_path.relative_to(_REPO)).replace("\\", "/"),
        "fewshot_file_sha256": _sha256(fewshot_path),
        "generation_instruction_full": generation_instruction_full,
        "axes": axes,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
