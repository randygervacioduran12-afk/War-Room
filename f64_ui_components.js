function esc(value) {
return String(value ?? “”)
.replaceAll(”&”, “&”)
.replaceAll(”<”, “<”)
.replaceAll(”>”, “>”)
.replaceAll(’”’, “””);
}

function parseMaybeJson(value) {
if (value == null) return null;
if (typeof value === “object”) return value;
if (typeof value !== “string”) return value;
const t = value.trim();
if (!t) return null;
if ((t.startsWith(”{”) && t.endsWith(”}”)) || (t.startsWith(”[”) && t.endsWith(”]”))) {
try { return JSON.parse(t); } catch { return value; }
}
return value;
}

function previewText(value, max = 220) {
if (value == null) return “”;
let text = typeof value === “string” ? value : JSON.stringify(value, null, 2);
text = text.replace(/`[\s\S]*?`/g, “[code block]”);
text = text.replace(/\s+/g, “ “).trim();
return text.length <= max ? text : `${text.slice(0, max - 1)}…`;
}

function formatDate(value) {
if (!value) return “”;
try {
return new Date(value).toLocaleString(undefined, {
month: “short”, day: “numeric”,
hour: “2-digit”, minute: “2-digit”,
});
} catch { return String(value); }
}

function inferHref(path) {
if (!path) return “”;
if (String(path).startsWith(”/”)) return path;
return `/artifact-files/${String(path).replace(/^\/+/, "")}`;
}

function normalizeArtifact(task) {
const directArtifact = parseMaybeJson(task?.artifact_json);
const resultJson     = parseMaybeJson(task?.result_json);
const outputPayload  = parseMaybeJson(task?.output_payload);

const nestedArtifact =
(resultJson    && typeof resultJson    === “object” && resultJson.artifact)    ||
(outputPayload && typeof outputPayload === “object” && outputPayload.artifact) ||
null;

const artifact   = directArtifact || nestedArtifact;
const fallbackPath = task?.artifact_path || “”;

if (artifact && typeof artifact === “object”) {
const path = artifact.path || fallbackPath || “”;
return {
type:        artifact.type || “markdown”,
title:       artifact.title || task.title || “Artifact”,
body:        artifact.body || artifact.content || artifact.text ||
resultJson?.raw_text || resultJson?.summary ||
outputPayload?.summary || “”,
href:        artifact.href || inferHref(path),
path,
general_key: artifact.general_key || task.general_key || “”,
task_id:     artifact.task_id || task.task_id || “”,
created_at:  artifact.created_at || task.updated_at || task.created_at || “”,
};
}

const summaryBody =
(resultJson    && typeof resultJson    === “object” && (resultJson.summary    || resultJson.raw_text))    ||
(outputPayload && typeof outputPayload === “object” && (outputPayload.summary || outputPayload.raw_text)) ||
“”;

if (summaryBody || fallbackPath) {
return {
type: “markdown”, title: task.title || “Artifact”,
body: String(summaryBody || “Open generated file.”),
href: inferHref(fallbackPath), path: fallbackPath,
general_key: task.general_key || “”, task_id: task.task_id || “”,
created_at: task.updated_at || task.created_at || “”,
};
}
return null;
}

/* ── statusPill — semantic Destiny-style pill ── */
function statusPill(status) {
const map = {
queued:    “pill pill-queued”,
claimed:   “pill pill-claimed”,
completed: “pill pill-completed”,
failed:    “pill pill-failed”,
};
return `<span class="${map[status] || "pill"}">${esc(status || "unknown")}</span>`;
}

/* ── emptyState helper ── */
function emptyState(icon, message) {
return `<div style="text-align:center;padding:36px 20px;color:var(--text-3);">

<div style="font-size:32px;margin-bottom:12px;opacity:0.4;">${icon}</div>
<div style="font-family:var(--f-mono);font-size:12px;">${esc(message)}</div>

  </div>`;
}

/* ═══════════════════════════════════════════
EXPORTS
═══════════════════════════════════════════ */

export function pickRows(payload) {
if (Array.isArray(payload))       return payload;
if (Array.isArray(payload?.items)) return payload.items;
if (Array.isArray(payload?.rows))  return payload.rows;
if (Array.isArray(payload?.runs))  return payload.runs;
if (Array.isArray(payload?.data))  return payload.data;
return [];
}

