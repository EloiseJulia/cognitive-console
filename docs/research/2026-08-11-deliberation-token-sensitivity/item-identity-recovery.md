# E-0006 deliberation item-identity recovery

Status: **ordered pool/TEST index IDs proven; item payload reconstructed**

Recovery did not inspect per-item outcomes.

1. Historical commit `d20ccedf3756f267a4b9325abd2623c4e7c46335`
   generated GSM8K IDs by test-split row index, took the first 60 rows, sorted
   IDs before the seeded DEV/TEST split, and included all axis item-ID sets in
   `_config_fingerprint`.
2. Reconstructing IDs `gsm8k-test-00000`…`00059`, the frozen seed and all other
   recorded arguments reproduces all four retained fingerprints exactly:
   `433c5772c8ede7f8`, `861d5b5f8773c6f0`, `2d1749bdc7089f83`,
   `d39efbeac006dac5`.
3. The resulting sorted 40 TEST IDs are locked in `e0006-item-identity.json`.
4. No surviving original remote cache or historical item-payload hash was
   available. The GSM8K Hub revision current at the 2026-07-24 run is pinned as
   `740312add88f781978c0658806c59bc2815b9866`; its data files had not changed
   since the 2024 parquet conversion.

Therefore E-0017 may say **recovered historical TEST index IDs on a pinned
reconstructed payload**, not unconditionally “the exact same historical item
bytes.” Exact 64-token per-item outcome reproduction remains a mandatory
validity gate; failure is `INVALID_64_NONREPRODUCTION`, never a cap effect.
