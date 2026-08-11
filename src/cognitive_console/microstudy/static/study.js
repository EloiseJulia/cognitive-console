"use strict";

const app = {
  csrf: null, locale: null, common: null, sequenceCodes: [], capability: null,
  attemptId: null, current: null, hiddenStarted: null, hiddenMs: 0,
  formal: false, ended: false, pendingRequests: {}, saveExitTrigger: null,
  languages: [], bootstrapReady: false, welcomeReady: false,
  languagePending: false, startPending: false,
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
  const errorKey = error?.message;
  const message = app.common?.errors?.[errorKey]
    || app.common?.errors?.state || "错误 / Error";
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

function startReady() {
  return app.bootstrapReady
    && typeof app.csrf === "string" && app.csrf.length > 0
    && app.welcomeReady
    && typeof app.locale === "string"
    && app.common !== null
    && app.sequenceCodes.length > 0
    && !app.languagePending
    && !app.startPending;
}

function updateReadyControls() {
  document.querySelectorAll('[data-action="choose-language"]').forEach(node => {
    node.disabled = !app.bootstrapReady || app.languagePending;
  });
  const switchButton = document.querySelector('[data-action="switch-language"]');
  if (switchButton) switchButton.disabled = app.languagePending || app.startPending;
  const startButton = document.getElementById("start-button");
  if (startButton) startButton.disabled = !startReady();
}

function requestId() {
  const bytes = crypto.getRandomValues(new Uint8Array(18));
  return Array.from(bytes, value => value.toString(16).padStart(2, "0")).join("");
}

function optionFieldset(name, question, options, config = {}) {
  const fieldset = el("fieldset", {id: `${name}-group`});
  if (config.labelledby) fieldset.setAttribute("aria-labelledby", config.labelledby);
  else fieldset.append(el("legend", {}, question));
  const describedBy = [];
  if (config.helper) {
    const helperId = `${name}-helper`;
    fieldset.append(el("p", {id: helperId, class: "choice-helper"}, config.helper));
    describedBy.push(helperId);
  }
  const errorId = `${name}-error`;
  describedBy.push(errorId);
  fieldset.append(el("p", {
    id: errorId, class: "error choice-error", role: "alert",
  }));
  for (const option of options) {
    const label = el("label", {class: "choice"});
    const input = el("input", {
      type: "radio", name, value: option.id,
      "aria-describedby": describedBy.join(" "),
    });
    label.append(input, document.createTextNode(` ${option.text}`));
    fieldset.append(label);
  }
  return fieldset;
}

function selected(name) {
  return document.querySelector(`input[name="${name}"]:checked`)?.value ?? null;
}

function showChoiceError(name, message) {
  const radios = [...document.querySelectorAll(`input[name="${name}"]`)];
  const error = document.getElementById(`${name}-error`);
  if (error) error.textContent = message;
  radios.forEach(node => node.setAttribute("aria-invalid", "true"));
  radios[0]?.focus();
}

function clearChoiceError(name) {
  const error = document.getElementById(`${name}-error`);
  if (error) error.textContent = "";
  document.querySelectorAll(`input[name="${name}"]`).forEach(node => {
    node.removeAttribute("aria-invalid");
  });
}

function selectedText(name) {
  return document.querySelector(`input[name="${name}"]:checked`)
    ?.closest("label")?.textContent.trim() ?? "";
}

function lockedSummary(state) {
  return el("div", {
    class: "locked-summary", role: "status", "aria-live": "polite",
  }, format(app.common.locked.summary, {state}));
}

function detailsBlock(summary, paragraphs, className = "") {
  const details = el("details", {class: className});
  details.append(el("summary", {}, summary));
  for (const paragraph of paragraphs) details.append(el("p", {}, paragraph));
  return details;
}

async function api(path, data) {
  const nonce = app.pendingRequests[path] || requestId();
  app.pendingRequests[path] = nonce;
  let response;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      response = await fetch(path, {
        method: "POST", cache: "no-store", credentials: "same-origin",
        headers: {
          "Content-Type": "application/json", "X-CSRF-Token": app.csrf,
          ...(app.capability ? {"X-Study-Capability": app.capability} : {}),
        },
        body: JSON.stringify({...data, request_id: nonce}),
      });
      break;
    } catch (error) {
      if (attempt === 2) throw error;
      await new Promise(resolve => setTimeout(resolve, 50));
    }
  }
  const value = await response.json();
  delete app.pendingRequests[path];
  if (!response.ok) throw new Error("state");
  return value;
}

