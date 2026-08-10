"use strict";

import {createEmptyTrial, csvEscape, submitQ1, submitQ2} from "./study_core.mjs";

const app = {
  materials: null,
  plan: null,
  exportData: null,
  trialIndex: 0,
  q1Start: 0,
  q2Start: 0,
  hiddenStarted: null,
  hiddenMs: 0,
  easeCompleted: {1: false, 2: false},
};

const stage = document.getElementById("stage");
const startPanel = document.getElementById("start");

function el(tag, attrs = {}, text = null) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else node.setAttribute(key, value);
  }
  if (text !== null) node.textContent = text;
  return node;
}

function replaceStage(...nodes) {
  stage.replaceChildren(...nodes);
  stage.hidden = false;
  stage.focus();
  window.scrollTo(0, 0);
}

function optionFieldset(name, question, options) {
  const fieldset = el("fieldset");
  fieldset.append(el("legend", {}, question));
  for (const option of options) {
    const label = el("label", {class: "choice"});
    const input = el("input", {type: "radio", name, value: option.key});
    label.append(input, document.createTextNode(` ${option.text}`));
    fieldset.append(label);
  }
  return fieldset;
}

function selected(name) {
  return document.querySelector(`input[name="${name}"]:checked`)?.value ?? null;
}

function lock(name) {
  document.querySelectorAll(`input[name="${name}"]`).forEach(node => {
    node.disabled = true;
  });
}

function renderEvidence(item, condition, primitiveIds, headings, notice) {
  const card = el("article", {
    class: "evidence-card",
    "data-condition": condition,
    "data-stimulus-id": item.stimulus_id || "practice",
    "aria-label": `${condition} simulated evaluation record`,
  });
  card.append(el("h2", {}, notice));
  const rows = el("dl", {class: "evidence-rows"});
  const order = condition === "Contract" ? primitiveIds : item.flat_order;
  order.forEach((evidenceId, index) => {
    const row = el("div", {
      class: "evidence-row",
      "data-evidence-id": evidenceId,
      "data-position": String(index + 1),
    });
    const label = condition === "Contract" ? headings[evidenceId] : `Evidence ${"ABCDE"[index]}`;
    row.append(
      el("dt", {class: "evidence-label"}, label),
      el("dd", {class: "evidence-body"}, item.primitive_evidence[evidenceId]),
    );
    rows.append(row);
  });
  card.append(rows);
  return card;
}

async function loadMaterials() {
  const response = await fetch("/api/materials", {cache: "no-store", credentials: "omit"});
  if (!response.ok) throw new Error("Could not load authoritative materials.");
  app.materials = await response.json();
  const sequence = document.getElementById("sequence");
  for (const row of app.materials.sequences.sequences) {
    sequence.append(el("option", {value: row.code}, row.code));
  }
}

function showTutorial() {
  const m = app.materials.stimuli.participant_materials;
  const title = el("h1", {}, "Tutorial and legend");
  const legend = el("p", {}, m.legend);
  const tutorial = el("p", {}, m.tutorial);
  const next = el("button", {type: "button"}, "Continue to practice");
  next.addEventListener("click", showPractice);
  replaceStage(title, legend, tutorial, next);
}

function showPractice() {
  const stimuli = app.materials.stimuli;
  const practice = stimuli.participant_materials.practice;
  const item = {
    stimulus_id: "practice",
    primitive_evidence: practice.primitive_evidence,
    flat_order: stimuli.primitive_ids,
  };
  app.exportData.practice_presented = true;
  const card = renderEvidence(
    item, "Contract", stimuli.primitive_ids, stimuli.contract_headings, practice.notice
  );
  const q1 = optionFieldset("practice-q1", practice.q1.text, stimuli.q1.options);
  const submitQ1 = el("button", {type: "button"}, "Submit practice Q1");
  const area = el("div");
  submitQ1.addEventListener("click", () => {
    if (!selected("practice-q1")) return;
    lock("practice-q1");
    submitQ1.disabled = true;
    app.exportData.practice_q1_submitted = true;
    const q2 = optionFieldset("practice-q2", practice.q2.text, practice.q2.options);
    const submitQ2 = el("button", {type: "button"}, "Submit practice Q2");
    submitQ2.addEventListener("click", () => {
      if (!selected("practice-q2")) return;
      lock("practice-q2");
      submitQ2.disabled = true;
      app.exportData.practice_q2_submitted = true;
      app.exportData.practice_complete = true;
      const feedback = el("p", {class: "feedback"}, practice.feedback);
      const proceed = el("button", {type: "button"}, "Begin formal trials");
      proceed.addEventListener("click", showTrial);
      area.append(feedback, proceed);
    });
    area.append(q2, submitQ2);
    q2.querySelector("input").focus();
  });
  replaceStage(el("h1", {}, "Practice"), card, q1, submitQ1, area);
}

