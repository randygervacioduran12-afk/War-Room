import {
getHealth,
listRuns,
createRun,
listTasks,
createTask,
listMemory,
createMemory,
listWorkbenchFiles,
requeueTask,
deleteTask,
} from "/f63_ui_api.js";

import {
pickRows,
renderMiniHealth,
renderHealthCards,
renderSignalCorridor,
renderRuns,
renderMemory,
renderWorkbench,
renderArtifacts,
renderTaskBoard,
} from "/f64_ui_components.js";

import { openArtifactModal, closeArtifactModal } from "/f67_ui_artifacts.js";
import { normalizeWorkbenchPayload } from "/f66_ui_workbench.js";
import { bootTheme, cycleTheme } from "/f65_ui_theme.js";

const state = {
activeRunId: localStorage.getItem("warroom_active_run_id") || "",
activeProjectKey: localStorage.getItem("warroom_project_key") || "demo-project",
autoPollTasks: true,
health: null,
runs: [],
tasks: [],
memory: [],
workbench: [],
activeAgentPreset: "general_of_the_army",
};

const el = {};

function cacheDom() {
[
"mini-health",
"health-overview",
"health-meta",
"active-run-id",
"active-run-meta",
"task-pulse",
"task-pulse-meta",
"artifact-pulse",
"artifact-pulse-meta",
"launch-result",
"dispatch-result",
"note-result",
"run-project-key",
"run-adapter-key",
"run-goal",
"dispatch-general-key",
"dispatch-task-type",
"dispatch-title",
"dispatch-message",
"note-title",
"note-body",
"health-cards",
"signal-corridor",
"task-board",
"runs-list",
"memory-list",
"memory-list-secondary",
"workbench-grid",
"artifact-grid",
"artifact-grid-secondary",
"workbench-prefix",
"artifact-modal",
"artifact-modal-subtitle",
"artifact-modal-body",
].forEach((id) => {
el[id] = document.getElementById(id);
});
}

function escapeError(err) {
if (!err) return "Unknown error";
if (typeof err === "string") return err;
if (err.data) {
try {
return JSON.stringify(err.data, null, 2);
} catch {
return String(err.data);
}
}
return err.message || String(err);
}

function setAgentPreset(generalKey) {
state.activeAgentPreset = generalKey || "general_of_the_army";
if (el["dispatch-general-key"]) {
el["dispatch-general-key"].value = state.activeAgentPreset;
}

document.querySelectorAll("[data-agent-preset]").forEach((btn) => {
btn.classList.toggle("active", btn.dataset.agentPreset === state.activeAgentPreset);
});
}

function syncProjectFromActiveRun() {
if (!state.activeRunId) return;

const activeRun = state.runs.find(
(run) => (run.run_id || run.id || "") === state.activeRunId
);

if (!activeRun) return;

const projectKey = activeRun.project_key || state.activeProjectKey || "demo-project";
state.activeProjectKey = projectKey;
localStorage.setItem("warroom_project_key", projectKey);

if (el["run-project-key"]) {
el["run-project-key"].value = projectKey;
}
}

function setActiveRun(runId) {
state.activeRunId = runId || "";
localStorage.setItem("warroom_active_run_id", state.activeRunId);
syncProjectFromActiveRun();
renderHeaderMetrics();
renderRuns(el["runs-list"], state.runs, state.activeRunId);
}

function switchView(view) {
document.querySelectorAll(".nav-icon[data-panel]").forEach((btn) => {
btn.classList.toggle("active", btn.dataset.panel === view);
});
document.querySelectorAll(".mob-btn[data-panel]").forEach((btn) => {
btn.classList.toggle("active", btn.dataset.panel === view);
});
document.querySelectorAll(".nav-chip").forEach((btn) => {
btn.classList.toggle("active", btn.dataset.view === view);
});
document.querySelectorAll(".view-panel").forEach((section) => {
section.classList.toggle("active-view", section.id === `view-${view}`);
});
const ws = document.getElementById("workspace-split");
if (ws) ws.classList.toggle("panels-open", !!view);
}

