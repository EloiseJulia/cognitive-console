import assert from "node:assert/strict";
import {
  noPrivateKeys,
  participantRoute,
  uniqueIds,
} from "../src/cognitive_console/button_board_stepwise/static/study_core.mjs";

assert.equal(uniqueIds([{ id: "a" }, { id: "b" }]), true);
assert.equal(uniqueIds([{ id: "a" }, { id: "a" }]), false);
assert.equal(noPrivateKeys({ scene: { id: "F2" } }), true);
assert.equal(noPrivateKeys({ scene: { expected_state: "SUPPORTED" } }), false);
assert.equal(participantRoute([{ step: 1, answer: "INFO" }]), "DIAGNOSTIC");
assert.equal(participantRoute([
  { step: 1, answer: "CONTROL" },
  { step: 2, answer: "NOT_COMPARED" },
]), "UNRESOLVED");
assert.equal(participantRoute([
  { step: 1, answer: "CONTROL" },
  { step: 2, answer: "COMPARED" },
  { step: 3, answer: "NOT_BETTER" },
]), "WITHHELD");
assert.equal(participantRoute([
  { step: 1, answer: "CONTROL" },
  { step: 2, answer: "COMPARED" },
  { step: 3, answer: "BETTER" },
  { step: 4, answer: "NO_HARM" },
  { step: 5, answer: "SCOPE_WRITTEN" },
  { step: 6, answer: "opaque-option" },
]), "SUPPORTED");

console.log("button-board stepwise JS checks passed");
