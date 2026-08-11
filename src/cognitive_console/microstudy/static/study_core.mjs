export function csvEscape(value) {
  if (value === null || value === undefined) return "";
  let text = typeof value === "object" ? JSON.stringify(value) : String(value);
  if (/^[=+\-@]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

export function createEmptyTrial(slot, materialsVersion) {
  return {
    slot_index: slot.slot_index,
    ticket_code: slot.ticket_code,
    position: slot.position,
    planned: true,
    presented: false,
    q1_submitted: false,
    q2_submitted: false,
    complete: false,
    submitted: false,
    q1: null,
    q2: null,
    q1_correct: null,
    q2_correct: null,
    cca_correct: null,
    rt_q1_ms: null,
    rt_q2_ms: null,
    rt_total_ms: null,
    hidden_ms: null,
    q1_missing: true,
    q2_missing: true,
    q1_correct_missing: true,
    q2_correct_missing: true,
    cca_correct_missing: true,
    rt_q1_missing: true,
    rt_q2_missing: true,
    rt_total_missing: true,
    hidden_ms_missing: true,
    materials_version: materialsVersion,
  };
}

export function submitQ1(trial, answer, correctCode, rtMs) {
  if (trial.q1_submitted) throw new Error("Q1 is already locked");
  trial.q1 = answer;
  trial.q1_submitted = true;
  trial.q1_correct = answer === correctCode;
  trial.rt_q1_ms = Math.round(rtMs);
  trial.q1_missing = false;
  trial.q1_correct_missing = false;
  trial.rt_q1_missing = false;
}

export function submitQ2(trial, answer, correctCode, rtMs, hiddenMs) {
  if (!trial.q1_submitted) throw new Error("Q1 must be locked before Q2");
  if (trial.q2_submitted) throw new Error("Q2 is already locked");
  trial.q2 = answer;
  trial.q2_submitted = true;
  trial.complete = true;
  trial.submitted = true;
  trial.q2_correct = answer === correctCode;
  trial.cca_correct = trial.q1_correct && trial.q2_correct;
  trial.rt_q2_ms = Math.round(rtMs);
  trial.rt_total_ms = trial.rt_q1_ms + trial.rt_q2_ms;
  trial.hidden_ms = Math.round(hiddenMs);
  for (const key of [
    "q2_missing", "q2_correct_missing", "cca_correct_missing",
    "rt_q2_missing", "rt_total_missing", "hidden_ms_missing",
  ]) trial[key] = false;
}

export function neutralPreview(copy, choice) {
  return copy.replaceAll("{choice}", choice);
}
