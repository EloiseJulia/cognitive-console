# Reusable Methodology Asset for Latent-vs-Prompt Behavioral Control Reality Checks

Status: draft contribution candidate for Route (b), pure-model paper.

Scope guard: all positive/negative statements below are scoped to **two model families (Qwen2.5-7B-Instruct, Llama-3-8B-Instruct), two naive off-the-shelf mean-difference-style steering families (CAA, ITI), and the frozen adjudication protocols** unless explicitly marked otherwise. This is **not** an impossibility theorem and does **not** cover trained/optimized steering methods. The robustness arm `prereg-robustness-mechanism-arm` is now **EXECUTED** and generalized the negative across the tested 2×2 grid (`E-0006`); the off-manifold mechanism arm returned a valid null (`E-0007`), so mechanism remains open.
Evidence tags use: `E-0003`, `E-0005`, `E-0006`, `E-0007`, `prereg-c2b-adjudication`, `prereg-robustness-mechanism-arm`, `prereg-ood-capture`, and critic findings (`R1/R2/R3`).

---

## 1) Frozen adjudication protocol as a reusable methodological contribution

### 1.1 Protocol kernel (what is frozen)

The reusable unit is a **frozen adjudication protocol** for testing whether latent steering delivers behavioral gains beyond a strong prompt ceiling:

1. Define per-axis behavioral outcomes with real headroom (not lexical proxies).
   - deliberation: accuracy
   - skepticism: false-premise rejection rate
   - uncertainty: per-item `(1 - Brier)` (ECE descriptive only)
   **Source:** `prereg-c2b-adjudication` §1.

2. Use a **DEV/TEST split** per axis. Select both best prompt and steering strength alpha only on DEV; adjudicate only on disjoint TEST.
   **Source:** `prereg-c2b-adjudication` §1, §2, §5.

3. Compare steering vs prompt with **paired item-cluster bootstrap** on TEST differences `d_i = steer_i - prompt_i`, with Bonferroni correction across axes.
   - CI level: `1 - 0.05/3 = 98.33%`
   - Bootstrap: item-level clusters, `B >= 10000`
   **Source:** `prereg-c2b-adjudication` §4, §5.

4. Require three simultaneous pass conditions per axis:
   - corrected CI excludes 0
   - point estimate `mean(d) >= delta`
   - coherence gate passes
   with `delta = 0.05` and pre-registered coherence threshold.
   **Source:** `prereg-c2b-adjudication` §4, §5.

5. Aggregate to a three-tier verdict (`STRONG GO`, `CONDITIONAL GO`, `KILL`) based on number of passing axes.
   **Source:** `prereg-c2b-adjudication` §4.

6. Fix per-axis sample sizes before run (`N=60/60/80`, `k=5` here), and treat all post-freeze criterion edits as invalid.
   **Source:** `prereg-c2b-adjudication` §5, §6; `E-0005`.

### 1.2 Why this design reduces researcher degrees of freedom and HARKing

This protocol closes common flexibility channels:

- **Selection bias control:** alpha and best prompt are both chosen on DEV, not TEST, avoiding asymmetric "best-of-many" inflation.
  **Source:** `prereg-c2b-adjudication` §1, §4.
- **Comparator fairness:** prompt and latent channels share the same task pool and paired comparison unit (item), reducing cross-sample confounds.
  **Source:** `prereg-c2b-adjudication` §2, §4.
- **Multiplicity control:** Bonferroni family-wise control across axes lowers false positives from multi-axis fishing.
  **Source:** `prereg-c2b-adjudication` §4.
- **Practical-significance guard:** delta threshold blocks trivially nonzero wins from being overclaimed.
  **Source:** `prereg-c2b-adjudication` §5.
- **Quality guard:** coherence gate blocks wins that come from degenerate output regimes rather than usable behavior.
  **Source:** `prereg-c2b-adjudication` §3, §5.
- **Freeze discipline:** explicit pre-run freeze and immutable verdict rule prevent post-hoc criterion rewrites.
  **Source:** `prereg-c2b-adjudication` §6; `E-0005`.

### 1.3 Portability recipe (how others can reuse it)

To transfer this protocol to another axis/model/method:

1. Keep the adjudication skeleton fixed (DEV/TEST, paired cluster bootstrap, multiplicity correction, coherence gate, three-tier verdict).
2. Replace only axis-specific outcome functions and pre-registered `delta` in comparable units.
3. Re-freeze per-axis `N`, `k`, alpha grid, and coherence metric definition before seeing outcomes.
4. Report scope line in headline claims: model families, steering families, protocol version, and whether the method is naive/off-the-shelf or trained/optimized.
5. If method/model families change beyond the frozen 2×2 grid, treat them as a new adjudication package rather than retroactive reinterpretation.

