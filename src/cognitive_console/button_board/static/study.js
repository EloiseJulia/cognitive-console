import { noPrivateKeys, uniqueIds } from "./study_core.mjs";

const gate = document.querySelector("#language-gate");
const startPanel = document.querySelector("#start");
const stage = document.querySelector("#stage");
const header = document.querySelector("#site-header");
const footer = document.querySelector("#site-footer");
const saveButton = document.querySelector("#save-exit-button");
const saveDialog = document.querySelector("#save-exit-dialog");

const app = {
  csrf: null,
  materials: null,
  locale: null,
  attemptId: null,
  capability: null,
  current: null,
  selectedQ1Text: null,
  ready: false,
};

window.ButtonBoardTest = app;

function el(tag, attrs = {}, text = null) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (value !== null) node.setAttribute(key, value);
  }
  if (text !== null) node.textContent = text;
  return node;
}

function focusHeading(container) {
  const heading = container.querySelector("h1, h2");
  if (heading) {
    heading.tabIndex = -1;
    heading.focus();
  }
}

function replaceStage(...nodes) {
  stage.replaceChildren(...nodes);
  gate.hidden = true;
  startPanel.hidden = true;
  stage.hidden = false;
  header.hidden = false;
  footer.hidden = false;
  requestAnimationFrame(() => focusHeading(stage));
}

function requestId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)))
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("");
}

async function api(path, data = null) {
  const options = { headers: {} };
  if (data !== null) {
    options.method = "POST";
    options.body = JSON.stringify({ ...data, request_id: requestId() });
    options.headers["Content-Type"] = "application/json";
    options.headers["X-CSRF-Token"] = app.csrf;
    if (app.capability) options.headers["X-Study-Capability"] = app.capability;
  } else if (path.startsWith("/api/export")) {
    options.headers["X-Study-Capability"] = app.capability;
  }
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = `${response.status}`;
    try { message = (await response.json()).error || message; } catch {}
    throw new Error(message);
  }
  const value = await response.json();
  if (!noPrivateKeys(value)) throw new Error("private answer material received");
  return value;
}

function showError(container, message = null) {
  const target = container.querySelector(".error") || container;
  target.textContent = message || app.materials.common.errors.generic;
  target.focus?.();
}

function setChrome() {
  const common = app.materials.common;
  document.querySelector("#header-title").textContent = common.title;
  document.querySelector("#fiction-banner").textContent = common.disclaimer;
  saveButton.textContent = common.save_exit.button;
  saveButton.hidden = true;
  document.querySelector("#save-exit-heading").textContent = common.save_exit.heading;
  document.querySelector("#save-exit-body").textContent = common.save_exit.body;
  saveDialog.querySelector('[data-action="cancel-save-exit"]').textContent = common.save_exit.cancel;
  saveDialog.querySelector('[data-action="confirm-save-exit"]').textContent = common.save_exit.confirm;
  footer.textContent = common.draft;
}