function renderEvidence(cardData) {
  const card = el("article", {class: "evidence-card", "aria-label": cardData.aria_label});
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
  const participantLabel = el("label", {for: "participant-code"}, welcome.participant_code);
  const participantHelp = el(
    "p", {id: "participant-code-help", class: "help"}, welcome.participant_code_help,
  );
  const participantInput = el("input", {
    id: "participant-code", autocomplete: "off", maxlength: "64", required: "",
    "aria-describedby": "participant-code-help",
  });
  const sequenceLabel = el("label", {for: "sequence"}, welcome.sequence);
  const sequenceHelp = el("p", {id: "sequence-help", class: "help"}, welcome.sequence_help);
  sequence.setAttribute("aria-describedby", "sequence-help");
  const privacyDetails = detailsBlock(
    welcome.details_summary, welcome.details.map(row => row.text), "welcome-details",
  );
  const switchButton = el(
    "button", {type: "button", "data-action": "switch-language"},
    welcome.switch_language,
  );
  startPanel.replaceChildren(
    el("h1", {}, welcome.heading),
    el("p", {class: "subtitle"}, welcome.subtitle),
    el("p", {class: "task-size"}, welcome.task_size),
    el("p", {class: "estimate"}, welcome.estimate),
    el("p", {class: "warning"}, welcome.warning),
    el("p", {class: "no-resume"}, welcome.no_resume),
    el("p", {}, welcome.setup_placeholder),
    privacyDetails,
    participantLabel,
    participantHelp,
    participantInput,
    sequenceLabel,
    sequenceHelp,
    sequence,
    el("div", {class: "actions"}),
    el("p", {id: "start-error", class: "error", role: "alert", tabindex: "-1"}),
  );
  startPanel.querySelector(".actions").append(
    el("button", {
      id: "start-button", type: "button", "data-action": "start", disabled: "",
    }, welcome.start),
    switchButton,
  );
  startPanel.hidden = false;
  stage.hidden = true;
  updateReadyControls();
  focusHeading(startPanel);
}

async function chooseLanguage(locale) {
  if (!app.bootstrapReady || app.languagePending || !app.languages.includes(locale)) {
    throw new Error("load");
  }
  app.languagePending = true;
  app.welcomeReady = false;
  updateReadyControls();
  try {
    const response = await fetch(
      `/api/welcome?ui_language=${encodeURIComponent(locale)}`,
      {cache: "no-store", credentials: "same-origin"},
    );
    if (!response.ok) throw new Error("load");
    const selectedBundle = await response.json();
    if (
      selectedBundle.ui_language !== locale
      || !selectedBundle.common
      || !Array.isArray(selectedBundle.sequence_codes)
      || selectedBundle.sequence_codes.length === 0
    ) {
      throw new Error("load");
    }
    app.locale = locale;
    app.common = selectedBundle.common;
    app.sequenceCodes = [...selectedBundle.sequence_codes];
    app.welcomeReady = true;
    if (gate.isConnected) gate.remove();
    showWelcome();
  } finally {
    app.languagePending = false;
    updateReadyControls();
  }
}

function showTutorial() {
  const onboarding = app.common.onboarding;
  const factGuidance = el("ul", {class: "fact-guidance"});
  for (const sentence of onboarding.fact_guidance) {
    factGuidance.append(el("li", {}, sentence));
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
    el("p", {class: "fact-guidance-intro"}, onboarding.fact_guidance_intro),
    factGuidance,
    el("h2", {}, onboarding.states_heading),
    states,
    el("p", {class: "state-distinction"}, onboarding.state_distinction),
    el("h2", {}, onboarding.steps_heading),
    steps,
    el("p", {class: "guard"}, app.common.position_guard),
    el("button", {type: "button", "data-action": "show-practice"}, onboarding.continue_practice),
  );
}

