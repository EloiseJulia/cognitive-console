"use strict";

const app = {
  materials: null, csrf: null, capability: null, attemptId: null, current: null,
  hiddenStarted: null, hiddenMs: 0, formal: false, ended: false, pendingRequests: {},
};
const stage = document.getElementById("stage");
const startPanel = document.getElementById("start");
const saveExitButton = document.getElementById("save-exit-button");

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
  const error = el("p", {id: "stage-error", class: "error", role: "alert", tabindex: "-1"});
  stage.replaceChildren(error, ...nodes);
  stage.hidden = false;
  stage.focus();
  window.scrollTo(0, 0);
}

function showError(error) {
  const target = startPanel.hidden
    ? document.getElementById("stage-error")
    : document.getElementById("start-error");
  target.textContent = error.message || String(error);
  target.focus();
}

function setFormal(value) {
  app.formal = value;
  saveExitButton.hidden = !value || app.ended;
}

function requestId() {
  const bytes = crypto.getRandomValues(new Uint8Array(18));
  return Array.from(bytes, value => value.toString(16).padStart(2, "0")).join("");
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
  document.querySelectorAll(`input[name="${name}"]`).forEach(node => { node.disabled = true; });
}

async function api(path, data) {
  const nonce = app.pendingRequests[path] || requestId();
  app.pendingRequests[path] = nonce;
  let response;
  try {
    response = await fetch(path, {
      method: "POST", cache: "no-store", credentials: "same-origin",
      headers: {
        "Content-Type": "application/json", "X-CSRF-Token": app.csrf,
        ...(app.capability ? {"X-Study-Capability": app.capability} : {}),
      },
      body: JSON.stringify({...data, request_id: nonce}),
    });
  } catch (error) {
    throw error;
  }
  const value = await response.json();
  delete app.pendingRequests[path];
  if (!response.ok) throw new Error(value.error || "Study state error.");
  return value;
}

function renderEvidence(item, condition) {
  const card = el("article", {class: "evidence-card", "aria-label": "Evidence panel"});
  card.append(el("h2", {}, app.materials.simulated_record_notice));
  const rows = el("dl", {class: "evidence-rows"});
  const order = condition === "Contract" ? app.materials.primitive_ids : item.flat_order;
  order.forEach((evidenceId, index) => {
    const row = el("div", {
      class: "evidence-row", "data-row-id": `row-${index + 1}`,
      "data-position": String(index + 1),
    });
    const label = condition === "Contract"
      ? app.materials.contract_headings[evidenceId] : `Evidence ${"ABCDE"[index]}`;
    row.append(
      el("dt", {class: "evidence-label"}, label),
      el("dd", {class: "evidence-body"}, item.primitive_evidence[evidenceId]),
    );
    rows.append(row);
  });
  card.append(rows);
  return card;
}

function showTutorial() {
  const m = app.materials.participant_materials;
  const button = el("button", {type: "button", "data-action": "show-practice"}, "Continue to practice");
  replaceStage(el("h1", {}, "Tutorial and legend"), el("p", {}, m.legend), el("p", {}, m.tutorial), button);
}

function showPractice() {
  const practice = app.materials.participant_materials.practice;
  const item = {
    stimulus_id: "practice", primitive_evidence: practice.primitive_evidence,
    flat_order: app.materials.primitive_ids,
  };
  replaceStage(
    el("h1", {}, "Practice"), renderEvidence(item, "Contract"),
    optionFieldset("practice-q1", practice.q1.text, app.materials.q1.options),
    el("button", {type: "button", "data-action": "practice-q1"}, "Submit practice Q1"),
    el("div", {id: "practice-next"}),
  );
}

async function practiceQ1(button) {
  const answer = selected("practice-q1");
  if (!answer) return;
  button.disabled = true;
  await api("/api/practice", {attempt_id: app.attemptId, step: "q1", answer});
  lock("practice-q1");
  button.disabled = true;
  const practice = app.materials.participant_materials.practice;
  document.getElementById("practice-next").append(
    optionFieldset("practice-q2", practice.q2.text, practice.q2.options),
    el("button", {type: "button", "data-action": "practice-q2"}, "Submit practice Q2"),
  );
  document.querySelector('input[name="practice-q2"]').focus();
}