function renderHeaderMetrics() {
if (el["active-run-id"]) {
el["active-run-id"].textContent = state.activeRunId || "No active run";
}

if (el["active-run-meta"]) {
el["active-run-meta"].textContent = state.activeRunId
? `Context locked to ${state.activeProjectKey || "this project"}`
: "Create or select a run";
}

const queued = state.tasks.filter((t) => t.status === "queued").length;
const claimed = state.tasks.filter((t) => t.status === "claimed").length;
const completed = state.tasks.filter((t) => t.status === "completed").length;
const failed = state.tasks.filter((t) => t.status === "failed").length;

if (el["task-pulse"]) {
el["task-pulse"].textContent = `${queued} queued · ${claimed} claimed`;
}

if (el["task-pulse-meta"]) {
el["task-pulse-meta"].textContent = `${completed} completed · ${failed} failed`;
}

const artifactTasks = state.tasks.filter(
(t) => t.artifact_json || t.artifact_path || t.result_json || t.output_payload
).length;

if (el["artifact-pulse"]) {
el["artifact-pulse"].textContent = artifactTasks
? `${artifactTasks} artifacts detected`
: "No artifacts";
}

if (el["artifact-pulse-meta"]) {
el["artifact-pulse-meta"].textContent = artifactTasks
? "Dock has generated outputs"
: "Dock idle";
}

if (state.health) {
if (el["health-overview"]) {
el["health-overview"].textContent = state.health.ok ? "System nominal" : "Attention needed";
}
if (el["health-meta"]) {
el["health-meta"].textContent = `db=${state.health.db_ok ? "up" : "down"} · llm=${state.health.llm_ok ? "up" : "down"}`;
}
}
}

async function refreshHealth() {
try {
state.health = await getHealth();
renderMiniHealth(el["mini-health"], state.health);
renderHealthCards(el["health-cards"], state.health);
renderHeaderMetrics();
} catch (err) {
console.error(err);
}
}

async function refreshRuns() {
try {
const payload = await listRuns();
state.runs = pickRows(payload?.runs || payload);

if (!state.activeRunId && state.runs.length) {
const first = state.runs[0];
state.activeRunId = first.run_id || first.id || "";
localStorage.setItem("warroom_active_run_id", state.activeRunId);
}

syncProjectFromActiveRun();
renderRuns(el["runs-list"], state.runs, state.activeRunId);
renderSignalCorridor(el["signal-corridor"], state);
renderHeaderMetrics();

} catch (err) {
console.error(err);
el["runs-list"].innerHTML = `<div class="run-card"><div class="card-title">Run load failed</div><div class="card-meta">${escapeError(err)}</div></div>`;
}
}

async function refreshTasks() {
try {
if (!state.activeRunId) {
state.tasks = [];
renderTaskBoard(el["task-board"], state.tasks);
renderArtifacts(el["artifact-grid"], state.tasks);
renderArtifacts(el["artifact-grid-secondary"], state.tasks);
renderSignalCorridor(el["signal-corridor"], state);
renderHeaderMetrics();
return;
}

const payload = await listTasks(state.activeRunId);
state.tasks = pickRows(payload);
renderTaskBoard(el["task-board"], state.tasks);
renderArtifacts(el["artifact-grid"], state.tasks);
renderArtifacts(el["artifact-grid-secondary"], state.tasks);
renderSignalCorridor(el["signal-corridor"], state);
renderHeaderMetrics();

} catch (err) {
console.error(err);
el["task-board"].innerHTML = `<div class="task-card"><div class="task-title">Task load failed</div><div class="task-meta">${escapeError(err)}</div></div>`;
}
}

async function refreshMemory() {
try {
const payload = await listMemory(state.activeProjectKey || "demo-project");
state.memory = pickRows(payload);
renderMemory(el["memory-list"], state.memory);
renderMemory(el["memory-list-secondary"], state.memory);
} catch (err) {
console.error(err);
const markup = `<div class="memory-card"><div class="card-title">Memory load failed</div><div class="card-meta">${escapeError(err)}</div></div>`;
if (el["memory-list"]) el["memory-list"].innerHTML = markup;
if (el["memory-list-secondary"]) el["memory-list-secondary"].innerHTML = markup;
}
}

