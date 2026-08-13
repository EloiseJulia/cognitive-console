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
  currentScene: null,
  currentProgress: null,
  currentStep: null,
  demonstration: null,
  demonstrationStep: 0,
  ready: false,
};

window.StepwiseButtonBoardTest = app;

function el(tag, attrs = {}, text = null) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else if (key === "styleVars") {
      for (const [name, item] of Object.entries(value)) node.style.setProperty(name, item);
    } else if (value !== null) node.setAttribute(key, value);
  }
  if (text !== null) node.textContent = text;
  return node;
}

function focusHeading(container, selector = "h1, h2") {
  const heading = container.querySelector(selector);
  if (heading) {
    heading.tabIndex = -1;
    heading.focus();
  }
}

function replaceStageFocused(selector, ...nodes) {
  stage.replaceChildren(...nodes);
  gate.hidden = true;
  startPanel.hidden = true;
  stage.hidden = false;
  header.hidden = false;
  footer.hidden = false;
  requestAnimationFrame(() => focusHeading(stage, selector || "h1, h2"));
}

function replaceStage(...nodes) {
  replaceStageFocused(null, ...nodes);
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
  if (!noPrivateKeys(value)) throw new Error("private derivation material received");
  return value;
}

function setChrome() {
  const common = app.materials.common;
  document.querySelector("#header-title").textContent = common.title;
  document.querySelector("#fiction-banner").textContent = common.disclaimer;
  saveButton.textContent = common.save_exit.button;
  document.querySelector("#save-exit-heading").textContent = common.save_exit.heading;
  document.querySelector("#save-exit-body").textContent = common.save_exit.body;
  saveDialog.querySelector('[data-action="cancel-save-exit"]').textContent = common.save_exit.cancel;
  saveDialog.querySelector('[data-action="confirm-save-exit"]').textContent = common.save_exit.confirm;
  footer.textContent = common.draft;
}

function showError(container, message = null) {
  const target = container.querySelector(".error") || container;
  target.textContent = message || app.materials.common.errors.generic;
  target.focus?.();
}

function localizedError() {
  return app.materials?.common?.errors?.generic || "Local request failed / 本地请求失败";
}

function showWelcome() {
  const copy = app.materials.common.welcome;
  startPanel.replaceChildren(
    el("h1", {}, copy.heading),
    el("p", { class: "subtitle" }, copy.goal),
    el("p", { class: "fiction-notice" }, app.materials.common.disclaimer),
    el("p", {}, copy.open_book),
    el("p", {}, copy.card_only),
    el("p", {}, copy.privacy),
    el("p", { class: "draft" }, app.materials.common.draft),
    el("p", { class: "error", role: "alert", tabindex: "-1" }),
    el("button", { type: "button", dataset: { action: "start" }, onclick: startStudy }, copy.start),
  );
  gate.hidden = true;
  stage.hidden = true;
  startPanel.hidden = false;
  header.hidden = false;
  footer.hidden = false;
  focusHeading(startPanel);
}

async function chooseLanguage(locale) {
  try {
    app.materials = await api(`/api/welcome?selected_locale=${encodeURIComponent(locale)}`);
    app.locale = locale;
    document.documentElement.lang = locale;
    document.title = app.materials.common.title;
    setChrome();
    showWelcome();
  } catch (error) {
    document.querySelector("#gate-error").textContent = localizedError();
  }
}

async function startStudy() {
  try {
    const response = await api("/api/start", {
      selected_locale: app.locale,
    });
    app.attemptId = response.attempt_id;
    app.capability = response.capability;
    showTutorial();
  } catch (error) {
    showError(startPanel, localizedError());
  }
}

function showTutorial() {
  const copy = app.materials.common.tutorial;
  replaceStage(
    el("h1", {}, copy.heading),
    el("p", { class: "fiction-notice" }, app.materials.common.disclaimer),
    el("p", {}, copy.intuition),
    el("button", {
      type: "button", dataset: { action: "show-demonstration" }, onclick: beginDemonstration,
    }, copy.show_demonstration),
  );
}