async function practiceQ2(button) {
  const answer = selected("practice-q2");
  if (!answer) return;
  button.disabled = true;
  const response = await api("/api/practice", {
    attempt_id: app.attemptId, step: "q2", answer,
  });
  lock("practice-q2");
  button.disabled = true;
  document.getElementById("practice-next").append(
    el("p", {class: "feedback"}, response.feedback),
    el("button", {type: "button", "data-action": "begin-formal"}, "Begin formal trials"),
  );
  app.current = response;
}

function showTrial() {
  setFormal(true);
  const trial = app.current;
  app.hiddenMs = 0;
  app.hiddenStarted = document.hidden ? performance.now() : null;
  replaceStage(
    el("p", {class: "progress"}, `Formal trial ${trial.trial_index + 1} of 10 · Block ${trial.block}`),
    renderEvidence(trial.item, trial.condition),
    optionFieldset("formal-q1", app.materials.q1.text, app.materials.q1.options),
    el("button", {type: "button", "data-action": "formal-q1"}, "Submit Q1 and lock answer"),
    el("div", {id: "q2-area"}),
  );
}

async function formalQ1(button) {
  const answer = selected("formal-q1");
  if (!answer) return;
  button.disabled = true;
  const response = await api("/api/q1", {attempt_id: app.attemptId, answer});
  lock("formal-q1");
  button.disabled = true;
  const q2Area = document.getElementById("q2-area");
  q2Area.append(
    optionFieldset("formal-q2", response.q2.text, response.q2.options),
    el("button", {type: "button", "data-action": "formal-q2"}, "Submit Q2 and continue"),
  );
  document.querySelector('input[name="formal-q2"]').focus();
}

async function formalQ2(button) {
  const answer = selected("formal-q2");
  if (!answer) return;
  button.disabled = true;
  const hidden = Math.round(app.hiddenMs + (
    app.hiddenStarted === null ? 0 : performance.now() - app.hiddenStarted
  ));
  app.current = await api("/api/q2", {
    attempt_id: app.attemptId, answer, hidden_ms: hidden,
  });
  if (app.current.phase === "ease") showEase(app.current.block);
  else showTrial();
}

function showEase(block) {
  const material = app.materials.participant_materials.block_ease;
  replaceStage(
    el("h1", {}, `Block ${block} complete`),
    optionFieldset("ease", material.question, material.options),
    el("div", {class: "actions"},
      null),
  );
  stage.lastChild.append(
    el("button", {type: "button", "data-action": "ease", "data-block": String(block)}, "Continue"),
    el("button", {type: "button", "data-action": "ease-skip", "data-block": String(block)}, "Prefer not to answer"),
  );
}

async function submitEase(button, skip) {
  const block = Number(button.dataset.block);
  const answer = skip ? null : selected("ease");
  if (!skip && !answer) return;
  button.disabled = true;
  app.current = await api("/api/ease", {attempt_id: app.attemptId, block, answer});
  if (app.current.phase === "diagnostic") showDiagnostic();
  else showTrial();
}

function showDiagnostic() {
  const material = app.materials.participant_materials.post_task_manipulation_diagnostic;
  replaceStage(
    el("h1", {}, "Post-task format question"),
    optionFieldset("diagnostic", material.question, material.options),
    el("div", {class: "actions"}),
  );
  stage.lastChild.append(
    el("button", {type: "button", "data-action": "diagnostic"}, "Submit"),
    el("button", {type: "button", "data-action": "diagnostic-skip"}, "Prefer not to answer"),
  );
}

async function submitDiagnostic(skip) {
  const answer = skip ? null : selected("diagnostic");
  if (!skip && !answer) return;
  document.querySelectorAll('[data-action^="diagnostic"]').forEach(node => { node.disabled = true; });
  await api("/api/diagnostic", {attempt_id: app.attemptId, answer});
  await api("/api/complete", {attempt_id: app.attemptId});
  showDebrief();
}

