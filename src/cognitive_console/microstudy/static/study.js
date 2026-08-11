"use strict";

const app = {
  csrf: null, locale: null, common: null, sequenceCodes: [], capability: null,
  attemptId: null, current: null, hiddenStarted: null, hiddenMs: 0,
  formal: false, ended: false, pendingRequests: {},
};
const gate = document.getElementById("language-gate");
const startPanel = document.getElementById("start");
const stage = document.getElementById("stage");
const header = document.getElementById("site-header");
const footer = document.getElementById("site-footer");
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

function format(text, values) {
  return Object.entries(values).reduce(
    (result, [key, value]) => result.replaceAll(`{${key}}`, String(value)), text,
  );
}

function focusHeading(container) {
  const heading = container.querySelector("h1");
  if (heading) {
    heading.tabIndex = -1;
    heading.focus();
  }
  window.scrollTo(0, 0);
}

function replaceStage(...nodes) {
  const error = el("p", {id: "stage-error", class: "error", role: "alert", tabindex: "-1"});
  stage.replaceChildren(error, ...nodes);
  stage.hidden = false;
  focusHeading(stage);
}

function showError(error) {
  const message = app.common?.errors?.state || "错误 / Error";
  const target = !gate.isConnected
    ? (startPanel.hidden ? document.getElementById("stage-error") : document.getElementById("start-error"))
    : document.getElementById("gate-error");
  if (!target) return;
  target.textContent = message;
  target.focus();
  console.error(error);
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
    const input = el("input", {type: "radio", name, value: option.id});
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
  const response = await fetch(path, {
    method: "POST", cache: "no-store", credentials: "same-origin",
    headers: {
      "Content-Type": "application/json", "X-CSRF-Token": app.csrf,
      ...(app.capability ? {"X-Study-Capability": app.capability} : {}),
    },
    body: JSON.stringify({...data, request_id: nonce}),
  });
  const value = await response.json();
  delete app.pendingRequests[path];
  if (!response.ok) throw new Error(value.error || "state");
  return value;
}

function renderEvidence(cardData) {
  const card = el("article", {class: "evidence-card", "aria-label": cardData.aria_label});
  card.append(el("h2", {}, cardData.notice));
  const rows = el("dl", {class: "evidence-rows"});
  cardData.rows.forEach((rowData, index) => {
    const row = el("div", {
      class: "evidence-row", "data-row-id": `row-${index + 1}`,
      "data-position": String(index + 1),
    });
    row.append(
      el("dt", {class: "evidence-label"}, rowData.label),
      el("dd", {class: "evidence-body"}, rowData.body),
    );
    rows.append(row);
  });
  card.append(rows);
  return card;
}

function applyChrome() {
  const chrome = app.common.chrome;
  document.documentElement.lang = app.locale;
  document.title = app.common.document_title;
  document.getElementById("header-title").textContent = chrome.header_title;
  document.getElementById("header-privacy").textContent = chrome.privacy_note;
  saveExitButton.textContent = chrome.save_exit;
  footer.textContent = chrome.footer;
  header.hidden = false;
  footer.hidden = false;
}

function showWelcome() {
  applyChrome();
  const welcome = app.common.welcome;
  const sequence = el("select", {id: "sequence", required: ""});
  for (const code of app.sequenceCodes) sequence.append(el("option", {value: code}, code));
  const switchButton = el(
    "button", {type: "button", "data-action": "switch-language"},
    welcome.switch_language,
  );
  startPanel.replaceChildren(
    el("h1", {}, welcome.heading),
    el("p", {class: "warning"}, welcome.warning),
    el("p", {}, welcome.setup_placeholder),
    el("label", {}, welcome.participant_code),
    el("label", {}, welcome.sequence),
    el("div", {class: "actions"}),
    el("p", {id: "start-error", class: "error", role: "alert", tabindex: "-1"}),
  );
  startPanel.children[3].append(
    el("input", {
      id: "participant-code", autocomplete: "off", maxlength: "64", required: "",
      "aria-label": welcome.participant_code,
    }),
  );
  startPanel.children[4].append(sequence);
  startPanel.children[5].append(
    el("button", {id: "start-button", type: "button", "data-action": "start"}, welcome.start),
    switchButton,
  );
  startPanel.hidden = false;
  stage.hidden = true;
  focusHeading(startPanel);
}