function recordCard(scene) {
  const labels = app.materials.common.labels;
  const card = el("article", { class: "record-card", "aria-label": scene.title });
  card.append(
    el("p", { class: "fiction-notice" }, app.materials.common.disclaimer),
    el("h2", {}, scene.title),
  );
  const list = el("dl", { class: "record-grid" });
  for (const key of ["situation", "goal", "existing", "new_item"]) {
    const row = el("div", { class: "record-row" });
    row.append(el("dt", {}, labels[key]), el("dd", {}, scene.card[key]));
    list.append(row);
  }
  const factsRow = el("div", { class: "record-row" });
  const facts = el("ul", { class: "fact-list" });
  for (const text of scene.card.facts) facts.append(el("li", {}, text));
  factsRow.append(el("dt", {}, labels.record), el("dd", {}, null));
  factsRow.querySelector("dd").append(facts);
  list.append(factsRow);
  card.append(list);
  return card;
}

function referencePanel() {
  const common = app.materials.common;
  const aside = el("aside", { class: "reference-panel", "aria-label": common.labels.reference_checklist });
  aside.append(el("h2", {}, common.labels.reference_checklist));
  const list = el("ol", { class: "checklist" });
  for (const text of common.checklist) list.append(el("li", {}, text));
  aside.append(list);
  return aside;
}

function answeredSteps(path) {
  if (!path?.length) return null;
  const labels = app.materials.common.labels;
  const actions = app.materials.common.actions;
  const nav = el("nav", {
    class: "answered-steps",
    "aria-label": labels.answered_steps,
  });
  nav.append(el("h2", {}, labels.answered_steps));
  const list = el("ol", { class: "step-summary-list" });
  for (const row of path) {
    const text = actions.change_step
      .replace("{step}", String(row.step))
      .replace("{answer}", row.answer_text);
    const item = el("li");
    item.append(el("button", {
      type: "button",
      class: "secondary step-summary",
      dataset: { action: "revise-step", step: String(row.step) },
      "aria-label": text,
      onclick: () => reviseStep(row.step),
    }, `${row.step}. ${row.answer_text}`));
    list.append(item);
  }
  nav.append(list);
  return nav;
}

function questionCard(response) {
  if (!uniqueIds(response.options)) throw new Error("duplicate option IDs");
  app.currentStep = response.step;
  const card = el("section", { class: "question-card", "aria-live": "polite" });
  card.append(el("div", { class: "question-heading" }, `${response.step} / 6`));
  const fieldset = el("fieldset");
  fieldset.append(el("legend", {}, response.question));
  const choices = el("div", { class: "choice-list" });
  for (const row of response.options) {
    const label = el("label", { class: `choice${row.segments ? " scope-choice" : ""}` });
    label.append(el("input", { type: "radio", name: "step-answer", value: row.id }));
    if (row.segments) {
      const segments = el("span", {
        class: "scope-segments",
        styleVars: { "--scope-columns": String(row.segments.length) },
      });
      for (const segment of row.segments) {
        const cell = el("span", { class: "scope-segment" });
        cell.append(el("b", {}, segment.label), el("span", {}, segment.value));
        segments.append(cell);
      }
      label.append(segments);
    } else {
      label.append(el("span", {}, row.text));
    }
    choices.append(label);
  }
  fieldset.append(choices);
  const error = el("p", { class: "error", role: "alert", tabindex: "-1" });
  const button = el("button", {
    type: "button", dataset: { action: "submit-step" }, onclick: submitStep,
  }, app.materials.common.actions.submit);
  const history = answeredSteps(response.path);
  if (history) card.append(history);
  card.append(fieldset, error);
  const actions = el("div", { class: "question-actions" });
  if (response.path?.length) {
    const previous = response.path[response.path.length - 1];
    actions.append(el("button", {
      type: "button",
      class: "secondary",
      dataset: { action: "previous-step" },
      onclick: () => reviseStep(previous.step),
    }, app.materials.common.actions.back));
  }
  actions.append(button);
  card.append(actions);
  return card;
}