function showDebrief() {
  app.ended = true;
  setFormal(false);
  const jsonLink = el("button", {type: "button", "data-action": "download-json"}, "Download signed JSON");
  const csvLink = el("button", {type: "button", "data-action": "download-csv"}, "Download signed CSV");
  replaceStage(
    el("h1", {}, "Preview complete"),
    el("p", {}, app.materials.participant_materials.debrief),
    el("p", {}, "Completed formal trials: 10 of 10."),
    el("div", {class: "actions"}),
  );
  stage.lastChild.append(jsonLink, csvLink);
}

async function downloadExport(format) {
  const response = await fetch(
    `/api/export?attempt_id=${encodeURIComponent(app.attemptId)}&format=${format}`,
    {cache: "no-store", credentials: "same-origin", headers: {"X-Study-Capability": app.capability}},
  );
  if (!response.ok) throw new Error("Signed export download failed.");
  const blob = await response.blob();
  const link = document.createElement("a");
  link.download = `microstudy-${app.attemptId}.${format}`;
  link.href = URL.createObjectURL(blob);
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

async function saveAndExit(button) {
  button.disabled = true;
  await api("/api/save-exit", {attempt_id: app.attemptId});
  app.ended = true;
  setFormal(false);
  await downloadExport("json");
  await downloadExport("csv");
  replaceStage(
    el("h1", {}, "Session ended"),
    el("p", {}, "Your signed partial JSON and CSV exports were downloaded. No performance feedback is shown."),
  );
}

async function startStudy() {
  const participantCode = document.getElementById("participant-code").value.trim();
  const sequence = document.getElementById("sequence").value;
  const response = await api("/api/start", {participant_code: participantCode, sequence});
  app.attemptId = response.attempt_id;
  app.capability = response.capability;
  startPanel.hidden = true;
  showTutorial();
}

document.addEventListener("click", event => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const actions = {
    "show-practice": () => showPractice(),
    "practice-q1": () => practiceQ1(button),
    "practice-q2": () => practiceQ2(button),
    "begin-formal": () => showTrial(),
    "formal-q1": () => formalQ1(button),
    "formal-q2": () => formalQ2(button),
    "ease": () => submitEase(button, false),
    "ease-skip": () => submitEase(button, true),
    "diagnostic": () => submitDiagnostic(false),
    "diagnostic-skip": () => submitDiagnostic(true),
    "save-exit": () => saveAndExit(button),
    "download-json": () => downloadExport("json"),
    "download-csv": () => downloadExport("csv"),
  };
  Promise.resolve(actions[button.dataset.action]?.()).catch(error => {
    showError(error);
    if (!app.ended) button.disabled = false;
  });
});

document.addEventListener("visibilitychange", () => {
  if (!app.attemptId) return;
  if (document.hidden && app.hiddenStarted === null) app.hiddenStarted = performance.now();
  if (!document.hidden && app.hiddenStarted !== null) {
    app.hiddenMs += performance.now() - app.hiddenStarted;
    app.hiddenStarted = null;
  }
});

document.getElementById("start-button").addEventListener("click", () => {
  document.getElementById("start-button").disabled = true;
  startStudy().catch(error => {
    showError(error);
    document.getElementById("start-button").disabled = false;
  });
});

fetch("/api/bootstrap", {cache: "no-store", credentials: "same-origin"})
  .then(response => response.ok ? response.json() : Promise.reject(new Error("Could not load materials.")))
  .then(bootstrap => {
    app.csrf = bootstrap.csrf_token;
    app.materials = bootstrap.materials;
    const select = document.getElementById("sequence");
    for (const code of app.materials.sequence_codes) select.append(el("option", {value: code}, code));
  })
  .catch(error => {
    showError(error);
    document.getElementById("start-button").disabled = true;
  });

window.MicrostudyTest = {renderEvidence};
