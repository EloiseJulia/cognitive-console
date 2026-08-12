"use strict";

const app = {
  csrf: null,
  locale: null,
  common: null,
  sequenceCodes: [],
  capability: null,
  attemptId: null,
  current: null,
  hiddenStarted: null,
  hiddenMs: 0,
  lockedChoice: null,
  formal: false,
  ended: false,
  pendingRequests: {},
  saveExitTrigger: null,
  languages: [],
  bootstrapReady: false,
  welcomeReady: false,
  languagePending: false,
  startPending: false,
  practiceLevel: 50,
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
    (result, [key, value]) => result.replaceAll(`{${key}}`, String(value)),
    text,
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
  const error = el("p", {
    id: "stage-error", class: "error", role: "alert", tabindex: "-1",
  });
  stage.replaceChildren(error, ...nodes);
  stage.hidden = false;
  focusHeading(stage);
}

function showError(error) {
  const message = app.common?.errors?.[error?.message]
    || app.common?.errors?.state
    || "错误 / Error";
  const target = gate.isConnected
    ? document.getElementById("gate-error")
    : (startPanel.hidden
      ? document.getElementById("stage-error")
      : document.getElementById("start-error"));
  if (!target) return;
  target.textContent = message;
  target.focus();
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

async function api(path, data) {
  const nonce = app.pendingRequests[path] || requestId();
  app.pendingRequests[path] = nonce;
  let response;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      response = await fetch(path, {
        method: "POST",
        cache: "no-store",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": app.csrf,
          ...(app.capability
            ? {"X-Study-Capability": app.capability}
            : {}),
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
  if (!response.ok) throw new Error("state");
  delete app.pendingRequests[path];
  return value;
}

function optionFieldset(name, question, options, labelledby = null) {
  const fieldset = el("fieldset", {id: `${name}-group`});
  if (labelledby) fieldset.setAttribute("aria-labelledby", labelledby);
  else fieldset.append(el("legend", {}, question));
  const errorId = `${name}-error`;
  fieldset.append(el("p", {
    id: errorId, class: "error choice-error", role: "alert",
  }));
  for (const option of options) {
    const label = el("label", {class: "choice"});
    const input = el("input", {
      type: "radio", name, value: option.id, "aria-describedby": errorId,
    });
    label.append(input, document.createTextNode(` ${option.text}`));
    fieldset.append(label);
  }
  return fieldset;
}

function selected(name) {
  return document.querySelector(`input[name="${name}"]:checked`)?.value ?? null;
}

function selectedText(name) {
  return document.querySelector(`input[name="${name}"]:checked`)
    ?.closest("label")?.textContent.trim() ?? "";
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

function badge(text) {
  return el("span", {class: "badge"}, text);
}

function productCard(product, sourceBadge, enabled = false) {
  const card = el("section", {class: "product-card"});
  card.append(
    badge(sourceBadge),
    el("h2", {}, product.title),
    el("p", {}, product.context),
  );
  const knobLine = el("div", {class: "knob-line"});
  const label = el("label", {for: enabled ? "practice-knob" : "ticket-knob"}, product.knob);
  const knob = el("input", {
    id: enabled ? "practice-knob" : "ticket-knob",
    type: "range", min: "0", max: "100", value: enabled ? String(app.practiceLevel) : "50",
    "aria-label": product.knob,
  });
  if (!enabled) {
    knob.disabled = true;
    knob.setAttribute("aria-disabled", "true");
  }
  knobLine.append(label, knob);
  card.append(knobLine);
  if (product.knob_note) card.append(el("p", {class: "muted"}, product.knob_note));
  return card;
}

function renderOutputs(outputs) {
  const container = el("div", {class: "outputs"});
  for (const output of outputs.slice(0, 2)) {
    const card = el("article", {class: "output-card"});
    card.append(badge(output.badge), el("p", {}, output.text));
    container.append(card);
  }
  return container;
}

function renderCard(cardData) {
  const card = el("article", {
    class: "evidence-card", "aria-label": cardData.aria_label,
  });
  if (Array.isArray(cardData.groups)) {
    const groups = el("div", {class: "evidence-groups"});
    for (const groupData of cardData.groups) {
      const group = el("section", {class: "evidence-group"});
      const list = el("ul");
      for (const fact of groupData.facts) list.append(el("li", {}, fact));
      group.append(el("h3", {}, groupData.heading), list);
      groups.append(group);
    }
    card.append(groups);
    return card;
  }
  const rows = el("dl", {class: "evidence-rows"});
  for (const rowData of cardData.rows) {
    const row = el("div", {class: "evidence-row"});
    row.append(
      el("dt", {class: "evidence-label"}, rowData.label),
      el("dd", {class: "evidence-body"}, rowData.body),
    );
    rows.append(row);
  }
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
  for (const code of app.sequenceCodes) {
    sequence.append(el("option", {value: code}, code));
  }
  const participant = el("input", {
    id: "participant-code",
    autocomplete: "off",
    maxlength: "64",
    required: "",
    "aria-describedby": "participant-code-help",
  });
  sequence.setAttribute("aria-describedby", "sequence-help");
  const details = el("details");
  details.append(el("summary", {}, welcome.details_summary));
  for (const text of welcome.details) details.append(el("p", {}, text));
  const actions = el("div", {class: "actions"});
  actions.append(
    el("button", {
      id: "start-button", type: "button", "data-action": "start", disabled: "",
    }, welcome.start),
    el("button", {
      type: "button", class: "secondary", "data-action": "switch-language",
    }, welcome.switch_language),
  );
  startPanel.replaceChildren(
    el("h1", {}, welcome.heading),
    el("p", {class: "subtitle"}, welcome.subtitle),
    el("p", {}, welcome.task_size),
    el("p", {class: "warning"}, welcome.warning),
    el("p", {class: "no-resume"}, welcome.no_resume),
    details,
    el("label", {for: "participant-code"}, welcome.participant_code),
    el("p", {id: "participant-code-help", class: "help"}, welcome.participant_code_help),
    participant,
    el("label", {for: "sequence"}, welcome.sequence),
    el("p", {id: "sequence-help", class: "help"}, welcome.sequence_help),
    sequence,
    actions,
    el("p", {id: "start-error", class: "error", role: "alert", tabindex: "-1"}),
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
      || selectedBundle.sequence_codes.length !== 12
    ) throw new Error("load");
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

function showBriefing() {
  const briefing = app.common.briefing;
  const policy = el("ul", {class: "policy-list"});
  for (const option of briefing.policy) policy.append(el("li", {}, option.text));
  const flow = el("ol", {class: "briefing-flow"});
  for (const step of briefing.flow) flow.append(el("li", {}, step));
  replaceStage(
    el("h1", {}, briefing.heading),
    el("p", {}, briefing.role),
    el("h2", {}, briefing.policy_heading),
    policy,
    flow,
    el("p", {class: "cca-note"}, briefing.cca),
    el("button", {
      type: "button", "data-action": "show-practice",
    }, briefing.continue_practice),
  );
}

function practicePreviewParameters(kind) {
  const level = app.practiceLevel / 100;
  return kind === "candidate"
    ? {toneHz: 215 + 50 * level, noise: 0.12 - 0.08 * level}
    : {toneHz: 220, noise: 0.055};
}

function playPractice(kind) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;
  const context = new AudioContextClass();
  const params = practicePreviewParameters(kind);
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  const buffer = context.createBuffer(1, Math.round(context.sampleRate * 0.55), context.sampleRate);
  const noise = buffer.getChannelData(0);
  for (let index = 0; index < noise.length; index += 1) {
    noise[index] = (Math.random() * 2 - 1) * params.noise;
  }
  const noiseSource = context.createBufferSource();
  noiseSource.buffer = buffer;
  oscillator.frequency.value = params.toneHz;
  gain.gain.setValueAtTime(0.0001, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.10, context.currentTime + 0.03);
  gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.52);
  oscillator.connect(gain).connect(context.destination);
  noiseSource.connect(gain);
  oscillator.start();
  noiseSource.start();
  oscillator.stop(context.currentTime + 0.55);
  noiseSource.stop(context.currentTime + 0.55);
  setTimeout(() => context.close(), 650);
}

function showPractice() {
  const practice = app.common.practice;
  const product = {
    title: practice.heading,
    context: practice.context,
    knob: practice.knob,
  };
  const rows = practice.facts.map((body, index) => ({
    label: app.locale === "en" ? `Fact ${index + 1}` : `事实 ${index + 1}`,
    body,
  }));
  const audioActions = el("div", {class: "audio-actions"});
  audioActions.append(
    el("button", {
      type: "button", class: "secondary", "data-action": "play-preset",
    }, practice.preset),
    el("button", {
      type: "button", class: "secondary", "data-action": "play-candidate",
    }, practice.candidate),
  );
  replaceStage(
    el("h1", {}, practice.heading),
    productCard(product, app.common.badges.simulated, true),
    audioActions,
    renderCard({aria_label: practice.heading, rows}),
    el("div", {id: "practice-q1-area"}),
    el("div", {id: "practice-q2-area"}),
  );
  document.getElementById("practice-knob").addEventListener("input", event => {
    app.practiceLevel = Number(event.target.value);
  });
  document.getElementById("practice-q1-area").append(
    optionFieldset("practice-q1", practice.q1, app.common.q1.options),
    el("button", {
      type: "button", "data-action": "practice-q1",
    }, practice.submit_q1),
  );
}

async function practiceQ1(button) {
  const answer = selected("practice-q1");
  if (!answer) {
    showChoiceError("practice-q1", app.common.errors.required_q1);
    return;
  }
  clearChoiceError("practice-q1");
  button.disabled = true;
  await api("/api/practice", {
    attempt_id: app.attemptId, step: "q1", answer,
  });
  const choice = selectedText("practice-q1");
  document.getElementById("practice-q1-area").replaceChildren(
    el("p", {class: "locked-summary", role: "status"}, format(app.common.locked, {choice})),
  );
  const practice = app.common.practice;
  document.getElementById("practice-q2-area").append(
    el("h2", {id: "practice-q2-heading", tabindex: "-1"}, practice.q2),
    optionFieldset("practice-q2", practice.q2, practice.q2_options, "practice-q2-heading"),
    el("button", {
      type: "button", "data-action": "practice-q2",
    }, practice.submit_q2),
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
  app.current = await api("/api/practice", {
    attempt_id: app.attemptId, step: "q2", answer,
  });
  replaceStage(
    el("h1", {}, app.common.practice.heading),
    el("p", {class: "practice-note"}, app.current.feedback),
    el("button", {
      type: "button", "data-action": "begin-formal",
    }, app.common.practice.begin_formal),
  );
}

function showTrial() {
  setFormal(true);
  app.hiddenMs = 0;
  app.hiddenStarted = document.hidden ? performance.now() : null;
  app.lockedChoice = null;
  const trial = app.current;
  const shell = el("div", {class: "ticket-shell"});
  shell.append(
    el("p", {class: "ticket-code"}, trial.ticket_code),
    productCard(trial.product, trial.source_badge),
    renderOutputs(trial.outputs),
    renderCard(trial.card),
  );
  shell.append(el("div", {id: "q1-area"}), el("div", {id: "q2-area"}));
  replaceStage(
    el("h1", {}, format(app.common.progress.ticket, {
      current: trial.trial_index + 1,
    })),
    el("p", {class: "progress"}, trial.product.title),
    shell,
  );
  document.getElementById("q1-area").append(
    optionFieldset("formal-q1", trial.q1.text, trial.q1.options),
    el("button", {
      type: "button", "data-action": "formal-q1",
    }, app.common.buttons.submit_q1),
  );
}

async function formalQ1(button) {
  const answer = selected("formal-q1");
  if (!answer) {
    showChoiceError("formal-q1", app.common.errors.required_q1);
    return;
  }
  clearChoiceError("formal-q1");
  app.lockedChoice = selectedText("formal-q1");
  button.disabled = true;
  const response = await api("/api/q1", {
    attempt_id: app.attemptId, answer,
  });
  document.getElementById("q1-area").replaceChildren(
    el("p", {class: "locked-summary", role: "status"}, format(
      app.common.locked, {choice: app.lockedChoice},
    )),
  );
  const heading = el("h2", {id: "q2-heading", tabindex: "-1"}, response.q2.text);
  document.getElementById("q2-area").append(
    heading,
    optionFieldset("formal-q2", response.q2.text, response.q2.options, "q2-heading"),
    el("button", {
      type: "button", "data-action": "formal-q2",
    }, app.common.buttons.submit_q2),
  );
  heading.focus();
}

async function formalQ2(button) {
  const answer = selected("formal-q2");
  if (!answer) {
    showChoiceError("formal-q2", app.common.errors.required_q2);
    return;
  }
  clearChoiceError("formal-q2");
  button.disabled = true;
  const hiddenMs = Math.round(app.hiddenMs + (
    app.hiddenStarted === null ? 0 : performance.now() - app.hiddenStarted
  ));
  const response = await api("/api/q2", {
    attempt_id: app.attemptId, answer, hidden_ms: hiddenMs,
  });
  if (response.phase !== "preview") throw new Error("state");
  showPreview();
}

function showPreview() {
  const preview = app.common.preview;
  const section = el("section", {class: "decision-preview"});
  section.append(el("h2", {}, preview.heading));
  replaceStage(
    el("h1", {}, preview.heading),
    section,
  );
  section.append(
    el("p", {}, format(preview.body, {choice: app.lockedChoice})),
    el("button", {
      type: "button", "data-action": "continue-preview",
    }, preview.continue),
  );
}

async function continuePreview(button) {
  button.disabled = true;
  app.current = await api("/api/continue", {attempt_id: app.attemptId});
  if (app.current.phase === "ready_complete") {
    await api("/api/complete", {attempt_id: app.attemptId});
    showExportScreen(true);
    return;
  }
  showTrial();
}

function showExportScreen(complete) {
  app.ended = true;
  setFormal(false);
  const copy = app.common.export;
  replaceStage(
    el("h1", {}, complete ? copy.complete_heading : copy.partial_heading),
    ...(complete
      ? [el("p", {}, app.common.debrief), el("p", {}, copy.complete_count)]
      : [el("p", {}, copy.partial_ready)]),
    el("p", {id: "export-status"}, copy.ready),
    el("p", {}, copy.retry),
    el("div", {class: "actions"}),
  );
  stage.lastChild.append(
    el("button", {
      type: "button", "data-action": "download-json",
    }, app.common.buttons.download_json),
    el("button", {
      type: "button", "data-action": "download-csv",
    }, app.common.buttons.download_csv),
    el("button", {
      type: "button", "data-action": "finish",
    }, app.common.buttons.finish),
  );
}

async function downloadExport(outputFormat) {
  const response = await fetch(
    `/api/export?attempt_id=${encodeURIComponent(app.attemptId)}&format=${outputFormat}`,
    {
      cache: "no-store",
      credentials: "same-origin",
      headers: {"X-Study-Capability": app.capability},
    },
  );
  if (!response.ok) throw new Error("download");
  const blob = await response.blob();
  const link = document.createElement("a");
  link.download = `microstudy-v9-${app.attemptId}.${outputFormat}`;
  link.href = URL.createObjectURL(blob);
  document.body.append(link);
  link.click();
  const url = link.href;
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  document.getElementById("export-status").textContent = format(
    app.common.export.download_started,
    {format: outputFormat.toUpperCase()},
  );
}

function saveExitDialog() {
  let dialog = document.getElementById("save-exit-dialog");
  if (dialog) return dialog;
  const copy = app.common.save_exit;
  dialog = el("dialog", {
    id: "save-exit-dialog",
    "aria-labelledby": "save-exit-heading",
    "aria-describedby": "save-exit-description",
  });
  const consequences = el("ul");
  for (const text of copy.consequences) consequences.append(el("li", {}, text));
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
  button.disabled = true;
  try {
    const response = await api("/api/start", {
      participant_code: document.getElementById("participant-code").value.trim(),
      sequence: document.getElementById("sequence").value,
      ui_language: app.locale,
    });
    if (
      response.ui_language !== app.locale
      || typeof response.attempt_id !== "string"
      || typeof response.capability !== "string"
    ) throw new Error("state");
    app.attemptId = response.attempt_id;
    app.capability = response.capability;
    startPanel.replaceChildren();
    startPanel.hidden = true;
    showBriefing();
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
    "play-preset": () => playPractice("preset"),
    "play-candidate": () => playPractice("candidate"),
    "practice-q1": () => practiceQ1(button),
    "practice-q2": () => practiceQ2(button),
    "begin-formal": () => showTrial(),
    "formal-q1": () => formalQ1(button),
    "formal-q2": () => formalQ2(button),
    "continue-preview": () => continuePreview(button),
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
  if (document.hidden && app.hiddenStarted === null) {
    app.hiddenStarted = performance.now();
  }
  if (!document.hidden && app.hiddenStarted !== null) {
    app.hiddenMs += performance.now() - app.hiddenStarted;
    app.hiddenStarted = null;
  }
});

document.addEventListener("change", event => {
  if (event.target.matches('input[type="radio"]')) {
    clearChoiceError(event.target.name);
  }
});

fetch("/api/bootstrap", {cache: "no-store", credentials: "same-origin"})
  .then(response => (
    response.ok ? response.json() : Promise.reject(new Error("load"))
  ))
  .then(bootstrap => {
    if (
      bootstrap.fallback !== null
      || bootstrap.auto_detect !== false
      || bootstrap.minimum_width_px !== 1280
      || typeof bootstrap.csrf_token !== "string"
      || !Array.isArray(bootstrap.languages)
    ) throw new Error("load");
    app.csrf = bootstrap.csrf_token;
    app.languages = bootstrap.languages.map(row => row.id);
    app.bootstrapReady = true;
    updateReadyControls();
  })
  .catch(showError);

window.MicrostudyTest = {
  renderCard,
  practicePreviewParameters,
};