/* Mini health in topbar metric chip */
export function renderMiniHealth(target, health) {
if (!target) return;
const ok = !!health?.ok;
target.innerHTML = ` <span class="dot ${ok ? "ok" : "err"}"></span> <span style="font-family:var(--f-mono);font-size:11.5px;"> ${esc(ok ? "command link active" : "attention needed")} </span>`;
}

/* 4 health cards — Finance dashboard KPI style */
export function renderHealthCards(target, health) {
if (!target) return;
const cards = [
[“API”,         health?.ok     ? “online”    : “degraded”,     health?.timestamp    || “”],
[“Database”,    health?.db_ok  ? “up”        : “down”,          health?.db_error    || “storage ready”],
[“LLM”,         health?.llm_ok ? “up”        : “down”,          health?.provider    || “provider missing”],
[“Environment”, health?.app_env || “dev”,                        “current runtime”],
];
target.innerHTML = cards.map(([title, value, meta]) => ` <div class="health-card"> <div class="card-title">${esc(title)}</div> <div style="font-family:var(--f-display);font-size:26px;font-weight:800;line-height:1.05; margin:8px 0 5px;letter-spacing:-0.025em;">${esc(value)}</div> <div class="card-meta">${esc(meta)}</div> </div>`).join(””);
}

/* 8-card signal corridor — Destiny dashboard stats */
export function renderSignalCorridor(target, state) {
if (!target) return;
const queued    = state.tasks.filter(t => t.status === “queued”).length;
const claimed   = state.tasks.filter(t => t.status === “claimed”).length;
const completed = state.tasks.filter(t => t.status === “completed”).length;
const failed    = state.tasks.filter(t => t.status === “failed”).length;
const artifacts = state.tasks.filter(t => normalizeArtifact(t)).length;

const cards = [
[“Runs”,       state.runs.length,            “mission threads”,    “”],
[“Queued”,     queued,                        “awaiting execution”, queued    ? “warn” : “”],
[“Claimed”,    claimed,                       “currently owned”,    claimed   ? “ok”   : “”],
[“Completed”,  completed,                     “delivered outcomes”, completed ? “ok”   : “”],
[“Failed”,     failed,                        “needs review”,       failed    ? “err”  : “”],
[“Artifacts”,  artifacts,                     “dock-ready outputs”, artifacts ? “ok”   : “”],
[“Project”,    state.activeProjectKey || “—”, “current context”,   “”],
[“Active run”, state.activeRunId
? state.activeRunId.slice(0, 16) + “…”
: “—”,                                      “selected mission”,  state.activeRunId ? “ok” : “”],
];

target.innerHTML = cards.map(([title, value, meta, dot]) => `<div class="signal-card"> <div class="card-title">${esc(title)}</div> <div style="font-family:var(--f-display);font-size:24px;font-weight:800; line-height:1.05;margin:7px 0 4px;word-break:break-word;letter-spacing:-0.02em;"> ${dot ?`<span class="dot ${dot}" style="display:inline-block;margin-right:8px;vertical-align:middle;"></span>` : ""}${esc(String(value))} </div> <div class="card-meta">${esc(meta)}</div> </div>`).join(””);
}

/* Run list — Agentrooms agent card style */
export function renderRuns(target, runs, activeRunId) {
if (!target) return;
if (!runs.length) {
target.innerHTML = emptyState(“⚡”, “No runs yet — launch one to begin.”);
return;
}
target.innerHTML = runs.map(run => {
const runId    = run.run_id || run.id || “”;
const isActive = runId === activeRunId;
return ` <div class="run-card ${isActive ? "active-run" : ""}"> <div class="card-title">${esc(run.goal || run.title || "Mission")}</div> <div class="card-meta" style="margin-top:7px;"> <span style="font-family:var(--f-mono);font-size:11px;opacity:0.7;"> ${esc(runId)}<br> ${esc(run.project_key || "")} · ${esc(run.status || "created")} </span> </div> <div class="run-actions"> <button class="ghost-btn sm" data-run-select="${esc(runId)}"> ${isActive ? "✓ Active run" : "Set active"} </button> </div> </div>`;
}).join(””);
}

/* Memory cards — richer display */
export function renderMemory(target, rows) {
if (!target) return;
if (!rows.length) {
target.innerHTML = emptyState(“◉”, “No memory entries yet.”);
return;
}
target.innerHTML = rows.map(row => {
const body = row.body || row.content || “”;
const bits = [
row.memory_type || “note”,
row.source_task_id ? `task=${row.source_task_id.slice(0,10)}…` : “”,
row.created_at ? formatDate(row.created_at) : “”,
].filter(Boolean);
return `<div class="memory-card"> <div class="card-title">${esc(row.title || row.memory_id || "Memory entry")}</div> <div class="task-tags"> ${bits.map(b =>`<span class="pill">${esc(b)}</span>`).join("")} </div> <div class="card-meta" style="margin-top:10px;line-height:1.6;"> ${esc(previewText(body, 600))} </div> </div>`;
}).join(””);
}

