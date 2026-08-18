"""Prepare non-GPU frozen manifests for the C2b composition preregistration.

This script does not generate model outputs. It only:
1. loads the frozen headline best-prompt winners from existing E-0005/E-0006
   result JSON,
2. reconstructs the headline TEST item ids from the frozen C2b split, and
3. writes fresh DEV/TEST item and prompt manifests for the composition arm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from cognitive_console.eval import c2b_tasks
from cognitive_console.experiments import adjudicate_c2b as adj


AXES = ("deliberation", "skepticism", "uncertainty_awareness")
ORDINARY_PROMPTS = {
    "deliberation": "Please think carefully before answering.",
    "skepticism": "Please check the claim carefully before answering.",
    "uncertainty_awareness": "Please state your confidence and mention if you are unsure.",
}
SOURCE_PROVENANCE = {
    "deliberation": {
        "source_loader": "openai/gsm8k main test",
        "source_dataset_revision": "740312add88f781978c0658806c59bc2815b9866",
        "source_dataset_fingerprint": "59ec1b7f9357c7a2",
    },
    "skepticism": {
        "source_loader": "truthfulqa/truthful_qa multiple_choice validation",
        "source_dataset_revision": "741b8276f2d1982aa3d5b832d3ee81ed3b896490",
        "source_dataset_fingerprint": "8ba81adae744fd06",
    },
    "uncertainty_awareness": {
        "source_loader": "mandarjoshi/trivia_qa rc.nocontext validation",
        "source_dataset_revision": "0f7faf33a3908546c6fd5b73a660e0f8ff173c2f",
        "source_dataset_fingerprint": "b024cd028213e383",
    },
}
TARGET_DEV = 200
TARGET_TEST = 400
COMPOSITION_SPLIT_SEED = 20260818
HEADLINE_SPLIT_SEED = 20260723


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def item_hash(item: Dict[str, Any]) -> str:
    payload = {k: v for k, v in item.items() if k != "split"}
    return sha256_text(canonical_json(payload))


def load_headline_winners(path: Path) -> Dict[str, Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    winners: Dict[str, Dict[str, Any]] = {}
    for row in data.get("axes", []):
        axis = str(row["axis"])
        dev = row.get("dev_selection") or {}
        pid = dev.get("best_prompt_id")
        ptext = dev.get("best_prompt_text")
        if not pid or not ptext:
            raise RuntimeError(f"missing headline winner for axis {axis} in {path}")
        winners[axis] = {
            "prompt_id": str(pid),
            "text": str(ptext),
            "source_result": str(path.as_posix()),
            "source_experiment": "E-0005/E-0006 headline frozen DEV winner",
        }
    missing = sorted(set(AXES) - set(winners))
    if missing:
        raise RuntimeError(f"headline winners missing axes: {missing}")
    return winners


def headline_test_ids(axis: str, all_items: List[Dict[str, Any]]) -> List[str]:
    cap = adj.N_ITEMS_BY_AXIS[axis]
    headline_items = all_items[:cap]
    ids = [str(it["id"]) for it in headline_items]
    split = adj.split_dev_test(ids, dev_fraction=adj.DEV_FRACTION, seed=HEADLINE_SPLIT_SEED)
    return list(split.test_ids)


def composition_split_ids(ids: List[str]) -> tuple[List[str], List[str]]:
    split = adj.split_dev_test(ids, dev_fraction=TARGET_DEV / max(1, len(ids)), seed=COMPOSITION_SPLIT_SEED)
    dev_ids = list(split.dev_ids)[:TARGET_DEV]
    remaining_test = [i for i in split.test_ids if i not in set(dev_ids)]
    test_ids = remaining_test[:TARGET_TEST]
    return dev_ids, test_ids


def load_all_axis_items(axis: str) -> List[Dict[str, Any]]:
    task = c2b_tasks.load_c2b_task(axis, use_fixture=False)
    seen: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for item in task.items:
        iid = str(item["id"])
        if iid in seen:
            continue
        seen.add(iid)
        unique.append(dict(item))
    return unique


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(canonical_json(row) + "\n")


def main() -> int:
    root = repo_root()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headline-results",
        default=str(root / "results" / "arm_full" / "cell_caa__qwen2.5-7b" / "c2b_adjudication_results.json"),
    )
    parser.add_argument(
        "--item-manifest",
        default=str(root / "docs" / "specs" / "c2b-composition-item-manifest.jsonl"),
    )
    parser.add_argument(
        "--prompt-manifest",
        default=str(root / "docs" / "specs" / "c2b-composition-prompt-manifest.yaml"),
    )
    args = parser.parse_args()

    headline_path = Path(args.headline_results)
    winners = load_headline_winners(headline_path)
    headline_source_rel = headline_path.resolve().relative_to(root).as_posix()
    for winner in winners.values():
        winner["source_result"] = headline_source_rel

    item_rows: List[Dict[str, Any]] = []
    axis_summaries: Dict[str, Any] = {}
    for axis in AXES:
        all_items = load_all_axis_items(axis)
        headline_test = set(headline_test_ids(axis, all_items))
        fresh = [it for it in all_items if str(it["id"]) not in headline_test]
        fresh_ids = [str(it["id"]) for it in fresh]
        dev_ids, test_ids = composition_split_ids(fresh_ids)
        by_id = {str(it["id"]): it for it in fresh}
        for split_name, split_ids in (("DEV", dev_ids), ("TEST", test_ids)):
            for iid in split_ids:
                item = by_id[iid]
                item_rows.append(
                    {
                        "axis": axis,
                        "split": split_name,
                        "item_id": iid,
                        "item_sha256": item_hash(item),
                        **SOURCE_PROVENANCE[axis],
                        "headline_test_overlap": iid in headline_test,
                    }
                )
        axis_summaries[axis] = {
            "source_unique_items": len(all_items),
            "headline_test_excluded": len(headline_test),
            "fresh_unique_after_headline_test_exclusion": len(fresh),
            "target_dev": TARGET_DEV,
            "target_test": TARGET_TEST,
            "realized_dev": len(dev_ids),
            "realized_test": len(test_ids),
            "cap_to_ceiling_applied": len(dev_ids) < TARGET_DEV or len(test_ids) < TARGET_TEST,
            "headline_test_overlap_count": 0,
        }

    write_jsonl(Path(args.item_manifest), item_rows)

    prompt_manifest = {
        "manifest_id": "c2b-composition-prompt-manifest",
        "status": "FROZEN_BY_MANAGER_2026-08-18",
        "ordinary_prompt_semantics": (
            "plain-instruction everyday-user proxy; not validated as representative "
            "of real novices, which remains a human-anchor threat"
        ),
        "strong_prompt_policy": "reuse headline frozen best-of-set DEV winner id; no reselection",
        "headline_results_source": headline_source_rel,
        "axes": {},
    }
    for axis in AXES:
        prompt_manifest["axes"][axis] = {
            "ordinary": {
                "prompt_id": f"{axis}-ordinary-plain-v1",
                "text": ORDINARY_PROMPTS[axis],
                "sha256": sha256_text(ORDINARY_PROMPTS[axis]),
            },
            "strong": {
                **winners[axis],
                "sha256": sha256_text(winners[axis]["text"]),
            },
        }
    Path(args.prompt_manifest).write_text(
        yaml.safe_dump(prompt_manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    summary = {
        "item_manifest": str(Path(args.item_manifest).as_posix()),
        "prompt_manifest": str(Path(args.prompt_manifest).as_posix()),
        "split_seed": COMPOSITION_SPLIT_SEED,
        "headline_test_seed": HEADLINE_SPLIT_SEED,
        "axis_summaries": axis_summaries,
        "total_rows": len(item_rows),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
