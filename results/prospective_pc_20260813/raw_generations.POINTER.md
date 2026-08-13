# External raw-generations pointer (REPORT_STORE)

The full raw per-sample generations (with model output texts) for this run are
stored OUTSIDE git per `<REPORT_STORE>` (AGENTS.md §1), because they are large
model-output text.

- **filename:** `raw_generations.jsonl`
- **sha256:** `dd98123fabf91524e81ebb90c197539f0c275608fb7002b62f6f4ea2e43974ca`
- **records:** 795 (53 TEST items × 3 conditions × k=5 samples)
- **external location:** `~/reports/cognitive-console/prospective_pc_20260813/raw_generations.jsonl`
  (local machine REPORT_STORE); a byte-identical copy also remains on the A800
  host at `~/cc_l0/pc_run/results/prospective_pc_20260813/raw_generations.jsonl`
  until host cleanup.
- **schema (per line):** `{condition, item_id, orig_id, sample_index, confidence_parsed,
  correct, one_minus_brier, degeneracy, text_sha256, text}`.

The per-sample metadata (everything except the raw `text`) is ALSO embedded in
`prospective_pc_result.json` under `conditions.<cond>.raw`, so the adjudicated
result is fully reconstructible from the in-git artifact; the external file only
adds the verbatim generation texts (referenced by `text_sha256`).