function renderTrial(response) {
  if (response.scene) app.currentScene = response.scene;
  if (response.progress) app.currentProgress = response.progress;
  const heading = el("h1", {}, app.currentProgress);
  const layout = el("div", { class: "study-layout" });
  const left = el("div", { class: "trial-column" });
  left.append(recordCard(app.currentScene), questionCard(response));
  layout.append(left, referencePanel());
  replaceStage(heading, layout);
  saveButton.hidden = false;
}

function workedStep(row, copy) {
  const card = el("section", {
    class: "worked-step",
    "aria-live": "polite",
    "aria-atomic": "true",
  });
  card.append(
    el("h2", { class: "worked-step-heading" }, copy.step.replace("{step}", String(row.step))),
    el("p", { class: "worked-question" }, row.question),
    el("h3", { class: "worked-label" }, copy.options),
  );
  const options = el("ul", { class: "worked-options", "aria-label": copy.options });
  for (const option of row.options) {
    const item = el("li", {
      class: `worked-option${option.demonstrated ? " worked-option--demonstrated" : ""}`,
    });
    item.append(el("span", { class: "worked-option-text" }, option.text));
    if (option.demonstrated) {
      item.append(el("strong", { class: "worked-correct-label" }, copy.demonstrated_choice));
    }
    options.append(item);
  }
  card.append(options);
  const reasoning = el("section", {
    class: "worked-reasoning",
    "aria-label": copy.reasoning,
  });
  reasoning.append(
    el("h3", {}, copy.reasoning),
    el("p", { class: "worked-why" }, `${copy.why}: ${row.why}`),
    el("p", { class: "worked-label" }, `${copy.evidence}:`),
  );
  const evidence = el("ul", { class: "worked-evidence" });
  for (const text of row.evidence) evidence.append(el("li", {}, text));
  reasoning.append(evidence);
  card.append(reasoning);
  return card;
}

function demonstrationResult(response, copy, formal) {
  const result = el("section", {
    class: "demonstration-result",
    "aria-live": "polite",
    "aria-atomic": "true",
  });
  result.append(
    el("h2", { class: "demonstration-result-heading" }, copy.result),
    el("div", { class: "result-destination" }, response.destination.label),
    el("p", {}, response.destination.description),
    el("p", { class: "demonstration-summary" }, response.why),
    el("p", { class: "formal-instructions" }, formal.guard),
    el("p", {}, formal.feedback),
    el("button", {
      type: "button", dataset: { action: "begin-formal" }, onclick: beginFormal,
    }, formal.begin),
  );
  return result;
}

function renderDemonstration(response = app.demonstration) {
  app.demonstration = response;
  app.currentScene = response.scene;
  app.currentProgress = response.progress;
  app.currentStep = null;
  const copy = app.materials.common.demonstration;
  const formal = app.materials.common.formal_intro;
  const explanation = el("section", { class: "demonstration-card" });
  explanation.append(el("h2", {}, copy.heading), el("p", {}, copy.intro));
  const isResult = app.demonstrationStep >= response.worked_steps.length;
  if (isResult) {
    explanation.append(demonstrationResult(response, copy, formal));
  } else {
    explanation.append(
      workedStep(response.worked_steps[app.demonstrationStep], copy),
      el("button", {
        type: "button",
        dataset: { action: "next-demonstration-step" },
        onclick: nextDemonstrationStep,
      }, copy.next_step),
    );
  }
  const layout = el("div", { class: "study-layout" });
  const left = el("div", { class: "trial-column" });
  left.append(recordCard(response.scene), explanation);
  layout.append(left, referencePanel());
  replaceStageFocused(
    isResult ? ".demonstration-result-heading" : ".worked-step-heading",
    el("h1", {}, response.progress),
    layout,
  );
  saveButton.hidden = true;
}

