import assert from "node:assert/strict";
import {
  createEmptyTrial, csvEscape, neutralPreview, submitQ1, submitQ2,
} from "../src/cognitive_console/microstudy/static/study_core.mjs";

const slot = {
  slot_index: 1, ticket_code: "UNC-R", condition: "C", position: 1,
};
const trial = createEmptyTrial(slot, "v9");
assert.equal(trial.planned, true);
assert.equal(trial.presented, false);
assert.throws(() => submitQ2(trial, "A", "A", 10, 0), /Q1 must be locked/);
submitQ1(trial, "A", "A", 12.4);
assert.equal(trial.q1_submitted, true);
assert.equal(trial.rt_q1_ms, 12);
assert.throws(() => submitQ1(trial, "B", "B", 3), /already locked/);
assert.equal(trial.q1, "A");
submitQ2(trial, "B", "B", 20.6, 4.8);
assert.equal(trial.complete, true);
assert.equal(trial.cca_correct, true);
assert.equal(trial.rt_total_ms, 33);
assert.throws(() => submitQ2(trial, "C", "C", 1, 0), /already locked/);
assert.equal(trial.q2, "B");
assert.equal(csvEscape("=SUM(A1:A2)"), "\"'=SUM(A1:A2)\"");
assert.equal(csvEscape('a"b'), '"a""b"');
assert.equal(csvEscape(null), "");
assert.equal(
  neutralPreview("Your release choice: {choice}. Not correctness.", "W — Hide"),
  "Your release choice: W — Hide. Not correctness.",
);
