export function uniqueIds(rows) {
  return new Set(rows.map((row) => row.id)).size === rows.length;
}

export function noPrivateKeys(value) {
  const blocked = /(expected|comparison_rule|required_readings|required_scope_dimensions|scope_correct|scope_written|decisive_step|gaa_correct|strict_correct|correctness)/i;
  if (Array.isArray(value)) return value.every(noPrivateKeys);
  if (value && typeof value === "object") {
    return Object.entries(value).every(([key, child]) => !blocked.test(key) && noPrivateKeys(child));
  }
  return true;
}

export function participantRoute(path) {
  for (const row of path) {
    if (row.step === 1 && row.answer === "INFO") return "DIAGNOSTIC";
    if (row.step === 2 && row.answer === "NOT_COMPARED") return "UNRESOLVED";
    if (row.step === 3 && row.answer === "NOT_BETTER") return "WITHHELD";
    if (row.step === 4 && row.answer === "HARM") return "WITHHELD";
    if (row.step === 5 && row.answer === "SCOPE_MISSING") return "UNRESOLVED";
    if (row.step === 6) return "SUPPORTED";
  }
  return null;
}
