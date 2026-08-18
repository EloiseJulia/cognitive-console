# Hostile Audit — E-0017f Latent Behavioral Positive Control (Stolfo / Phi-3, Stage-2 TEST)

- **Auditor:** independent hostile audit session `audit-latentpc` (fresh, no-context, adversarial), 2026-08-18
- **Target:** `feature/latent-positive-control@41b6f9d` (run code `78db8d0`)
- **Experiment:** `E-0017f-phi3-official-stolfo-positive-control-stage2-test-once`
- **Artifact:** `results/latent_positive_control_phi_official_stage2_test/official_latent_positive_control_dev_results.json`
- **Verdict:** **TEST PASS is SOUND. No numerical BLOCKER.** MAJORs are paper-integration scope/wording + forking-path disclosure, not the number.

## Independent re-derivation from committed per-item arrays
- baseline `9/45 = 0.200`
- prompt `39/45 = 0.867`
- steer `19/45 = 0.422`
- primary `steer − baseline = +0.222222`
- item-cluster bootstrap B=10000, 98.33% CI = **[0.088889, 0.377778]** (matches artifact exactly)
- coherence `0.102290 <= 0.111595` → PASS
- `feature/latent-positive-control = 41b6f9d` confirmed to exist; run code `78db8d0` is an ancestor.
- **PASS verdict confirmed.**

## Robustness / sensitivity checks (all still clear zero)
- **Unique-key** (45 task rows but only 20 unique IFEval source keys): Δ=0.1958, CI [0.0792, 0.3208].
- **Whole-word** (official verifier is regex substring, IGNORECASE; no confidence/imputation found): Δ=0.200, CI [0.0444, 0.3778].
- **Truncation-excluded** (drop all rows hitting the 1024 cap; baseline 2/45, steer 3/45, prompt 0): n=40, Δ=0.225, CI [0.075, 0.400]. No truncation-artifact blocker.

## Ranked findings
### MAJOR — scope / paper wording currently unsafe
- `docs/paper/main.tex:584` still says "Because no latent behavioral positive control passes…" (now false).
- `main.tex:33,636` "predeclared positive control" refers to the B1 **prompt-level** control; must not be conflated with this **latent** control, and must not imply headline CAA/ITI × Qwen/Llama sensitivity.
- Minimal fix: "A Stolfo-validated Phi-3 keyword-existence latent steering positive control passes the same adjudicator, supporting adjudicator/procedure sensitivity **in that narrow setting**."

### MAJOR — forking-paths reviewer risk (NOT a TEST cherry-pick)
- Qwen absent from Stolfo official repo/paper (paper validates Phi-3, Gemma, Mistral); Gemma blocked by HF gated access (`gated:"manual"`); Phi-3 `gated:false`, MIT, revision matches.
- TEST freeze recorded before run (`docs/specs/latent-positive-control-prereg.md:145-159`; single candidate cell).
- Conclusion: not a TEST cherry-pick, **but the model fallback was not pre-registered before the Qwen failure**. Paper must disclose the full Qwen→Gemma→Phi path.

### MAJOR — n=45 rows / 20 unique keys
- Report "45 task rows / 20 source keys" + unique-key sensitivity (passes, see above).

### MINOR — official verifier is regex substring, not whole-word
- No confidence/imputation. Whole-word sensitivity still passes.

### UNVERIFIED — direction norms not persisted
- Code uses official `resid_post` hook and normalizes direction (`scripts/…:204,210`), but artifact does not store direction L2 norms. Add a norm summary for future auditability. Does not affect the verdict.

## Validation
- `python -m pytest -q tests\test_latent_positive_control.py` → 5 passed.

## Scope statement (what PASS licenses)
PASS licenses a **procedure-sensitivity** claim only: the frozen adjudicator + coherence gate + item-cluster bootstrap can certify a genuine, published latent control (Stolfo instruction-steering) on **Phi-3-mini + keyword-existence** — a different model and task than the headline. It does **not** validate assay sensitivity on Qwen/Llama at the three console axes, does **not** make those axes controllable, and does **not** revise the frozen 0/12 grid (E-0005/E-0006/E-0011).
