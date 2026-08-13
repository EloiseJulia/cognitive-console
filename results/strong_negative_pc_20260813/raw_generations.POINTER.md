# RAW GENERATIONS POINTER — strong-vs-strong′ positive control (`strong-negative-pc-c839e1c-20260813`)

The full raw generations (795 records = 3 conditions × 53 TEST items × 5 samples,
including the decoded model text and per-row `base_seed`, `call_seed`, and
`finish_reason` for every sample) are now archived in this directory as
`raw_generations.jsonl`, copied from the A800 REPORT_STORE mirror on 2026-08-13.

- **REPORT_STORE path (Windows):**
  `%USERPROFILE%\reports\cognitive-console\strong_negative_pc_20260813\raw_generations.jsonl`
- **REPORT_STORE path (A800 host mirror):**
  `~/reports/cognitive-console/strong_negative_pc_20260813/raw_generations.jsonl`
- **sha256:** `08025f4890fa197c5d943380799562565698da33c0eaea8b6601f3ee79a363bf`
- **records:** 795 (JSONL; fields: condition, item_id, orig_id, sample_index,
  base_seed, call_seed, compliance, token_count, finish_reason, n_new_tokens_true,
  hit_budget, degeneracy, text_sha256, text)

The committed `strong_negative_pc_result.json` contains the same per-sample
compliance / token_count / finish_reason / seeds / degeneracy / text_sha256 (decoded
text stripped), so every reported number is reproducible from git; this pointer
preserves the full decoded text for audit.
