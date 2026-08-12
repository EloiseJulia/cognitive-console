export function csvEscape(value) {
  if (value === null || value === undefined) return "";
  let text = typeof value === "object" ? JSON.stringify(value) : String(value);
  if (/^[=+\-@]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"', '""')}"`;
}

export function noPrivateKeys(value) {
  const text = JSON.stringify(value);
  return !/(expected|correct_reason_id|correct_scope_id|q1_state|paper_state|reason_class|scope_gate_required|decisive_positive|decisive_negative)/i.test(text);
}

export function strictGaa(q1Correct, reasonChoiceCorrect, scopeGateRequired, scopeChoiceCorrect) {
  const reasonCorrect = Boolean(reasonChoiceCorrect)
    && (!scopeGateRequired || Boolean(scopeChoiceCorrect));
  return Boolean(q1Correct) && reasonCorrect;
}

export function uniqueIds(rows) {
  return new Set(rows.map((row) => row.id)).size === rows.length;
}