function currentItem(slot) {
  return app.materials.stimuli.items.find(item => item.stimulus_id === slot.item);
}

function showTrial() {
  if (app.trialIndex >= app.plan.length) {
    showDiagnostic();
    return;
  }
  const slot = app.plan[app.trialIndex];
  if (slot.position === 1 && app.trialIndex > 0 &&
      !app.easeCompleted[slot.block - 1]) {
    showEase(slot.block - 1);
    return;
  }
  const stimuli = app.materials.stimuli;
  const item = currentItem(slot);
  const trial = app.exportData.trials[app.trialIndex];
  trial.presented = true;
  app.hiddenMs = 0;
  app.hiddenStarted = document.hidden ? performance.now() : null;
  app.q1Start = performance.now();
  const progress = el("p", {class: "progress"}, `Formal trial ${app.trialIndex + 1} of 10 · Block ${slot.block}`);
  const card = renderEvidence(
    item, slot.condition, stimuli.primitive_ids, stimuli.contract_headings,
    stimuli.simulated_record_notice
  );
  const q1 = optionFieldset("formal-q1", stimuli.q1.text, stimuli.q1.options);
  const submitQ1 = el("button", {type: "button"}, "Submit Q1 and lock answer");
  const q2Area = el("div");
  submitQ1.addEventListener("click", () => {
    const answer = selected("formal-q1");
    if (!answer) return;
    submitQ1(trial, answer, slot.q1_key, performance.now() - app.q1Start);
    lock("formal-q1");
    submitQ1.disabled = true;
    const template = stimuli.q2_templates.find(row => row.template_id === slot.q2_template_id);
    const q2 = optionFieldset("formal-q2", template.text, template.options);
    const submitQ2 = el("button", {type: "button"}, "Submit Q2 and continue");
    app.q2Start = performance.now();
    submitQ2.addEventListener("click", () => {
      const q2Answer = selected("formal-q2");
      if (!q2Answer) return;
      submitQ2(
        trial, q2Answer, slot.q2_key, performance.now() - app.q2Start,
        app.hiddenMs + (app.hiddenStarted === null ? 0 : performance.now() - app.hiddenStarted)
      );
      lock("formal-q2");
      submitQ2.disabled = true;
      app.trialIndex += 1;
      showTrial();
    });
    q2Area.append(q2, submitQ2);
    q2.querySelector("input").focus();
  });
  replaceStage(progress, card, q1, submitQ1, q2Area);
}

function showEase(block) {
  const material = app.materials.stimuli.participant_materials.block_ease;
  const field = optionFieldset("ease", material.question, material.options);
  const continueButton = el("button", {type: "button"}, "Continue");
  const skipButton = el("button", {type: "button"}, "Prefer not to answer");
  const finish = value => {
    app.exportData[`block_${block}_ease`] = value;
    app.easeCompleted[block] = true;
    showTrial();
  };
  continueButton.addEventListener("click", () => {
    const answer = selected("ease");
    if (answer) finish(answer);
  });
  skipButton.addEventListener("click", () => finish(null));
  replaceStage(el("h1", {}, `Block ${block} complete`), field,
    el("div", {class: "actions"}));
  stage.lastChild.append(continueButton, skipButton);
}

function showDiagnostic() {
  if (!app.easeCompleted[2]) {
    showEase(2);
    return;
  }
  const diagnostic = app.materials.stimuli.participant_materials.post_task_manipulation_diagnostic;
  app.exportData.post_task_diagnostic_presented = true;
  const field = optionFieldset("diagnostic", diagnostic.question, diagnostic.options);
  const submit = el("button", {type: "button"}, "Submit");
  const skip = el("button", {type: "button"}, "Prefer not to answer");
  const finish = answer => {
    app.exportData.post_task_diagnostic_submitted = answer !== null;
    app.exportData.post_task_diagnostic_response = answer;
    app.exportData.post_task_diagnostic_correct =
      answer === null ? null : answer === diagnostic.correct_key;
    showDebrief();
  };
  submit.addEventListener("click", () => {
    const answer = selected("diagnostic");
    if (answer) finish(answer);
  });
  skip.addEventListener("click", () => finish(null));
  replaceStage(el("h1", {}, "Post-task format question"), field, el("div", {class:"actions"}));
  stage.lastChild.append(submit, skip);
}