This is the intended reusable "negative-result instrument" contribution, directly addressing "so what / method not tuned" risks by making failure claims auditable and portable across labs.
**Critic alignment:** `R3-M2`, `R2-B1`, `R2-M2`, `R1-F1`.

---

## 2) Latent control failure taxonomy (evidence-marked)

| Failure class | Observable symptom | Evidence status | Plausible mechanism | Diagnostic signal | Deployment meaning |
|---|---|---|---|---|---|
| **F1. Legible-but-non-transfer facade** | Axis is representationally legible, but steering does not beat best prompt behavior | **Supported in tested scope:** `E-0003` (legibility on 3/4 Qwen axes) + `E-0005`/`E-0006` (all 4 method×model cells 0/3 behavioral pass) | Behavioral policy may not be parameterized by that single linear control coordinate | Positive C1-style legibility plus null/negative paired `d_i` on adjudication | Treat latent direction as a diagnostic probe, not production control |
| **F2. Calibration backfire under steering** | Uncertainty/calibration axis worsens under steering | **Supported/generalized in tested 2×2:** `E-0005` (Qwen×CAA uncertainty mean(d) = -0.228, CI excludes 0) + `E-0006` (all 4 cells negative, CI excludes 0) | **Mechanism open:** distance-based off-manifold account was directly tested and not supported (`E-0007`) | Negative paired effect concentrated on calibration metrics across method×model cells | For calibration-facing products, do not deploy naive CAA/ITI steering as a trust-control primitive |
| **F3. Coherence-fragility corridor** | Higher steering strength risks coherence collapse or forces conservative usable alpha | **Instrumented but not triggered in tested cells:** coherence gate exists by design (`prereg-c2b`, robustness prereg); E-0005/E-0006 report coherence ok, so this is a guardrail rather than observed failure here | Steering may enter unusable output regimes, but this run's calibration harm was not explained by the tested off-manifold distance metric (`E-0007`) | Coherence diagnostics worsen faster than target metric improves | If coherence deteriorates before meaningful gain, stop latent route and keep prompt-only |
| **F4. Layer-sensitive instability** | Axis effect depends strongly on layer choice | **Supported in-scope:** `E-0003` notes layer sensitivity (e.g., deliberation layer-16 CI crossing); `E-0006` independently re-derived per-model layers/α | Axis is distributed/nonlinear; single-layer extraction under-specifies control geometry | Large variance or sign/strength shifts across nearby layers | Any deployment must include layer sensitivity sweeps and stability checks; otherwise high fragility |
| **F5. Axis extraction degeneration** | Extracted direction overshoots or fails to encode intended construct | **Supported in-scope:** focus axis overshoot/no facade in `E-0003`; focus dropped in prereg; robustness conclusions are limited to the three adjudicated axes | Target construct not linearly captured by current extraction objective/data | Ratio/pathology diagnostics show no valid facade regime | Exclude axis from control claims; redesign axis definition before any deployment |

Interpretation boundary: F1-F5 are currently a **method-scoped operational taxonomy**, not universal laws of latent control.

---

## 3) When-NOT-to-deploy latent control: operational decision checklist

This checklist turns the taxonomy into product/engineering decisions.

### 3.1 Hard no-go triggers (for naive CAA/ITI-like steering in this tested scope)

Do **not** deploy latent control as a user-facing control feature if any of the following holds:

1. Target is calibration/uncertainty expression and adjudication shows negative paired effect (as in `E-0005` and generalized in `E-0006`).
2. Increasing intervention strength improves target metric only while failing coherence gate or causing degeneration.
3. Axis is extraction-degenerate (no stable facade signal, overshoot pathologies).
4. Legibility is present but paired adjudication repeatedly yields null/negative transfer.

### 3.2 Prompt-vs-latent decision flow

1. Run frozen adjudication on the intended axis and product objective.
2. If axis fails pass criteria, default to prompt/channel-only control for deployment.
3. If axis passes but is layer/coherence fragile, keep latent control as internal analyst tooling, not end-user control.
4. Treat `E-0006` as a scoped 2×2 warning, not deployment clearance: promote to user-facing latent control only after product-specific adjudication passes under the intended model/method and any stronger/trained/optimized steering is tested in a new preregistered package.

### 3.3 What this contributes beyond one negative run

The contribution is a **decision discipline**: teams can avoid shipping brittle latent controls by using a frozen adjudication and explicit no-go criteria, while still reporting honest scoped negatives as cumulative knowledge. The executed robustness arm shows the negative is not a single CAA×Qwen accident, but the scope remains exactly the tested 2 model families × 2 naive steering families.
This directly answers the "method not tuned / so what" challenge by turning failures into reusable evaluation infrastructure rather than narrative-only conclusions, without claiming a universal limit on latent control.
**Critic alignment:** especially `R3-M2`, plus `R2-B1` scope control and `R1-F1` robustness framing.