function showWelcome() {
  const common = app.materials.common;
  const heading = el("h1", {}, common.welcome.heading);
  const goal = el("p", { class: "subtitle" }, common.welcome.goal);
  const steps = el("p", {}, common.welcome.steps);
  const fiction = el("p", { class: "fiction-notice" }, common.disclaimer);
  const note = el("p", {}, common.welcome.fiction_note);
  const local = el("p", {}, common.welcome.local_note);
  const draft = el("p", { class: "draft" }, common.draft);
  const label = el("label", { for: "participant-code" }, common.welcome.participant_label);
  const input = el("input", {
    id: "participant-code", type: "text", maxlength: "64", autocomplete: "off",
    "aria-describedby": "participant-help",
  });
  const help = el("p", { id: "participant-help", class: "muted" }, common.welcome.participant_help);
  const error = el("p", { id: "start-error", class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", { type: "button", dataset: { action: "start" }, onclick: startStudy }, common.welcome.start);
  startPanel.replaceChildren(heading, goal, steps, fiction, note, local, draft, label, input, help, error, button);
  gate.hidden = true;
  stage.hidden = true;
  startPanel.hidden = false;
  header.hidden = false;
  footer.hidden = false;
  focusHeading(startPanel);
}

async function chooseLanguage(locale) {
  try {
    const materials = await api(`/api/welcome?selected_locale=${encodeURIComponent(locale)}`);
    app.materials = materials;
    app.locale = locale;
    document.documentElement.lang = locale;
    document.title = materials.common.title;
    setChrome();
    showWelcome();
  } catch (error) {
    document.querySelector("#gate-error").textContent = String(error.message || error);
  }
}

async function startStudy() {
  const input = document.querySelector("#participant-code");
  const code = input.value.trim();
  if (!/^[A-Za-z0-9._-]{1,64}$/.test(code)) {
    showError(startPanel, app.materials.common.welcome.participant_help);
    input.focus();
    return;
  }
  try {
    const response = await api("/api/start", {
      participant_code: code,
      selected_locale: app.locale,
    });
    app.attemptId = response.attempt_id;
    app.capability = response.capability;
    showTutorial();
  } catch (error) {
    showError(startPanel, String(error.message || error));
  }
}

function showTutorial() {
  const copy = app.materials.common.tutorial;
  const heading = el("h1", {}, copy.heading);
  const grid = el("div", { class: "tutorial-grid" });
  const frame1 = el("section", { class: "tutorial-frame" });
  frame1.append(
    el("h2", {}, copy.frame_1_heading),
    el("p", {}, copy.frame_1),
    el("p", { class: "muted" }, copy.frame_1_demo),
  );
  const lights = el("div", { class: "demo-lights", "aria-hidden": "true" });
  lights.append(el("div", { class: "demo-light" }), el("div", { class: "demo-light" }));
  const counts = el("table", { class: "demo-counts", "aria-label": copy.frame_1_demo });
  const headerRow = el("tr");
  headerRow.append(el("th", {}, "A"), el("th", {}, "B"));
  const countRow = el("tr");
  countRow.append(el("td", {}, "3 / 5"), el("td", {}, "4 / 5"));
  counts.append(headerRow, countRow);
  frame1.append(lights, counts);
  const frame2 = el("section", { class: "tutorial-frame" });
  frame2.append(el("h2", {}, copy.frame_2_heading), el("p", {}, copy.frame_2));
  const frame3 = el("section", { class: "tutorial-frame" });
  frame3.append(el("h2", {}, copy.frame_3_heading), el("p", {}, copy.frame_3));
  grid.append(frame1, frame2, frame3);
  const button = el("button", {
    type: "button", dataset: { action: "show-practice" }, onclick: showPractice,
  }, copy.show_practice);
  replaceStage(heading, el("p", { class: "fiction-notice" }, app.materials.common.disclaimer), grid, button);
}

function recordCard(payload) {
  const labels = app.materials.common.record_labels;
  const card = el("article", { class: "record-card", "aria-label": payload.title });
  card.append(el("h2", {}, payload.title));
  const list = el("dl", { class: "record-grid" });
  for (const field of ["situation", "goal", "existing", "new_item", "respond", "comparison", "amount", "effects", "conditions"]) {
    const row = el("div", { class: "record-row" });
    row.append(el("dt", {}, labels[field]), el("dd", {}, payload.record[field]));
    list.append(row);
  }
  card.append(list);
  return card;
}

function q1Fieldset(options, name) {
  if (!uniqueIds(options)) throw new Error("duplicate Q1 option IDs");
  const fieldset = el("fieldset");
  fieldset.append(el("legend", {}, app.materials.common.questions.q1));
  const grid = el("div", { class: "board-grid" });
  for (const row of options) {
    const label = el("label", { class: "board-choice" });
    const input = el("input", { type: "radio", name, value: row.id });
    const copy = el("span", { class: "board-copy" });
    copy.append(el("span", { class: "board-label" }, row.label), el("span", {}, row.description));
    label.append(input, copy);
    grid.append(label);
  }
  fieldset.append(grid);
  return fieldset;
}

function choiceFieldset(prompt, options, name) {
  if (!uniqueIds(options)) throw new Error("duplicate option IDs");
  const fieldset = el("fieldset");
  fieldset.append(el("legend", {}, prompt));
  const list = el("div", { class: "choice-list" });
  for (const row of options) {
    const label = el("label", { class: "choice" });
    label.append(el("input", { type: "radio", name, value: row.id }), el("span", {}, row.text));
    list.append(label);
  }
  fieldset.append(list);
  return fieldset;
}

function selected(name) {
  return document.querySelector(`input[name="${name}"]:checked`);
}

function selectedLabel(name) {
  const input = selected(name);
  return input?.closest("label")?.innerText || "";
}

function cardShell(payload, headingText) {
  const heading = el("h1", {}, headingText || payload.progress);
  const shell = el("div", { class: "record-shell" });
  shell.append(el("p", { class: "progress" }, payload.progress), recordCard(payload));
  return { heading, shell };
}

function showPractice() {
  app.current = {
    ...app.materials.practice,
    progress: app.materials.common.progress.practice,
    q1_options: app.materials.common.q1_options,
  };
  renderQ1("practice");
}

function renderQ1(mode) {
  saveButton.hidden = mode === "practice";
  const { heading, shell } = cardShell(app.current);
  const name = `${mode}-q1`;
  shell.append(q1Fieldset(app.current.q1_options, name));
  const error = el("p", { class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", {
    type: "button", dataset: { action: `${mode}-q1` },
    onclick: () => submitQ1(mode, name),
  }, app.materials.common.questions.stamp);
  shell.append(error, button);
  replaceStage(heading, el("p", { class: "fiction-notice" }, app.materials.common.disclaimer), shell);
}

async function submitQ1(mode, name) {
  const answer = selected(name);
  if (!answer) {
    showError(stage, app.materials.common.questions.choice_required);
    return;
  }
  app.selectedQ1Text = selectedLabel(name);
  try {
    const response = mode === "practice"
      ? await api("/api/practice", { attempt_id: app.attemptId, step: "q1", answer: answer.value })
      : await api("/api/q1", { attempt_id: app.attemptId, answer: answer.value });
    renderScope(mode, response.scope_options);
  } catch (error) {
    showError(stage, String(error.message || error));
  }
}

function lockedSummary() {
  const box = el("div", { class: "locked-summary", role: "status" });
  box.append(el("strong", {}, app.materials.common.questions.locked), el("p", {}, app.selectedQ1Text));
  return box;
}

function renderScope(mode, options) {
  const { heading, shell } = cardShell(app.current);
  shell.append(lockedSummary());
  const name = `${mode}-scope`;
  shell.append(choiceFieldset(app.materials.common.questions.scope, options, name));
  const error = el("p", { class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", {
    type: "button", dataset: { action: `${mode}-scope` },
    onclick: () => submitScope(mode, name),
  }, app.materials.common.questions.submit_scope);
  shell.append(error, button);
  replaceStage(heading, el("p", { class: "fiction-notice" }, app.materials.common.disclaimer), shell);
}

async function submitScope(mode, name) {
  const answer = selected(name);
  if (!answer) {
    showError(stage, app.materials.common.questions.choice_required);
    return;
  }
  try {
    const response = mode === "practice"
      ? await api("/api/practice", { attempt_id: app.attemptId, step: "scope", answer: answer.value })
      : await api("/api/scope", { attempt_id: app.attemptId, answer: answer.value });
    renderReason(mode, response.reason_options);
  } catch (error) {
    showError(stage, String(error.message || error));
  }
}

function renderReason(mode, options) {
  const { heading, shell } = cardShell(app.current);
  shell.append(lockedSummary());
  const name = `${mode}-reason`;
  shell.append(choiceFieldset(app.materials.common.questions.reason, options, name));
  const error = el("p", { class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", {
    type: "button", dataset: { action: `${mode}-reason` },
    onclick: () => submitReason(mode, name),
  }, app.materials.common.questions.submit_reason);
  shell.append(error, button);
  replaceStage(heading, el("p", { class: "fiction-notice" }, app.materials.common.disclaimer), shell);
}

async function submitReason(mode, name) {
  const answer = selected(name);
  if (!answer) {
    showError(stage, app.materials.common.questions.choice_required);
    return;
  }
  try {
    const response = mode === "practice"
      ? await api("/api/practice", { attempt_id: app.attemptId, step: "reason", answer: answer.value })
      : await api("/api/reason", { attempt_id: app.attemptId, answer: answer.value });
    if (mode === "practice") showPracticeFeedback(response.feedback);
    else routeNext(response);
  } catch (error) {
    showError(stage, String(error.message || error));
  }
}

function showPracticeFeedback(feedback) {
  saveButton.hidden = true;
  const copy = app.materials.common.formal_intro;
  const heading = el("h1", {}, copy.heading);
  const feedbackBox = el("div", { class: "practice-feedback" });
  feedbackBox.append(el("h2", {}, app.materials.common.progress.practice), el("p", {}, feedback));
  const instructions = el("div", { class: "formal-instructions" });
  instructions.append(el("p", {}, copy.guard), el("p", {}, copy.notes));
  const button = el("button", {
    type: "button", dataset: { action: "begin-formal" }, onclick: beginFormal,
  }, copy.begin);
  replaceStage(heading, el("p", { class: "fiction-notice" }, app.materials.common.disclaimer), feedbackBox, instructions, button);
}

async function beginFormal() {
  try {
    const response = await api("/api/continue", { attempt_id: app.attemptId });
    routeNext(response);
  } catch (error) {
    showError(stage, String(error.message || error));
  }
}

function routeNext(response) {
  if (response.phase === "formal_q1") {
    app.current = response;
    renderQ1("formal");
  } else if (response.phase === "attention_q1") {
    showAttentionQ1(response);
  } else if (response.phase === "reflection") {
    showReflection();
  } else {
    throw new Error(`unexpected phase ${response.phase}`);
  }
}

function showAttentionQ1(response) {
  saveButton.hidden = false;
  const common = app.materials.common;
  const heading = el("h1", {}, common.attention.heading);
  const instruction = el("p", { class: "formal-instructions" }, response.instruction);
  const name = "attention-q1";
  const fields = q1Fieldset(response.q1_options, name);
  const error = el("p", { class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", {
    type: "button", dataset: { action: "attention-q1" },
    onclick: () => submitAttentionQ1(name),
  }, common.attention.submit_q1);
  replaceStage(heading, el("p", { class: "fiction-notice" }, common.disclaimer), instruction, fields, error, button);
}

async function submitAttentionQ1(name) {
  const answer = selected(name);
  if (!answer) {
    showError(stage, app.materials.common.questions.choice_required);
    return;
  }
  app.selectedQ1Text = selectedLabel(name);
  try {
    const response = await api("/api/attention", {
      attempt_id: app.attemptId, step: "q1", answer: answer.value,
    });
    showAttentionReason(response.reason_options);
  } catch (error) {
    showError(stage, String(error.message || error));
  }
}

function showAttentionReason(options) {
  const common = app.materials.common;
  const heading = el("h1", {}, common.attention.heading);
  const name = "attention-reason";
  const fields = choiceFieldset(common.attention.reason_prompt, options, name);
  const error = el("p", { class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", {
    type: "button", dataset: { action: "attention-reason" },
    onclick: () => submitAttentionReason(name),
  }, common.attention.submit_reason);
  replaceStage(heading, el("p", { class: "fiction-notice" }, common.disclaimer), lockedSummary(), fields, error, button);
}

async function submitAttentionReason(name) {
  const answer = selected(name);
  if (!answer) {
    showError(stage, app.materials.common.questions.choice_required);
    return;
  }
  try {
    const response = await api("/api/attention", {
      attempt_id: app.attemptId, step: "reason", answer: answer.value,
    });
    routeNext(response);
  } catch (error) {
    showError(stage, String(error.message || error));
  }
}

function reflectionSelect(field, prompt, rows) {
  const label = el("label", { for: `reflection-${field}` }, prompt);
  const select = el("select", { id: `reflection-${field}`, name: field });
  for (const row of rows) select.append(el("option", { value: row.id }, row.text));
  label.append(select);
  return label;
}

function showReflection() {
  saveButton.hidden = false;
  const copy = app.materials.common.reflection;
  const heading = el("h1", {}, copy.heading);
  const options = copy.options;
  const form = el("div");
  form.append(
    reflectionSelect("helpful", copy.helpful, options.helpful),
    reflectionSelect("confusing", copy.confusing, options.confusing),
    reflectionSelect("amount", copy.amount, options.amount),
  );
  const error = el("p", { class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", {
    type: "button", dataset: { action: "reflection" }, onclick: submitReflection,
  }, copy.submit);
  replaceStage(heading, el("p", { class: "fiction-notice" }, app.materials.common.disclaimer), form, error, button);
}

async function submitReflection() {
  try {
    await api("/api/reflection", {
      attempt_id: app.attemptId,
      helpful: document.querySelector("#reflection-helpful").value,
      confusing: document.querySelector("#reflection-confusing").value,
      amount: document.querySelector("#reflection-amount").value,
    });
    await api("/api/complete", { attempt_id: app.attemptId });
    showExport(true);
  } catch (error) {
    showError(stage, String(error.message || error));
  }
}

function showExport(complete) {
  saveButton.hidden = true;
  const copy = app.materials.common.export;
  const heading = el("h1", {}, copy.heading);
  const error = el("p", { id: "stage-error", class: "error", role: "alert", tabindex: "-1" });
  const actions = el("div", { class: "actions" });
  const jsonButton = el("button", {
    type: "button", dataset: { action: "download-json" }, onclick: () => downloadExport("json"),
  }, copy.download_json);
  const csvButton = el("button", {
    type: "button", dataset: { action: "download-csv" }, onclick: () => downloadExport("csv"),
  }, copy.download_csv);
  const finish = el("button", {
    type: "button", class: "secondary", dataset: { action: "finish" }, onclick: finishPage,
  }, copy.finish);
  actions.append(jsonButton, csvButton, finish);
  replaceStage(
    heading,
    el("p", { class: "fiction-notice" }, app.materials.common.disclaimer),
    el("p", {}, copy.debrief),
    el("p", {}, copy.manual),
    el(
      "p",
      { class: "muted" },
      complete ? copy.complete_product : copy.partial_product,
    ),
    error,
    actions,
  );
}

async function downloadExport(format) {
  try {
    const response = await fetch(
      `/api/export?attempt_id=${encodeURIComponent(app.attemptId)}&format=${format}`,
      { headers: { "X-Study-Capability": app.capability } },
    );
    if (!response.ok) throw new Error(String(response.status));
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `button-board-${app.attemptId}.${format}`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch {
    showError(stage, app.materials.common.errors.download);
  }
}

function showSaveExitDialog() {
  saveDialog.showModal();
  saveDialog.querySelector('[data-action="cancel-save-exit"]').focus();
}

function closeSaveExitDialog() {
  saveDialog.close();
  saveButton.focus();
}

async function confirmSaveExit() {
  try {
    await api("/api/save-exit", { attempt_id: app.attemptId });
    saveDialog.close();
    showExport(false);
  } catch (error) {
    saveDialog.close();
    showError(stage, String(error.message || error));
  }
}

function finishPage() {
  stage.replaceChildren(el("p", {}, app.materials.common.export.debrief));
  saveButton.hidden = true;
}

document.addEventListener("click", (event) => {
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (action === "choose-language") chooseLanguage(event.target.dataset.locale);
  else if (action === "save-exit") showSaveExitDialog();
  else if (action === "cancel-save-exit") closeSaveExitDialog();
  else if (action === "confirm-save-exit") confirmSaveExit();
});

async function bootstrap() {
  try {
    const response = await fetch("/api/bootstrap");
    if (!response.ok) throw new Error(String(response.status));
    const value = await response.json();
    app.csrf = value.csrf_token;
    app.ready = true;
    for (const button of document.querySelectorAll("[data-locale]")) button.disabled = false;
  } catch (error) {
    document.querySelector("#gate-error").textContent = String(error.message || error);
  }
}

bootstrap();