async function chooseLanguage(locale) {
  const response = await fetch(
    `/api/welcome?ui_language=${encodeURIComponent(locale)}`,
    {cache: "no-store", credentials: "same-origin"},
  );
  if (!response.ok) throw new Error("locale");
  const selectedBundle = await response.json();
  if (selectedBundle.ui_language !== locale) throw new Error("locale mismatch");
  app.locale = locale;
  app.common = selectedBundle.common;
  app.sequenceCodes = selectedBundle.sequence_codes;
  if (gate.isConnected) gate.remove();
  showWelcome();
}

function showTutorial() {
  const onboarding = app.common.onboarding;
  const glossary = el("dl", {class: "glossary"});
  for (const row of onboarding.glossary) {
    glossary.append(el("dt", {}, row.term), el("dd", {}, row.description));
  }
  const states = el("dl", {class: "glossary"});
  for (const row of onboarding.states) {
    states.append(el("dt", {}, row.label), el("dd", {}, row.description));
  }
  const steps = el("ol");
  for (const step of onboarding.steps) steps.append(el("li", {}, step));
  replaceStage(
    el("h1", {}, onboarding.heading),
    el("p", {}, onboarding.intro),
    glossary,
    el("h2", {}, onboarding.states_heading),
    states,
    el("h2", {}, onboarding.steps_heading),
    steps,
    el("button", {type: "button", "data-action": "show-practice"}, onboarding.continue_practice),
  );
}

function showPractice() {
  const practice = app.common.practice;
  replaceStage(
    el("h1", {}, practice.heading),
    el("article", {class: "practice-card"},
      null),
    optionFieldset("practice-q1", practice.q1.text, practice.q1.options),
    el("button", {type: "button", "data-action": "practice-q1"}, practice.submit_q1),
    el("div", {id: "practice-next"}),
  );
  stage.children[2].append(
    el("h2", {}, practice.notice),
    el("p", {}, practice.narrative),
  );
}