function csvText(data) {
  const sessionFields = app.materials.stimuli.export_schema.session_fields;
  const trialFields = app.materials.stimuli.export_schema.trial_fields;
  const fields = ["export_schema_version", "stimuli_sha256", "sequences_sha256",
    ...sessionFields, ...trialFields];
  const lines = [fields.map(csvEscape).join(",")];
  for (const trial of data.trials) {
    const row = {
      export_schema_version: data.export_schema_version,
      stimuli_sha256: data.material_hashes.stimuli_sha256,
      sequences_sha256: data.material_hashes.sequences_sha256,
      ...data,
      ...trial,
    };
    lines.push(fields.map(field => csvEscape(row[field])).join(","));
  }
  return `${lines.join("\r\n")}\r\n`;
}

function download(name, type, text) {
  const url = URL.createObjectURL(new Blob([text], {type}));
  const link = el("a", {href: url, download: name});
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function currentExport() {
  const snapshot = structuredClone(app.exportData);
  snapshot.completion_status = snapshot.trials.every(row => row.complete)
    ? "complete" : "partial";
  return snapshot;
}

function showDebrief() {
  app.exportData.completion_status = app.exportData.trials.every(row => row.complete)
    ? "complete" : "partial";
  const complete = app.exportData.trials.filter(row => row.complete).length;
  const jsonButton = el("button", {type: "button"}, "Download JSON");
  const csvButton = el("button", {type: "button"}, "Download CSV");
  jsonButton.addEventListener("click", () => download(
    `microstudy-${app.exportData.attempt_id}.json`, "application/json",
    `${JSON.stringify(app.exportData, null, 2)}\n`
  ));
  csvButton.addEventListener("click", () => download(
    `microstudy-${app.exportData.attempt_id}.csv`, "text/csv;charset=utf-8",
    csvText(app.exportData)
  ));
  replaceStage(
    el("h1", {}, "Preview complete"),
    el("p", {}, app.materials.stimuli.participant_materials.debrief),
    el("p", {}, `Completed formal trials: ${complete} of 10. Sequence: ${app.exportData.sequence}.`),
    el("div", {class: "actions"}),
  );
  stage.lastChild.append(jsonButton, csvButton);
}

async function startStudy() {
  const participantCode = document.getElementById("participant-code").value.trim();
  const sequence = document.getElementById("sequence").value;
  if (!participantCode || !/^[A-Za-z0-9._-]{1,64}$/.test(participantCode)) {
    document.getElementById("start-error").textContent =
      "Enter an anonymous code using letters, numbers, dot, underscore, or hyphen.";
    return;
  }
  const response = await fetch(`/api/sequence/${encodeURIComponent(sequence)}`, {
    cache: "no-store", credentials: "omit",
  });
  if (!response.ok) throw new Error("Invalid sequence.");
  app.plan = await response.json();
  const stimuli = app.materials.stimuli;
  app.exportData = {
    export_schema_version: "microstudy-export-v1",
    material_schema_version: stimuli.schema_version,
    sequence_schema_version: app.materials.sequences.schema_version,
    material_hashes: app.materials.material_hashes,
    attempt_id: crypto.randomUUID(),
    participant_code: participantCode,
    sequence,
    completion_status: "in_progress",
    practice_presented: false,
    practice_q1_submitted: false,
    practice_q2_submitted: false,
    practice_complete: false,
    post_task_diagnostic_presented: false,
    post_task_diagnostic_submitted: false,
    post_task_diagnostic_response: null,
    post_task_diagnostic_correct: null,
    block_1_ease: null,
    block_2_ease: null,
    mechanical_exclusion: false,
    mechanical_exclusion_reason: "none",
    trials: app.plan.map(slot => createEmptyTrial(
      slot, stimuli.items.find(item => item.stimulus_id === slot.item),
      stimuli.materials_version
    )),
  };
  document.getElementById("download-current").hidden = false;
  startPanel.hidden = true;
  showTutorial();
}

document.addEventListener("visibilitychange", () => {
  if (!app.exportData || app.trialIndex >= 10) return;
  if (document.hidden && app.hiddenStarted === null) app.hiddenStarted = performance.now();
  if (!document.hidden && app.hiddenStarted !== null) {
    app.hiddenMs += performance.now() - app.hiddenStarted;
    app.hiddenStarted = null;
  }
});

document.getElementById("start-button").addEventListener("click", () => {
  startStudy().catch(error => {
    document.getElementById("start-error").textContent = error.message;
  });
  document.getElementById("download-current").addEventListener("click", () => {
    if (!app.exportData) return;
    const snapshot = currentExport();
    download(
      `microstudy-${snapshot.attempt_id}-current.json`,
      "application/json",
      `${JSON.stringify(snapshot, null, 2)}\n`,
    );
  });
});

loadMaterials().catch(error => {
  document.getElementById("start-error").textContent = error.message;
  document.getElementById("start-button").disabled = true;
});

window.MicrostudyTest = {csvEscape, csvText, createEmptyTrial, renderEvidence};
