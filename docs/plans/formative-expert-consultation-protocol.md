# Formative Expert Consultation — Protocol (for execution)

**Status:** PLAN / NOT YET EXECUTED. No data exists yet. Paper content behind this consultation is a
PENDING scaffold in `main.tex` (§Formative Study) and MUST NOT be filled with any expert statement,
quote, theme, or requirement until real, consented notes exist. Fabricating any of it would violate the
project's Part I honesty red line.

**Purpose (formative, not summative):** elicit whether the practical pain point this paper targets —
"a legible internal signal is being wired to an active control (a slider) before it is shown to help" —
is real in practice, and elicit design requirements for a release-decision record. This is motivation +
requirements elicitation, NOT validation of the method or a user study of the interface.

**Honest scope to state in the paper (caveat, non-negotiable):** single (or few) senior expert(s),
formative and non-representative; it motivates and shapes requirements; it does NOT test comprehension,
reliance calibration, behavior, or the interface itself. It does not close the need for a summative user study.

---

## 1. Participant(s)
- Target: 1 senior expert (or a small handful) with directly relevant expertise — e.g., interpretability /
  model-steering research, or ML/LLM interface/product design, or HCI evaluation of AI controls.
- Record (for methods section, subject to anonymization): seniority, field, why relevant. Do NOT name unless
  the expert explicitly consents to attribution; default to anonymized descriptor (e.g., "a senior researcher
  in mechanistic interpretability with N years' experience").

## 2. Ethics / consent (REQUIRED before any session — §5 item)
- Obtain the applicable ethics/IRB determination for a formative expert interview per your institution.
- Written informed consent covering: purpose, that notes/quotes may appear (anonymized by default) in a research
  paper, recording (if any), data handling/retention, right to withdraw, no compensation or compensation as applicable.
- Anonymization plan: assign a code (E1, E2, ...); strip identifying details from quotes; expert reviews any
  quote attributed to them before submission ("member check").
- Store consent + raw notes OUTSIDE git if they contain identifiers; commit only the anonymized, consented digest.

## 3. Format
- Semi-structured, 45–60 min, remote or in person. One interviewer + notetaker (or recording with consent).
- Show a brief stimulus: the problem framing (legible signal -> slider) + one worked qualification record
  (the Qwen–CAA uncertainty five-field record already in the paper) as a concrete artifact to react to.

## 4. Interview guide (semi-structured — probe, don't lead)
Opening (context, non-leading):
1. In your experience, when teams expose a model's internal signal in a UI (a probe, a steering direction),
   how is the decision to make it an *active control* vs a *read-only view* actually made today?
2. Have you seen cases where a control shipped on the basis that the signal was "there"/legible, rather than
   on evidence it helped? What happened?

Pain point (test whether it's real, allow disconfirmation):
3. Is "a legible direction is treated as a working control" a real problem you recognize, or overstated? Where
   is it most / least true?
4. What currently goes wrong when a steering control is offered to end users?

Reaction to the artifact (requirements elicitation):
5. [Show the five-field record.] Walking through this record, what would you need to see before granting a
   control an active role? What's missing?
6. Which of these fields matter to a release decision, which are noise, and what would you add?
7. What comparator would you consider fair (a strong prompt? an average prompt? something else)?
8. How should uncertainty / a negative or inconclusive result be shown so it isn't misread?

Closing:
9. If you had to give one rule of thumb for "don't ship this slider yet," what is it?
10. Anything I did not ask that matters here?

Non-leading discipline: do not ask "don't you agree sliders are premature?"; ask open questions and record
disconfirming views. Preserve any view that the pain point is NOT real — that is a valid, reportable outcome.

## 5. Analysis plan
- Lightweight thematic analysis / requirement extraction: code notes into (a) confirmation/disconfirmation of
  the pain point, (b) elicited design requirements, (c) proposed comparator/fairness views, (d) risks/warnings.
- Map elicited requirements to the paper's five-field record (which fields they support / challenge / add).
- Report N, expertise, method, and the formative/non-representative caveat honestly.
- If the expert disconfirms the pain point, report that too (do not suppress).

## 6. What goes into the paper (only after real notes + consent)
- §Formative Study: participant descriptor(s), method (semi-structured, stimulus, analysis), 2–4 elicited
  requirements, honest formative/N-scope caveat, and how the requirements shaped the record design.
- Intro/Motivation hook: 1–2 sentences that the pain point was grounded in a formative consultation, pointing
  to the section.
- Do NOT let it enter Abstract/Contributions as a validated finding; it is motivation + requirements only.

## 7. Reviewer-honesty guardrails
- Never state or imply the consultation validates the method or the interface.
- Never generalize N=1..few to users at large.
- Keep it clearly labeled formative throughout.