/* Workbench file cards */
export function renderWorkbench(target, files) {
if (!target) return;
if (!files.length) {
target.innerHTML = emptyState(“⌗”, “No matching files — try a different prefix.”);
return;
}
target.innerHTML = files.map(file => ` <div class="file-card"> <div class="card-title">${esc(file.name || file.path || "file")}</div> <div class="card-meta" style="font-family:var(--f-mono);font-size:11px;"> ${esc(file.path || file.name || "")} </div> </div>`).join(””);
}

/* Artifact cards — violet glass style */
export function renderArtifacts(target, tasks) {
if (!target) return;
const rows = tasks
.map(task => ({ task, artifact: normalizeArtifact(task) }))
.filter(e => e.artifact);

if (!rows.length) {
target.innerHTML = emptyState(“◎”, “Complete tasks to populate the artifact dock.”);
return;
}

target.innerHTML = rows.map(({ task, artifact }) => {
const modalPayload = {
task_id: task.task_id, title: artifact.title,
general_key: artifact.general_key || task.general_key,
status: task.status, artifact,
};
const encoded = esc(JSON.stringify(modalPayload));
return `<div class="artifact-card"> <div class="card-title">${esc(artifact.general_key || "artifact")}</div> <div style="font-family:var(--f-display);font-size:17px;font-weight:700; margin:6px 0 8px;line-height:1.2;"> ${esc(artifact.title || task.title || "Artifact")} </div> <div class="card-meta">${esc(previewText(artifact.body, 260))}</div> <div class="task-tags"> <span class="pill">${esc(artifact.type || "markdown")}</span> ${statusPill(task.status)} ${artifact.general_key ?`<span class="pill">${esc(artifact.general_key)}</span>`: ""} </div> <div class="artifact-links"> ${artifact.href ?`<a class="ghost-btn sm" href="${esc(artifact.href)}" target="_blank" rel="noreferrer">Open file</a>`: ""} <button class="ghost-btn sm" data-artifact-open='${encoded}'>Preview</button> </div> ${artifact.path ?`<div class="card-meta" style="margin-top:10px;font-family:var(--f-mono);font-size:10.5px;opacity:0.6;">${esc(artifact.path)}</div>` : ""} </div>`;
}).join(””);
}

/* Task card */
function renderTaskCard(task) {
const artifact = normalizeArtifact(task);
return `<div class="task-card"> <div class="task-title">${esc(task.title || "Untitled task")}</div> <div class="task-meta" style="font-family:var(--f-mono);font-size:10.5px;margin-top:5px;line-height:1.7;"> ${esc(task.task_id || "")} · ${esc(task.general_key || "")} · ${esc(task.task_type || "")} </div> ${artifact?.body ?`<div class="card-meta" style="margin-top:10px;">${esc(previewText(artifact.body, 200))}</div>` : ""} <div class="task-tags"> ${statusPill(task.status)} <span class="pill">${esc(task.project_key || "no-project")}</span> </div> <div class="task-actions"> <button class="ghost-btn sm" data-task-requeue="${esc(task.task_id || "")}">↺ Requeue</button> <button class="ghost-btn sm" data-task-delete="${esc(task.task_id || "")}">✕ Delete</button> </div> </div>`;
}

/* Task board — 4 lane Destiny-style board */
export function renderTaskBoard(target, tasks) {
if (!target) return;
const lanes = [
[“queued”,    “Queued”,    “Awaiting execution”],
[“claimed”,   “Claimed”,   “Currently active”],
[“completed”, “Completed”, “Delivered outcomes”],
[“failed”,    “Failed”,    “Needs review”],
];
target.innerHTML = lanes.map(([status, label, meta]) => {
const lane = tasks.filter(t => t.status === status);
return `<section class="lane"> <div class="lane-title">${esc(label)} · <span style="color:var(--text-2);">${lane.length}</span></div> <div class="lane-meta" style="margin-bottom:12px;">${esc(meta)}</div> ${lane.length ? lane.map(renderTaskCard).join("") :`<div class="task-card"><div class="task-meta">No tasks in this lane.</div></div>`} </section>`;
}).join(””);
}