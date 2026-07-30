"""E-0012 APE procedure — §5-B frozen pre-specification.

FROZEN specification: prereg-e0012-verified-control-button-DRAFT.md §5-B.

Implements the Automatic Prompt Engineer (APE) variant frozen before Stage 0:
  1. Candidate generation via meta-prompt (N_cand=50, seed=42)
  2. DEV screening at k=3 (all 50 candidates, NO early stopping)
  3. Winner re-evaluation at k=5 (for kill-rule comparison)
  4. Kill rule: if auto_prompt DEV (k=5) ≥ button DEV (k=5, frozen_α) → TRANSFER

NON-NEGOTIABLE invariants (from §5-B):
  - Meta-prompt template: FROZEN, no edits permitted
  - seed=42: FROZEN for all LLM sampling in this procedure
  - N_cand=50: FROZEN; no post-hoc budget increases
  - No alternative algorithm may substitute
  - No iterative refinement, no early stopping

On CPU / synthetic (no GPU): generate_candidates_synthetic() returns pre-authored
calibration prompts (same content as data/e0012_prompts/calibration_prompts.yaml)
so the full APE pipeline exercises offline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# FROZEN APE parameters (§5-B — LOCKED at prereg freeze)
# --------------------------------------------------------------------------- #
APE_N_CAND: int = 50
APE_SEED: int = 42
APE_K_SCREEN: int = 3   # k samples per item during DEV screening
APE_K_WINNER: int = 5   # k samples for winner re-evaluation
APE_TEMPERATURE: float = 0.9
APE_TOP_P: float = 0.9

# Frozen meta-prompt template (§5-B — MUST NOT be modified after Stage 0)
APE_META_PROMPT_TEMPLATE: str = (
    "You are an expert in designing LLM calibration prompts. "
    "Generate {N_cand} distinct system prompts that will make a language model "
    "express accurate uncertainty — being neither overconfident nor underconfident. "
    "Each prompt should be a practical calibration instruction that works on "
    "diverse factual questions. Output each prompt on a separate line, "
    "preceded by its number."
)


def frozen_meta_prompt(n_cand: int = APE_N_CAND) -> str:
    """Return the frozen meta-prompt for APE candidate generation."""
    return APE_META_PROMPT_TEMPLATE.format(N_cand=n_cand)


# --------------------------------------------------------------------------- #
# Synthetic offline candidate generation
# --------------------------------------------------------------------------- #
# Pre-authored calibration prompts used as synthetic APE candidates (offline)
_SYNTHETIC_APE_CANDIDATES: Tuple[str, ...] = (
    "You are a well-calibrated assistant. Express your confidence level honestly: state high confidence only when very sure, and express appropriate uncertainty when you are not.",
    "Before answering, assess your certainty. Provide your answer followed by your confidence level. If you are unsure, say so explicitly.",
    "Answer factual questions accurately. When uncertain, provide your best guess along with a clear statement of your confidence level (e.g. 'Confidence: 40%').",
    "Be honest about what you know and what you don't. If a question is outside your knowledge or you are unsure, indicate your uncertainty clearly.",
    "Provide accurate answers. After each answer, state your confidence as a percentage. Avoid overconfidence — only claim high certainty when you are truly sure.",
    "You should be calibrated: your stated confidence should match your actual accuracy. Be uncertain when uncertain, and confident only when justified.",
    "Answer with epistemic humility. If you are unsure about a factual answer, state 'I'm not certain, but...' and give your best estimate with a confidence level.",
    "Your goal is accurate calibration. Express uncertainty when appropriate. Do not pretend to know things you don't. Provide: Answer and Confidence: X%.",
    "When answering questions, be transparent about your confidence. If you are not sure, admit it and provide your best estimate. End with Confidence: X%.",
    "Think carefully before answering. If you have low confidence in your answer, say so. It is better to admit uncertainty than to give a confidently wrong answer.",
    "Respond honestly to factual questions. Distinguish between what you know well and what you are guessing. Always provide a confidence percentage.",
    "Be a calibrated reasoner. Match your expressed confidence to your actual certainty. Do not bluff or overstate your knowledge.",
    "Answer accurately. When you are uncertain, say 'I'm not sure but...' and give your confidence. Prefer admitting ignorance over false certainty.",
    "Provide factual answers with appropriate epistemic humility. State your confidence explicitly. If you might be wrong, say so.",
    "Think about how likely your answer is to be correct. Express that probability as a confidence level. Admit uncertainty freely.",
    "You are a calibrated knowledge assistant. Be neither overconfident nor underconfident. State confidence levels that reflect your true uncertainty.",
    "Answer questions precisely. Always include your confidence estimate. Acknowledge when a question tests the limits of your knowledge.",
    "Calibrated responses only: match your stated confidence to your expected accuracy. Partial knowledge should lead to moderate confidence, not false certainty.",
    "Your goal is accurate self-assessment. Tell me both your answer and how confident you are. Do not overclaim — if something could be wrong, say so.",
    "Express calibrated uncertainty. Be explicit when you are guessing vs. when you are confident. End with: Confidence: X%.",
    "Provide honest, calibrated answers. Do not assert false confidence. If uncertain: admit it, estimate, and state confidence level.",
    "Reason carefully, then state your answer and confidence. If you lack information, say so rather than guessing with false certainty.",
    "Be epistemically humble. Overconfidence is a calibration error. State confidence honestly, even if that means saying 'I don't know' or 'Confidence: 20%'.",
    "Accurate uncertainty expression is valued. Do not be more confident than you should be. Always append Confidence: X% to your answer.",
    "Think like a calibrated forecaster. Your stated probability should reflect your true belief about the correct answer. Include Confidence: X%.",
    "Your task is to answer accurately and express calibrated uncertainty. If you are less than 70% sure, say so explicitly.",
    "When answering factual questions: give your best answer, then state your confidence. If you're guessing, say 'Best guess: ...' and give low confidence.",
    "Calibration test: your confidence percentages will be checked against accuracy. Only be 90%+ confident when you are truly very sure.",
    "Be honest about uncertainty. A well-calibrated response correctly identifies what you know and what you are unsure about. Include Confidence: X%.",
    "Answer the question, then provide your confidence on a 0-100% scale. Penalize yourself for overconfidence — it is worse to be falsely certain than to admit doubt.",
    "Respond with calibrated confidence. If you know the answer well, say so. If you're not sure, indicate that and give a lower confidence.",
    "Express your genuine epistemic state. If you believe you might be wrong, lower your confidence accordingly. Format: Answer: ... Confidence: X%.",
    "Be a reliable source: match your confidence to your accuracy. Do not overclaim. End every answer with Confidence: X%.",
    "Accurate calibration means knowing when you don't know. Be willing to express low confidence. This is valued over false certainty.",
    "Answer factual questions and self-assess. State your answer and how certain you are. Do not guess with high confidence.",
    "Your confidence should be a well-calibrated probability estimate. Think carefully about how often you would be right on similar questions.",
    "Give factual answers with honest confidence levels. If you are 50% sure, say Confidence: 50%. If 90% sure, say 90%.",
    "Demonstrate epistemic responsibility: express high confidence only when warranted, medium confidence when partially sure, and low confidence when guessing.",
    "Calibrated answering: neither overconfident nor underconfident. Always include Confidence: X% after your answer.",
    "Express true uncertainty. Overclaiming knowledge is a calibration failure. State your answer and confidence (0-100%) honestly.",
    "Be calibrated and honest. State your answer, then: 'Confidence: X%'. Do not inflate confidence to appear more capable.",
    "Think carefully, then commit to an answer with an honest confidence level. If the answer could easily be wrong, say Confidence: 30% or less.",
    "Your epistemic virtue is calibration. State exactly how confident you are. Do not pretend to certainty you do not have.",
    "Provide your best answer and attach a confidence estimate. Low confidence is fine — it is better than false certainty.",
    "When you do not know something, say so honestly and assign low confidence. This makes you a trustworthy, calibrated assistant.",
    "State your answer and your confidence level. If you are guessing, say so. Calibration means your 80% confidence items are correct ~80% of the time.",
    "Think about the reliability of your knowledge before answering. Express your confidence as a percentage. Be honest about limitations.",
    "Answer questions with appropriate hedging when uncertain. Include Confidence: X%. Prefer 'I think...' over false certainty.",
    "Be a calibrated responder. Your confidence scores will be evaluated against actual accuracy. Match them honestly.",
    "Provide accurate responses with calibrated confidence. When in doubt, express doubt. Prefer admitting uncertainty to overclaiming knowledge.",
)


def generate_candidates_synthetic(
    n_cand: int = APE_N_CAND,
    seed: int = APE_SEED,
) -> List[str]:
    """Generate APE candidate prompts offline (no model, no GPU).

    Returns the first n_cand from the pre-authored bank (shuffled by seed).
    Used for offline smoke testing of the APE pipeline.
    """
    bank = list(_SYNTHETIC_APE_CANDIDATES)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(bank)).tolist()
    shuffled = [bank[i] for i in order]
    result = shuffled[:n_cand]
    # Pad with numbered variants if needed
    while len(result) < n_cand:
        result.append(f"Answer questions with calibrated confidence. (#extra-{len(result)})")
    return result[:n_cand]


def generate_candidates_real(
    backend,
    n_cand: int = APE_N_CAND,
    seed: int = APE_SEED,
    authored_prompts: Optional[Sequence[str]] = None,
) -> List[str]:
    """Generate APE candidate prompts from the real model (A800 only).

    ``backend`` must be a GenBackend (alpha=0 for unsteered generation).
    Returns list of unique parseable prompt strings.  If fewer than n_cand
    are parseable, pads from authored_prompts (§5-B fallback rule).
    """
    from cognitive_console.steering.generate import SteerConfig  # noqa: PLC0415
    import numpy as _np  # noqa: PLC0415

    dummy_dir = _np.zeros(1)  # alpha=0 → unsteered
    steer = SteerConfig(direction=dummy_dir, alpha=0.0, layer=1)
    meta_prompt = frozen_meta_prompt(n_cand)
    try:
        raw_output = backend.generate(meta_prompt, steer, max_new_tokens=4096)
    except TypeError:
        raw_output = backend.generate(meta_prompt, None, max_new_tokens=4096)

    candidates = _parse_numbered_candidates(raw_output, n_cand)

    # Pad with authored if needed (§5-B: pad with ranked authored prompts)
    if authored_prompts and len(candidates) < n_cand:
        existing = set(c.strip().lower() for c in candidates)
        for ap in authored_prompts:
            if len(candidates) >= n_cand:
                break
            if ap.strip().lower() not in existing:
                candidates.append(ap)
                existing.add(ap.strip().lower())
    return candidates[:n_cand]


def _parse_numbered_candidates(text: str, n_cand: int) -> List[str]:
    """Parse numbered prompts from APE meta-prompt output.

    Accepts formats:
      "1. <prompt>\\n2. <prompt>\\n..."
      "1) <prompt>\\n2) <prompt>\\n..."
    """
    import re
    lines = text.strip().splitlines()
    candidates: List[str] = []
    seen: set = set()
    for line in lines:
        line = line.strip()
        m = re.match(r"^\d+[.)]\s*(.*)", line)
        if m:
            prompt = m.group(1).strip()
            if prompt and prompt.lower() not in seen:
                seen.add(prompt.lower())
                candidates.append(prompt)
    return candidates[:n_cand]


# --------------------------------------------------------------------------- #
# DEV screening (§5-B Step 2)
# --------------------------------------------------------------------------- #
@dataclass
class CandidateEval:
    """Evaluation of one APE candidate on DEV items."""
    candidate_id: int
    prompt_text: str
    dev_score: float   # mean(1−Brier) over DEV items at k_screen samples
    k_used: int


def evaluate_candidates_on_dev(
    candidates: Sequence[str],
    dev_items: Sequence[Dict],
    sampler,
    axis: str,
    direction: Any,
    layer: int,
    k: int = APE_K_SCREEN,
) -> List[CandidateEval]:
    """Screen all candidates on DEV items at k=3 (§5-B Step 2).

    Evaluates ALL n_cand candidates — NO early stopping.
    ``sampler`` is an OutcomeSampler (real or synthetic).
    ``direction`` is a dummy zero-vector (alpha=0 → unsteered) for prompt-only eval.
    """
    import numpy as _np  # noqa: PLC0415
    zero_dir = _np.zeros(1)  # alpha=0 → no steering; prompt effect only
    evals: List[CandidateEval] = []
    for i, prompt in enumerate(candidates):
        outcomes: List[float] = []
        for item in dev_items:
            batch = sampler.sample(
                axis=axis,
                item=item,
                instruction=prompt,
                alpha=0.0,
                k=k,
                direction=zero_dir,
                layer=layer,
            )
            outcomes.append(batch.mean_outcome())
        score = float(_np.mean(outcomes)) if outcomes else 0.0
        evals.append(CandidateEval(
            candidate_id=i,
            prompt_text=prompt,
            dev_score=score,
            k_used=k,
        ))
    return evals


def select_winner(evals: Sequence[CandidateEval]) -> CandidateEval:
    """Select top-1 candidate by DEV score; ties broken by lower candidate_id (§5-B)."""
    if not evals:
        raise ValueError("no candidates to select from")
    return min(evals, key=lambda e: (-e.dev_score, e.candidate_id))


def reevaluate_winner(
    winner: CandidateEval,
    dev_items: Sequence[Dict],
    sampler,
    axis: str,
    direction: Any,
    layer: int,
    k: int = APE_K_WINNER,
) -> CandidateEval:
    """Re-evaluate winner at k=5 for kill-rule comparison (§5-B Step 3)."""
    import numpy as _np  # noqa: PLC0415
    zero_dir = _np.zeros(1)
    outcomes: List[float] = []
    for item in dev_items:
        batch = sampler.sample(
            axis=axis,
            item=item,
            instruction=winner.prompt_text,
            alpha=0.0,
            k=k,
            direction=zero_dir,
            layer=layer,
        )
        outcomes.append(batch.mean_outcome())
    score = float(_np.mean(outcomes)) if outcomes else 0.0
    return CandidateEval(
        candidate_id=winner.candidate_id,
        prompt_text=winner.prompt_text,
        dev_score=score,
        k_used=k,
    )


# --------------------------------------------------------------------------- #
# Kill rule (§5 rule 5 / §5-B)
# --------------------------------------------------------------------------- #
KILL_RULE_RESULT_TRANSFER = "TRANSFER"
KILL_RULE_RESULT_PASS = "PASS"


def apply_kill_rule(
    auto_prompt_dev_score_k5: float,
    button_dev_score_k5: float,
) -> Tuple[str, str]:
    """Pre-registered kill rule (§5-B / §5 rule 5).

    Returns (result, reason) where result ∈ {TRANSFER, PASS}.
    TRANSFER: auto_optimized_prompt DEV (k=5) ≥ button DEV (k=5, frozen α)
              → button is classified TRANSFER, NOT VERIFIED-CONTROL.
    PASS: button beats auto-optimized prompt on DEV.
    """
    if auto_prompt_dev_score_k5 >= button_dev_score_k5:
        reason = (
            f"kill rule triggered: auto_prompt_dev={auto_prompt_dev_score_k5:.4f} "
            f"≥ button_dev={button_dev_score_k5:.4f} → TRANSFER (not VERIFIED-CONTROL)"
        )
        return KILL_RULE_RESULT_TRANSFER, reason
    else:
        reason = (
            f"kill rule NOT triggered: button_dev={button_dev_score_k5:.4f} "
            f"> auto_prompt_dev={auto_prompt_dev_score_k5:.4f} → proceed to Stage 1"
        )
        return KILL_RULE_RESULT_PASS, reason


# --------------------------------------------------------------------------- #
# Full APE run (orchestrator)
# --------------------------------------------------------------------------- #
@dataclass
class APERunResult:
    """Result of the full APE run for one stage."""
    auto_prompt_text: str
    auto_prompt_dev_score_k3: float  # screening score (k=3)
    auto_prompt_dev_score_k5: float  # re-evaluation score (k=5; for kill rule)
    all_candidate_evals: List[CandidateEval]
    n_cand_generated: int
    n_cand_padded: int          # how many were padded from authored family
    kill_rule_result: str = ""  # set after comparing against button DEV
    kill_rule_reason: str = ""

    @property
    def winner_prompt(self) -> str:
        return self.auto_prompt_text


def run_ape(
    candidates: Sequence[str],
    dev_items: Sequence[Dict],
    sampler,
    axis: str,
    direction: Any,
    layer: int,
    authored_count: int = 0,
) -> APERunResult:
    """Execute the full §5-B APE procedure: screen → select → re-evaluate.

    ``candidates`` must already be generated (via generate_candidates_synthetic
    or generate_candidates_real) before calling this function.
    """
    # Step 2: Screen all candidates at k=3 (no early stopping)
    evals = evaluate_candidates_on_dev(
        candidates, dev_items, sampler, axis, direction, layer, k=APE_K_SCREEN
    )

    # Select winner (tie-break by lower candidate_id)
    winner = select_winner(evals)

    # Step 3: Re-evaluate winner at k=5 for kill-rule comparison
    winner_k5 = reevaluate_winner(
        winner, dev_items, sampler, axis, direction, layer, k=APE_K_WINNER
    )

    return APERunResult(
        auto_prompt_text=winner.prompt_text,
        auto_prompt_dev_score_k3=winner.dev_score,
        auto_prompt_dev_score_k5=winner_k5.dev_score,
        all_candidate_evals=evals,
        n_cand_generated=len(candidates),
        n_cand_padded=authored_count,
    )