async function practiceQ1(button) {
  const answer = selected("practice-q1");
  if (!answer) return;
  button.disabled = true;
  await api("/api/practice", {attempt_id: app.attemptId, step: "q1", answer});
  lock("practice-q1");
  const practice = app.common.practice;
  document.getElementById("practice-next").append(
    optionFieldset("practice-q2", practice.q2.text, practice.q2.options),
    el("button", {type: "button", "data-action": "practice-q2"}, practice.submit_q2),
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
  document.getElementById("practice-next").append(
    el("p", {class: "feedback"}, response.feedback),
    el("button", {type: "button", "data-action": "begin-formal"}, app.common.practice.begin_formal),
  );
  app.current = response;
}

function showTrial() {
  setFormal(true);
  const trial = app.current;
  app.hiddenMs = 0;
  app.hiddenStarted = document.hidden ? performance.now() : null;
  replaceStage(
    el("h1", {class: "sr-only"}, format(app.common.progress.formal_trial, {
      current: trial.trial_index + 1, block: trial.block,
    })),
    el("p", {class: "progress"}, format(app.common.progress.formal_trial, {
      current: trial.trial_index + 1, block: trial.block,
    })),
    renderEvidence(trial.card),
    optionFieldset("formal-q1", trial.q1.text, trial.q1.options),
    el("button", {type: "button", "data-action": "formal-q1"}, app.common.buttons.submit_q1),
    el("div", {id: "q2-area"}),
  );
}

async function formalQ1(button) {
  const answer = selected("formal-q1");
  if (!answer) return;
  button.disabled = true;
  const response = await api("/api/q1", {attempt_id: app.attemptId, answer});
  lock("formal-q1");
  const q2Area = document.getElementById("q2-area");
  q2Area.append(
    optionFieldset("formal-q2", response.q2.text, response.q2.options),
    el("button", {type: "button", "data-action": "formal-q2"}, app.common.buttons.submit_q2),
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
  replaceStage(
    el("h1", {}, format(app.common.progress.block_complete, {block})),
    optionFieldset("ease", app.common.ease.question, app.common.ease.options),
    el("div", {class: "actions"}),
  );
  stage.lastChild.append(
    el("button", {type: "button", "data-action": "ease", "data-block": String(block)}, app.common.buttons.continue),
    el("button", {type: "button", "data-action": "ease-skip", "data-block": String(block)}, app.common.buttons.prefer_not),
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
  const diagnostic = app.common.diagnostic;
  replaceStage(
    el("h1", {}, diagnostic.heading),
    optionFieldset("diagnostic", diagnostic.question, diagnostic.options),
    el("div", {class: "actions"}),
  );
  stage.lastChild.append(
    el("button", {type: "button", "data-action": "diagnostic"}, app.common.buttons.submit),
    el("button", {type: "button", "data-action": "diagnostic-skip"}, app.common.buttons.prefer_not),
  );
}

async function submitDiagnostic(skip) {
  const answer = skip ? null : selected("diagnostic");
  if (!skip && !answer) return;
  document.querySelectorAll('[data-action^="diagnostic"]').forEach(node => { node.disabled = true; });
  await api("/api/diagnostic", {attempt_id: app.attemptId, answer});
  await api("/api/complete", {attempt_id: app.attemptId});
  showExportScreen(true);
}

function showExportScreen(complete) {
  app.ended = true;
  setFormal(false);
  const copy = app.common.export;
  replaceStage(
    el("h1", {}, complete ? copy.complete_heading : copy.partial_heading),
    ...(complete ? [
      el("p", {}, app.common.debrief),
      el("p", {}, copy.completed_trials),
    ] : [el("p", {}, copy.partial_ready)]),
    el("p", {id: "export-status"}, copy.ready),
    el("p", {}, copy.retry),
    el("div", {class: "actions"}),
  );
  stage.lastChild.append(
    el("button", {type: "button", "data-action": "download-json"}, app.common.buttons.download_json),
    el("button", {type: "button", "data-action": "download-csv"}, app.common.buttons.download_csv),
    el("button", {type: "button", "data-action": "finish"}, app.common.buttons.finish),
  );
}

async function downloadExport(outputFormat) {
  const response = await fetch(
    `/api/export?attempt_id=${encodeURIComponent(app.attemptId)}&format=${outputFormat}`,
    {cache: "no-store", credentials: "same-origin", headers: {"X-Study-Capability": app.capability}},
  );
  if (!response.ok) throw new Error("download");
  const blob = await response.blob();
  const link = document.createElement("a");
  link.download = `microstudy-${app.attemptId}.${outputFormat}`;
  link.href = URL.createObjectURL(blob);
  document.body.append(link);
  link.click();
  const url = link.href;
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  document.getElementById("export-status").textContent =
    format(app.common.export.download_started, {format: outputFormat.toUpperCase()});
}

async function saveAndExit(button) {
  button.disabled = true;
  const response = await api("/api/save-exit", {attempt_id: app.attemptId});
  if (response.phase !== "export_ready") throw new Error("export");
  showExportScreen(false);
}

function finish() {
  app.ended = true;
  setFormal(false);
  replaceStage(
    el("h1", {}, app.common.export.finished_heading),
    el("p", {}, app.common.export.finished),
  );
}

async function startStudy(button) {
  button.disabled = true;
  const response = await api("/api/start", {
    participant_code: document.getElementById("participant-code").value.trim(),
    sequence: document.getElementById("sequence").value,
    ui_language: app.locale,
  });
  if (response.ui_language !== app.locale) throw new Error("locale lock");
  app.attemptId = response.attempt_id;
  app.capability = response.capability;
  startPanel.replaceChildren();
  startPanel.hidden = true;
  showTutorial();
}

document.addEventListener("click", event => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const actions = {
    "choose-language": () => chooseLanguage(button.dataset.locale),
    "switch-language": () => chooseLanguage(app.locale === "en" ? "zh-Hans" : "en"),
    "start": () => startStudy(button),
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
    "finish": () => finish(),
  };
  Promise.resolve(actions[button.dataset.action]?.()).catch(error => {
    showError(error);
    button.disabled = false;
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

fetch("/api/bootstrap", {cache: "no-store", credentials: "same-origin"})
  .then(response => response.ok ? response.json() : Promise.reject(new Error("bootstrap")))
  .then(bootstrap => {
    if (bootstrap.fallback !== null || bootstrap.auto_detect !== false) throw new Error("locale contract");
    app.csrf = bootstrap.csrf_token;
  })
  .catch(showError);

window.MicrostudyTest = {renderEvidence};