function showPractice() {
  const practice = app.common.practice;
  const card = {
    aria_label: practice.card_aria,
    rows: practice.facts.map(row => ({label: row.label, body: row.body})),
  };
  replaceStage(
    el("h1", {}, practice.heading),
    el("p", {class: "context-label"}, practice.notice),
    el("p", {class: "guard"}, app.common.position_guard),
    renderEvidence(card),
    el("div", {id: "practice-q1-area"}),
    el("div", {id: "practice-next"}),
  );
  document.getElementById("practice-q1-area").append(
    optionFieldset("practice-q1", practice.q1.text, practice.q1.options),
    el("button", {type: "button", "data-action": "practice-q1"}, practice.submit_q1),
  );
}

async function practiceQ1(button) {
  const answer = selected("practice-q1");
  if (!answer) {
    showChoiceError("practice-q1", app.common.errors.required_q1);
    return;
  }
  clearChoiceError("practice-q1");
  const state = selectedText("practice-q1");
  button.disabled = true;
  await api("/api/practice", {attempt_id: app.attemptId, step: "q1", answer});
  document.getElementById("practice-q1-area").replaceChildren(lockedSummary(state));
  const practice = app.common.practice;
  document.getElementById("practice-next").append(
    el("h2", {id: "practice-q2-heading", tabindex: "-1"}, practice.q2.text),
    optionFieldset("practice-q2", practice.q2.text, practice.q2.options, {
      labelledby: "practice-q2-heading",
    }),
    el("button", {type: "button", "data-action": "practice-q2"}, practice.submit_q2),
  );
  document.getElementById("practice-q2-heading").focus();
}

async function practiceQ2(button) {
  const answer = selected("practice-q2");
  if (!answer) {
    showChoiceError("practice-q2", app.common.errors.required_q2);
    return;
  }
  clearChoiceError("practice-q2");
  button.disabled = true;
  const response = await api("/api/practice", {
    attempt_id: app.attemptId, step: "q2", answer,
  });
  app.current = response;
  const transition = app.common.transition;
  const steps = el("ol");
  for (const step of transition.steps) steps.append(el("li", {}, step));
  replaceStage(
    el("h1", {}, transition.heading),
    el("p", {class: "feedback"}, response.feedback),
    el("p", {}, transition.intro),
    steps,
    el("p", {class: "guard"}, app.common.position_guard),
    el("button", {type: "button", "data-action": "begin-formal"}, app.common.practice.begin_formal),
  );
}

function showTrial() {
  setFormal(true);
  const trial = app.current;
  app.hiddenMs = 0;
  app.hiddenStarted = document.hidden ? performance.now() : null;
  const heading = format(app.common.progress.record_heading, {
    current: trial.trial_index + 1,
  });
  const progress = format(app.common.progress.question_progress, {
    question: 1, block: trial.block,
  });
  replaceStage(
    el("h1", {}, heading),
    el("p", {id: "question-progress", class: "progress"}, progress),
    detailsBlock(trial.context.summary, [trial.context.body], "record-context"),
    el("p", {class: "guard"}, app.common.position_guard),
    renderEvidence(trial.card),
    el("div", {id: "q1-area"}),
    el("div", {id: "q2-area"}),
  );
  document.getElementById("q1-area").append(
    optionFieldset("formal-q1", trial.q1.text, trial.q1.options),
    el("button", {type: "button", "data-action": "formal-q1"}, app.common.buttons.submit_q1),
  );
}

async function formalQ1(button) {
  const answer = selected("formal-q1");
  if (!answer) {
    showChoiceError("formal-q1", app.common.errors.required_q1);
    return;
  }
  clearChoiceError("formal-q1");
  const state = selectedText("formal-q1");
  button.disabled = true;
  const response = await api("/api/q1", {attempt_id: app.attemptId, answer});
  document.getElementById("q1-area").replaceChildren(lockedSummary(state));
  document.getElementById("question-progress").textContent = format(
    app.common.progress.question_progress, {question: 2, block: app.current.block},
  );
  const q2Area = document.getElementById("q2-area");
  const q2Heading = el("h2", {id: "q2-heading", tabindex: "-1"}, response.q2.text);
  q2Area.append(
    q2Heading,
    optionFieldset("formal-q2", response.q2.text, response.q2.options, {
      labelledby: "q2-heading", helper: response.q2.helper,
    }),
    el("button", {type: "button", "data-action": "formal-q2"}, app.common.buttons.submit_q2),
  );
  q2Heading.focus();
}