async function beginDemonstration() {
  try {
    app.demonstrationStep = 0;
    renderDemonstration(await api("/api/continue", { attempt_id: app.attemptId }));
  } catch (error) {
    showError(stage, localizedError());
  }
}

function nextDemonstrationStep() {
  app.demonstrationStep += 1;
  renderDemonstration();
}

async function submitStep() {
  const selected = document.querySelector('input[name="step-answer"]:checked');
  if (!selected) {
    showError(stage, app.materials.common.actions.choice_required);
    return;
  }
  try {
    const response = await api("/api/step", {
      attempt_id: app.attemptId,
      step: app.currentStep,
      answer: selected.value,
    });
    if (response.phase.endsWith("_result")) showResult(response);
    else renderTrial(response);
  } catch (error) {
    showError(stage, localizedError());
  }
}

async function reviseStep(step) {
  try {
    const response = await api("/api/revise-step", {
      attempt_id: app.attemptId,
      step,
    });
    renderTrial(response);
  } catch (error) {
    showError(stage, localizedError());
  }
}

function showResult(response) {
  app.currentStep = null;
  const labels = app.materials.common.labels;
  const heading = el("h1", {}, app.currentProgress);
  const layout = el("div", { class: "study-layout" });
  const left = el("div", { class: "trial-column" });
  const result = el("section", { class: "result-card", "aria-live": "polite" });
  result.append(
    el("p", {}, labels.result),
    el("div", { class: "result-destination" }, response.destination.label),
    el("p", {}, response.destination.description),
    el("h2", {}, labels.path),
  );
  result.append(answeredSteps(response.path));
  const actions = el("div", { class: "question-actions" });
  const previous = response.path[response.path.length - 1];
  actions.append(el("button", {
    type: "button",
    class: "secondary",
    dataset: { action: "previous-step" },
    onclick: () => reviseStep(previous.step),
  }, app.materials.common.actions.back));
  actions.append(el("button", {
    type: "button", dataset: { action: "continue-after-result" }, onclick: continueAfterResult,
  }, app.materials.common.actions.continue));
  result.append(actions);
  left.append(recordCard(app.currentScene), result);
  layout.append(left, referencePanel());
  replaceStage(heading, layout);
  saveButton.hidden = false;
}

async function continueAfterResult() {
  try {
    const response = await api("/api/continue", { attempt_id: app.attemptId });
    if (response.phase === "attention") showAttention(response);
    else renderTrial(response);
  } catch (error) {
    showError(stage, localizedError());
  }
}

async function beginFormal() {
  try {
    app.demonstration = null;
    app.demonstrationStep = 0;
    renderTrial(await api("/api/continue", { attempt_id: app.attemptId }));
  } catch (error) {
    showError(stage, localizedError());
  }
}

function showAttention(response) {
  app.currentStep = null;
  const fieldset = el("fieldset");
  fieldset.append(el("legend", {}, response.question));
  const list = el("div", { class: "choice-list" });
  for (const row of response.options) {
    const label = el("label", { class: "choice" });
    label.append(
      el("input", { type: "radio", name: "attention-answer", value: row.id }),
      el("span", {}, row.text),
    );
    list.append(label);
  }
  fieldset.append(list);
  replaceStage(
    el("h1", {}, response.heading),
    el("p", { class: "fiction-notice" }, app.materials.common.disclaimer),
    el("p", {}, response.instruction),
    fieldset,
    el("p", { class: "error", role: "alert", tabindex: "-1" }),
    el("button", {
      type: "button", dataset: { action: "submit-attention" }, onclick: submitAttention,
    }, app.materials.common.actions.submit),
  );
  saveButton.hidden = false;
}

