# Stage Summary — cognitive-console (as of 2026-07-23)

- **Status:** exploratory phase; NO frozen confirmatory results yet; NOTHING submitted.
- **Venue:** CHI (primary, not locked). Governed by AI-Instruction Part I + AGENTS.md.
- **Purpose of this doc:** consolidate the evidence chain + risks + routes, and serve as the vehicle for the
  pre-registered C2b adjudication (see `docs/ledgers/prereg-c2b-adjudication.md`).

---

## 1. Where we are (Hypothesis → Evidence → Claim)

| Claim | What it says | Status | Best evidence |
|---|---|---|---|
| **C1** semantic facade (RQ1) | readable prompts reach only PART of the neutral→pole representational range a latent vector reaches | **partially-supported (exploratory)** | E-0003: Qwen2.5-7B, **3/4 axes** hold (deliberation 0.583, skepticism 0.548, uncertainty 0.713; CI<1, seed-stable). focus overshoots. |
| **C2a** internal non-surjectivity (RQ2, theory) | steering reaches internal states no prompt reproduces | proposed (theory-backed: Mishra) | not separately measured; motivation only |
| **C2b** behavioral gap (RQ2, CORE) | latent steering reaches BEHAVIOR beyond a bounded-prompt ceiling | **not-supported (exploratory, INVALID instrument)** | E-0004: Qwen2.5-7B, 3/4 axes beyond=False — BUT crude lexical proxies (audit-rejected, ceiling-saturated). Invalid evidence → not decisive. |
| **C3** boundary object (RQ3) | levers preserve control across model swap | proposed | not started |

**Reading:** RQ1/C1 is an emerging, scale-robust foundation. RQ2/C2b — the paper's core, riskiest bet —
has NO positive signal yet, but the only probe so far used proxies the audit already ruled unfit
(keyword/length-based, saturated at ceiling). Per the owner, that negative is INVALID for an irreversible
pivot; C2b must be re-measured with a qualified instrument (pre-registered) before any Plan-D decision.

## 2. Top rejection/kill risks
1. **"This is NLP not HCI"** — mitigated by interaction model + user study + design knowledge (later phases).
2. **RQ2 core may not exist behaviorally** — Mishra proves INTERNAL non-surjectivity, not behavioral; PSR
   (ICML'26) shows steering can match prompts; first (invalid) probe was negative. This is THE make-or-break.
3. **Scoop = LOW** (manual sweep) but "obvious combination" ~MED, contingent on C1+C2b empirics.

## 3. Three routes forward
- **A (chosen): pre-registered C2b adjudication.** Fix instrument (unsaturated reasoning-gain tasks,
  orthogonal non-lexical proxies, multi-sample+CI, alpha sweep, drop focus) → freeze success/kill →
  one GPU run → adjudicate. Details: `docs/ledgers/prereg-c2b-adjudication.md`.
- **B: Plan D pivot** — RQ1-core measurement/diagnostic CHI paper on the semantic-facade/legibility gap.
  Only taken if the QUALIFIED C2b instrument still shows no signal.
- **C: redesign axes** — focus keeps failing; a bottom-up axis set might be needed regardless.

## 4. Spend so far
AI credits ≈ 6.6k (subagents/audits/fixes). GPU: one borrowed-A800 session (~4 min compute, fully wiped,
user data untouched). No paid API. Local CPU for 0.5B/1.5B.

## 5. Discipline notes
- 6 independent hostile audits so far; EACH caught a result-corrupting bug before it reached a conclusion
  (length confound, anti-aligned facade, denominator artifact, C2b proxy basis, GPU-on-CPU, stale cache key).
- All results EXPLORATORY, valid_for_paper=false, protocol unfrozen. Nothing submitted.
