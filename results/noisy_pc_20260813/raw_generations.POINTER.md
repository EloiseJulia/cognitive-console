# RAW GENERATIONS POINTER — noisy positive control (`noisy-pc-f16ce51-20260813`)

The full raw generations (795 records = 3 conditions × 53 TEST items × 5 samples,
including the decoded model text for every sample) are **NOT committed to git**
(REPORT_STORE policy for large raw artifacts). They live in REPORT_STORE:

- **REPORT_STORE path:** `~/reports/cognitive-console/noisy_pc_20260813/raw_generations.jsonl`
  (Windows: `%USERPROFILE%\reports\cognitive-console\noisy_pc_20260813\raw_generations.jsonl`)
- **sha256:** `0b29eebf45eec37d3cc7507f12d19246ce20cfb8ff92eb4e1a404c8e549aad8d`
- **records:** 795 (JSONL; fields: condition, item_id, orig_id, sample_index,
  compliance, token_count, degeneracy, text_sha256, text)

The committed `noisy_pc_result.json` contains the same per-sample compliance /
token_count / degeneracy / text_sha256 (text stripped), so every reported number is
reproducible from git; the pointer file preserves the full decoded text for audit.