async function refreshWorkbench() {
try {
const prefix = el["workbench-prefix"]?.value || "";
const payload = await listWorkbenchFiles(prefix);
state.workbench = normalizeWorkbenchPayload(payload);
renderWorkbench(el["workbench-grid"], state.workbench);
} catch (err) {
console.error(err);
el["workbench-grid"].innerHTML = `<div class="file-card"><div class="card-title">Workbench load failed</div><div class="card-meta">${escapeError(err)}</div></div>`;
}
}

async function handleCreateRun() {
const payload = {
project_key: el["run-project-key"].value.trim() || "demo-project",
adapter_key: el["run-adapter-key"].value.trim() || "research_project",
goal: el["run-goal"].value.trim(),
};

state.activeProjectKey = payload.project_key;
localStorage.setItem("warroom_project_key", state.activeProjectKey);

try {
const data = await createRun(payload);
el["launch-result"].textContent = JSON.stringify(data, null, 2);

const runId = data?.run_id || data?.id || "";
if (runId) setActiveRun(runId);

await refreshRuns();
await refreshTasks();
await refreshMemory();
switchView("signals");

} catch (err) {
console.error(err);
el["launch-result"].textContent = JSON.stringify(
{ error: "Run creation failed", detail: escapeError(err) },
null,
2
);
}
}

async function handleDispatchTask() {
if (!state.activeRunId) {
el["dispatch-result"].textContent = JSON.stringify(
{ error: "No active run selected" },
null,
2
);
return;
}

const operatorMessage = el["dispatch-message"].value.trim();

const payload = {
run_id: state.activeRunId,
general_key: el["dispatch-general-key"].value.trim() || state.activeAgentPreset,
task_type: el["dispatch-task-type"].value.trim() || "plan",
title: el["dispatch-title"].value.trim() || "Manual mission dispatch",
project_key: state.activeProjectKey,
operator_message: operatorMessage,
payload_json: {
operator_message: operatorMessage,
source: "ui_dispatch",
},
input_payload: {
goal: operatorMessage,
project_key: state.activeProjectKey,
adapter_key: el["run-adapter-key"]?.value?.trim() || "research_project",
},
};

try {
const data = await createTask(payload);
el["dispatch-result"].textContent = JSON.stringify(data, null, 2);

await refreshTasks();
await refreshMemory();
switchView("signals");

} catch (err) {
console.error(err);
el["dispatch-result"].textContent = JSON.stringify(
{ error: "Task dispatch failed", detail: escapeError(err) },
null,
2
);
}
}

async function handleSaveNote() {
const title = el["note-title"].value.trim() || "Operator note";
const body = el["note-body"].value.trim();

if (!body) {
el["note-result"].textContent = JSON.stringify(
{ error: "Note body is required" },
null,
2
);
return;
}

try {
const data = await createMemory({
project_key: state.activeProjectKey || "demo-project",
run_id: state.activeRunId || null,
memory_type: "note",
title,
body,
source_task_id: null,
});

el["note-result"].textContent = JSON.stringify(data, null, 2);
await refreshMemory();
switchView("memory");

} catch (err) {
console.error(err);
el["note-result"].textContent = JSON.stringify(
{ error: "Save note failed", detail: escapeError(err) },
null,
2
);
}
}

async function handleRequeue(taskId) {
if (!taskId) return;
try {
await requeueTask(taskId);
await refreshTasks();
await refreshMemory();
} catch (err) {
alert(`Requeue failed: ${escapeError(err)}`);
}
}

async function handleDelete(taskId) {
if (!taskId) return;
try {
await deleteTask(taskId);
await refreshTasks();
await refreshMemory();
} catch (err) {
alert(`Delete failed: ${escapeError(err)}`);
}
}

async function refreshAll() {
await refreshHealth();
await refreshRuns();
await refreshTasks();
await refreshMemory();
await refreshWorkbench();
}

function bootSanctuaryMotion() {
const surface = document.querySelector("[data-tilt-surface]");
const core = document.getElementById("claude-sanctuary");
if (!surface || !core) return;

surface.addEventListener("pointermove", (event) => {
const rect = surface.getBoundingClientRect();
const x = (event.clientX - rect.left) / rect.width - 0.5;
const y = (event.clientY - rect.top) / rect.height - 0.5;
core.style.transform = `rotateX(${y * -7}deg) rotateY(${x * 10}deg) translate3d(${x * 8}px, ${y * 8}px, 0)`;
});

surface.addEventListener("pointerleave", () => {
core.style.transform = "rotateX(0deg) rotateY(0deg) translate3d(0,0,0)";
});
}

