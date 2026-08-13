# REPORT — Prospective, Outcome-Blind POSITIVE CONTROL on a CONFOUND-FREE endpoint (frozen gate)

- **experiment_id:** `clean-pc-c27e9b4-20260813`
- **scientific_status:** `PENDING_HOSTILE_RESULT_AUDIT` — **`valid_for_paper=false`**. NOT blessed, NOT pushed, NOT merged.
- **branch:** `feature/positive-control-clean`
- **predeclaration commit (PRECEDES the result):** `f3e7c5a` — `docs/research/2026-08-13-clean-positive-control-predeclaration.md`
- **run code_commit:** `c27e9b4` (`scripts/run_clean_positive_control.py`; the exact code executed on the A800). The predeclaration commit `f3e7c5a` is this commit's parent → predeclaration provably precedes the run.
- **compute:** A800 `suzlab-a800`, **GPU3 only** (`CUDA_VISIBLE_DEVICES=3`, `NVIDIA A800 80GB PCIe`), bfloat16. In-process wall **532.0 s ⇒ 0.148 A800 GPU-hours** (process-lifetime upper bound ≤ 0.19 GPU-h; ≤ 0.5 GPU-h authorized).

## 1. What this run is (and is not)

A **prospective, outcome-blind positive control on the decision GATE**, on a **confound-free** endpoint. It asks whether the frozen comparator-bound gate — `adjudicate_c2b.cluster_bootstrap_ci` (B=10000, item-cluster, CI 1−0.05/3=0.98333, seed 20260723) + `axis_pass` (δ=0.05, coherence τ=1.5 / eps=0.02) — is **(a) satisfiable** by a genuine effect and **(b) discriminative** (rejects a null), on **FRESH** data, with everything predeclared **before** any generation.

It is **NOT** evidence for any steering/latent claim. It exercises the gate with a **PROMPT/instruction** effect (a strong format instruction vs a neutral baseline). See the scope caveat (§6).

## 2. Why a new endpoint (motivation)

The prior uncertainty-endpoint prospective control (`prospective-pc-efb6520-20260813`) was **DISCRIMINATIVE** (NEGATIVE correctly FAILED) but its **POSITIVE** arm **narrowly MISSED** PASS (mean_diff +0.1399, 98.333% CI [−0.0011, 0.2771]) due to a **confidence-parseability × truncation confound**: under the 64-token budget the strong uncertainty prompt truncated before emitting `Confidence: X%`, so only ~37% of strong-prompt samples parsed (vs ~81% neutral), inflating paired-diff variance. This run replaces the endpoint with a **confound-free** one (§3).

## 3. Confound-free endpoint & frozen protocol (predeclared, unchanged after seeing outcomes)

- **Endpoint (predeclared):** **prefix-compliance** — per-sample compliance = `1.0` iff the decoded reply, leading whitespace stripped, begins with the **exact, case-sensitive** marker `ANSWER:`, else `0.0`; per-item = mean over k=5. The scored signal is at the **START** of the reply → **not truncation-confounded**; no numeric value is parsed → **no parseability confound**; the instruction is a benign formatting directive → **non-harmful**.
- **Items:** 80 FRESH TriviaQA `rc.nocontext` validation items via the UNMODIFIED frozen `parse_uncertainty_rows`, drawn deterministically (`FRESH_SEED=20260814`) and **verified disjoint by item-id AND normalized-question-text hash** from the frozen E-0006 uncertainty pool (seed 0) and the E-0012 pool (seed 12/offset 500).
- **Split:** UNMODIFIED frozen `split_dev_test(dev_fraction=1/3, seed=20260723)` ⇒ **27 DEV / 53 TEST**; **TEST(53) evaluated only**.
- **Conditions (unsteered, α=0, layer=1) via the frozen `SteeredHFBackend.generate` primitive:** (i) prompt = strong format instruction ("reply MUST begin with the exact text ANSWER:"); (ii) baselineA = "Please answer the following question."; (iii) baselineB = same neutral text, independent seed. Generation identity: Qwen2.5-7B-Instruct, bfloat16, `temperature=0.7`, `do_sample=True`, `k=5`, `max_new_tokens=32` (predeclared; adequate and non-confounding). Per-(item,sample) seed uses the frozen `_call_seed` derivation.
- **Contrasts (through the UNMODIFIED frozen adjudicator):** POSITIVE = prompt−baselineA (expected PASS); NEGATIVE = baselineB−baselineA (expected FAIL). Both reported regardless.

