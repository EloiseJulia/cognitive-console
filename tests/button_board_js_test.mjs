import assert from "node:assert/strict";
import {
  csvEscape, noPrivateKeys, strictGaa, uniqueIds,
} from "../src/cognitive_console/button_board/static/study_core.mjs";

assert.equal(csvEscape("=SUM(A1:A2)"), "\"'=SUM(A1:A2)\"");
assert.equal(csvEscape('a"b'), '"a""b"');
assert.equal(csvEscape(null), "");
assert.equal(noPrivateKeys({ q1_options: [{ id: "board-use" }] }), true);
assert.equal(noPrivateKeys({ correct_reason_id: "F1-R-A" }), false);
assert.equal(noPrivateKeys({ scope_gate_required: true }), false);
assert.equal(noPrivateKeys({ strict_gaa_trial: true }), false);
assert.equal(strictGaa(true, true, true, true), true);
assert.equal(strictGaa(true, true, true, false), false);
assert.equal(strictGaa(true, true, false, false), true);
assert.equal(strictGaa(false, true, false, true), false);
assert.equal(uniqueIds([{ id: "A" }, { id: "B" }]), true);
assert.equal(uniqueIds([{ id: "A" }, { id: "A" }]), false);