async function submitAttention() {
  const selected = document.querySelector('input[name="attention-answer"]:checked');
  if (!selected) {
    showError(stage, app.materials.common.actions.choice_required);
    return;
  }
  try {
    const response = await api("/api/attention", {
      attempt_id: app.attemptId,
      answer: selected.value,
    });
    if (response.phase === "reflection") showReflection();
  } catch (error) {
    showError(stage, localizedError());
  }
}

function reflectionSelect(field, prompt, rows) {
  const label = el("label", { for: `reflection-${field}` }, prompt);
  const select = el("select", { id: `reflection-${field}` });
  for (const row of rows) select.append(el("option", { value: row.id }, row.text));
  label.append(select);
  return label;
}

function showReflection() {
  const copy = app.materials.common.reflection;
  const options = copy.options;
  replaceStage(
    el("h1", {}, copy.heading),
    reflectionSelect("hardest", copy.hardest, options.hardest),
    reflectionSelect("confusing", copy.confusing, options.confusing),
    reflectionSelect("amount", copy.amount, options.amount),
    reflectionSelect("pace", copy.pace, options.pace),
    el("p", { class: "error", role: "alert", tabindex: "-1" }),
    el("button", {
      type: "button", dataset: { action: "submit-reflection" }, onclick: submitReflection,
    }, copy.submit),
  );
}

async function submitReflection() {
  try {
    await api("/api/reflection", {
      attempt_id: app.attemptId,
      hardest: document.querySelector("#reflection-hardest").value,
      confusing: document.querySelector("#reflection-confusing").value,
      amount: document.querySelector("#reflection-amount").value,
      pace: document.querySelector("#reflection-pace").value,
    });
    await api("/api/complete", { attempt_id: app.attemptId });
    showExport(true);
  } catch (error) {
    showError(stage, localizedError());
  }
}

function showExport(complete) {
  const copy = app.materials.common.export;
  const jsonButton = el("button", {
    type: "button", dataset: { action: "download-json" }, onclick: () => downloadExport("json"),
  }, copy.download_json);
  const csvButton = el("button", {
    type: "button", dataset: { action: "download-csv" }, onclick: () => downloadExport("csv"),
  }, copy.download_csv);
  replaceStage(
    el("h1", {}, copy.heading),
    el("p", {}, copy.debrief),
    el("p", { class: "muted" }, copy.manual),
    el("div", { class: "actions" }, null),
    el("p", { class: "error", role: "alert", tabindex: "-1" }),
    el("button", {
      type: "button", class: "secondary", dataset: { action: "finish-page" }, onclick: finishPage,
    }, copy.finish),
  );
  stage.querySelector(".actions").append(jsonButton, csvButton);
  saveButton.hidden = true;
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
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `button-board-stepwise-${app.attemptId}.${format}`;
    anchor.click();
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
    showError(stage, localizedError());
  }
}

function finishPage() {
  stage.replaceChildren(el("p", {}, app.materials.common.export.debrief));
  saveButton.hidden = true;
  app.capability = null;
  app.attemptId = null;
}

async function bootstrap() {
  try {
    const response = await fetch("/api/bootstrap");
    if (!response.ok) throw new Error(String(response.status));
    const value = await response.json();
    if (!noPrivateKeys(value)) throw new Error("private derivation material received");
    app.csrf = value.csrf_token;
    for (const button of document.querySelectorAll('[data-action="choose-language"]')) {
      button.disabled = false;
      button.addEventListener("click", () => chooseLanguage(button.dataset.locale));
    }
    app.ready = true;
  } catch (error) {
    document.querySelector("#gate-error").textContent = localizedError();
  }
}

saveButton.addEventListener("click", showSaveExitDialog);
saveDialog.querySelector('[data-action="cancel-save-exit"]').addEventListener("click", closeSaveExitDialog);
saveDialog.querySelector('[data-action="confirm-save-exit"]').addEventListener("click", confirmSaveExit);
bootstrap();