function bindEvents() {
document.querySelectorAll(".nav-icon[data-panel]").forEach((btn) => {
btn.addEventListener("click", () => switchView(btn.dataset.panel));
});
document.querySelectorAll(".mob-btn[data-panel]").forEach((btn) => {
btn.addEventListener("click", () => switchView(btn.dataset.panel));
});
document.querySelectorAll(".nav-chip").forEach((btn) => {
btn.addEventListener("click", () => switchView(btn.dataset.view));
});

document.querySelectorAll("[data-agent-preset]").forEach((btn) => {
btn.addEventListener("click", () => setAgentPreset(btn.dataset.agentPreset));
});

document.getElementById("refresh-all-btn")?.addEventListener("click", refreshAll);
document.getElementById("health-refresh-btn")?.addEventListener("click", refreshHealth);
document.getElementById("load-runs-btn")?.addEventListener("click", refreshRuns);
document.getElementById("load-tasks-btn")?.addEventListener("click", refreshTasks);
document.getElementById("load-memory-btn")?.addEventListener("click", refreshMemory);
document.getElementById("load-artifacts-btn")?.addEventListener("click", () => {
renderArtifacts(el["artifact-grid"], state.tasks);
});
document.getElementById("load-artifacts-btn-secondary")?.addEventListener("click", () => {
renderArtifacts(el["artifact-grid-secondary"], state.tasks);
});
document.getElementById("load-workbench-btn")?.addEventListener("click", refreshWorkbench);

document.getElementById("create-run-btn")?.addEventListener("click", handleCreateRun);
document.getElementById("dispatch-task-btn")?.addEventListener("click", handleDispatchTask);
document.getElementById("save-note-btn")?.addEventListener("click", handleSaveNote);

document.getElementById("hero-launch-btn")?.addEventListener("click", () => switchView("operations"));
document.getElementById("hero-dispatch-btn")?.addEventListener("click", () => switchView("operations"));

document.getElementById("auto-poll-tasks-btn")?.addEventListener("click", (event) => {
state.autoPollTasks = !state.autoPollTasks;
const btn = event.currentTarget;
const span = btn.querySelector("span");
if (span) span.textContent = `Poll: ${state.autoPollTasks ? "on" : "off"}`;
});

document.getElementById("close-artifact-modal")?.addEventListener("click", () => {
closeArtifactModal(el["artifact-modal"]);
});

document.querySelector(".modal-backdrop")?.addEventListener("click", () => {
closeArtifactModal(el["artifact-modal"]);
});

document.body.addEventListener("click", async (event) => {
const runBtn = event.target.closest("[data-run-select]");
if (runBtn) {
setActiveRun(runBtn.dataset.runSelect);
await refreshTasks();
await refreshMemory();
return;
}

const requeueBtn = event.target.closest("[data-task-requeue]");
if (requeueBtn) {
await handleRequeue(requeueBtn.dataset.taskRequeue);
return;
}

const deleteBtn = event.target.closest("[data-task-delete]");
if (deleteBtn) {
await handleDelete(deleteBtn.dataset.taskDelete);
return;
}

const artifactBtn = event.target.closest("[data-artifact-open]");
if (artifactBtn) {
try {
const payload = JSON.parse(artifactBtn.dataset.artifactOpen);
openArtifactModal(
el["artifact-modal"],
el["artifact-modal-subtitle"],
el["artifact-modal-body"],
payload
);
} catch (err) {
console.error(err);
}
}

});
}

function startPolling() {
setInterval(async () => {
try {
await refreshHealth();
if (state.autoPollTasks) {
await refreshRuns();
await refreshTasks();
await refreshMemory();
}
} catch (err) {
console.error(err);
}
}, 7000);
}

async function boot() {
bootTheme();
cacheDom();
bindEvents();
bootSanctuaryMotion();
setAgentPreset(state.activeAgentPreset);
switchView("overview"); // opens panel-stage on load
await refreshAll();
startPolling();
}

boot();