## 4. Item-disjointness proof (verified in-run)

```
fresh_n = 80   e0006_n = 80   e0012_n = 80
id_intersection(fresh, E-0006)                     = []   (empty)
text_intersection(fresh, E-0006 ∪ E-0012)          = []   (empty)
```
Full sorted fresh `orig_id`s and question-text sha256 hashes, plus the E-0006 id set, are persisted in `clean_pc_result.json → disjointness_proof`. The run STOPS by construction if any intersection is non-empty.

## 5. Results (per-item prefix-compliance on 53 TEST items, k=5)

| condition | compliance rate | mean per-item outcome |
|---|---|---|
| (i) prompt `strong-format` | **1.000** | 1.0000 |
| (ii) baselineA (neutral) | **0.000** | 0.0000 |
| (iii) baselineB (neutral, indep seed) | **0.000** | 0.0000 |

| contrast | expected | mean_diff | CI(0.98333) | excl 0 | mean≥δ | coherence_ok | **PASS** |
|---|---|---|---|---|---|---|---|
| **POSITIVE** (prompt − baselineA) | PASS | **+1.0000** | [1.0000, 1.0000] | **yes** | yes | yes (deg 0.0003 ≤ 0.0226) | **True** |
| **NEGATIVE** (baselineB − baselineA) | FAIL | **0.0000** | [0.0000, 0.0000] | no | no | yes | **False** |

- **POSITIVE control PASSES** — a large (+1.0 ≥ δ), coherence-clean effect whose stringent Bonferroni 98.333% CI cleanly excludes 0 ⇒ the gate is **SATISFIABLE**.
- **NEGATIVE control correctly FAILS** (mean 0, CI [0,0] straddles 0) ⇒ the gate is **DISCRIMINATIVE** (rejects a null).
- **`gate_satisfiable_and_discriminative` = True** (POSITIVE PASS **and** NEGATIVE FAIL).

Coherence: all conditions are fluent (mean degeneracy ≈ 0.000–0.002); strong-prompt outputs are of the form `ANSWER: <answer>` (e.g. `ANSWER: THE EAGLES`), neutral outputs answer normally without the marker. The clean 1.0-vs-0.0 separation is genuine behavior, not a scoring artifact of truncation.

## 6. Interpretation & scope

- The gate is **demonstrated SATISFIABLE + DISCRIMINATIVE** on fresh, outcome-blind data with a fully predeclared, confound-free endpoint.
- **Scope caveat (predeclared):** this shows the gate accepts a **PROMPT/instruction** effect direction and rejects a null. It says **nothing** about whether a **latent/steering** signal can satisfy the gate. It is a positive control on the decision machinery, not evidence for the project's steering claims.

## 7. Artifacts & lineage

- `results/clean_pc_20260813/clean_pc_result.json` — adjudicated result + per-item outcomes + per-sample metadata (compliance/degeneracy/text_sha256) + disjointness proof + seeds/constants (in git).
- `results/clean_pc_20260813/run.log` — run stdout.
- `results/clean_pc_20260813/raw_generations.POINTER.md` — sha256 `90ddc78f…459455` + REPORT_STORE location of the full raw generations (with verbatim texts), stored OUTSIDE git.
- Registered: `docs/ledgers/experiment-registry.yaml` (`clean-pc-c27e9b4-20260813`, `valid_for_paper=false`, `PENDING_HOSTILE_RESULT_AUDIT`); `docs/ledgers/compute-ledger.md` (0.148 GPU-h).

## 8. Confirmations

- No frozen artifact touched (E-0005/6/11/13, `arm_full`, `data/e0006_uncertainty_baseline`, `e0006_uncertainty_baseline`, frozen `src/cognitive_console` modules). The two branch commits modify only `docs/research/...` (predeclaration) and `scripts/run_clean_positive_control.py`; `git diff main -- src` is empty. On the A800 host, `git status --porcelain` showed **NO tracked-file modification**; the recorded `dirty_tree=true` reflects only newly-created untracked output/helper files.
- No push, no merge, no bless. No tuning-to-pass; no arm/endpoint/scorer/threshold/CI/seed substitution after seeing outcomes; endpoint not swapped/retried. GPU3 only (GPUs 0–2 untouched).