async function formalQ2(button) {
  const answer = selected("formal-q2");
  if (!answer) {
    showChoiceError("formal-q2", app.common.errors.required_q2);
    return;
  }
  clearChoiceError("formal-q2");
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
  if (!skip && !answer) {
    showChoiceError("ease", app.common.errors.required_choice);
    return;
  }
  clearChoiceError("ease");
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
  if (!skip && !answer) {
    showChoiceError("diagnostic", app.common.errors.required_choice);
    return;
  }
  clearChoiceError("diagnostic");
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

function saveExitDialog() {
  let dialog = document.getElementById("save-exit-dialog");
  if (dialog) return dialog;
  const copy = app.common.save_exit;
  dialog = el("dialog", {
    id: "save-exit-dialog", "aria-labelledby": "save-exit-heading",
    "aria-describedby": "save-exit-description",
  });
  const consequences = el("ul");
  for (const consequence of copy.consequences) {
    consequences.append(el("li", {}, consequence));
  }
  dialog.append(
    el("h2", {id: "save-exit-heading"}, copy.heading),
    el("p", {id: "save-exit-description"}, copy.intro),
    consequences,
    el("div", {class: "actions"}),
  );
  dialog.lastChild.append(
    el("button", {
      type: "button", class: "secondary", "data-action": "cancel-save-exit",
    }, copy.cancel),
    el("button", {
      type: "button", "data-action": "confirm-save-exit",
    }, copy.confirm),
  );
  dialog.addEventListener("cancel", event => {
    event.preventDefault();
    closeSaveExitDialog();
  });
  document.body.append(dialog);
  return dialog;
}

function showSaveExitDialog(button) {
  app.saveExitTrigger = button;
  const dialog = saveExitDialog();
  dialog.showModal();
  dialog.querySelector('[data-action="cancel-save-exit"]').focus();
}

function closeSaveExitDialog() {
  const dialog = document.getElementById("save-exit-dialog");
  if (dialog?.open) dialog.close();
  app.saveExitTrigger?.focus();
  app.saveExitTrigger = null;
}

async function saveAndExit(button) {
  button.disabled = true;
  const response = await api("/api/save-exit", {attempt_id: app.attemptId});
  if (response.phase !== "export_ready") throw new Error("export_not_ready");
  const dialog = document.getElementById("save-exit-dialog");
  if (dialog?.open) dialog.close();
  app.saveExitTrigger = null;
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
  if (!startReady()) return;
  app.startPending = true;
  updateReadyControls();
  try {
    const response = await api("/api/start", {
      participant_code: document.getElementById("participant-code").value.trim(),
      sequence: document.getElementById("sequence").value,
      ui_language: app.locale,
    });
    if (
      response.ui_language !== app.locale
      || typeof response.attempt_id !== "string" || response.attempt_id.length === 0
      || typeof response.capability !== "string" || response.capability.length === 0
    ) {
      throw new Error("state");
    }
    app.attemptId = response.attempt_id;
    app.capability = response.capability;
    startPanel.replaceChildren();
    startPanel.hidden = true;
    showTutorial();
  } finally {
    app.startPending = false;
    updateReadyControls();
  }
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
    "save-exit": () => showSaveExitDialog(button),
    "cancel-save-exit": () => closeSaveExitDialog(),
    "confirm-save-exit": () => saveAndExit(button),
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

document.addEventListener("change", event => {
  if (event.target.matches('input[type="radio"]')) clearChoiceError(event.target.name);
});

fetch("/api/bootstrap", {cache: "no-store", credentials: "same-origin"})
  .then(response => response.ok ? response.json() : Promise.reject(new Error("bootstrap")))
  .then(bootstrap => {
    if (
      bootstrap.fallback !== null
      || bootstrap.auto_detect !== false
      || typeof bootstrap.csrf_token !== "string"
      || bootstrap.csrf_token.length === 0
      || !Array.isArray(bootstrap.languages)
    ) {
      throw new Error("locale contract");
    }
    app.csrf = bootstrap.csrf_token;
    app.languages = bootstrap.languages.map(row => row.id);
    app.bootstrapReady = true;
    updateReadyControls();
  })
  .catch(showError);

window.MicrostudyTest = {renderEvidence};
