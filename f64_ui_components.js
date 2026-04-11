function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function parseMaybeJson(value) {
  if (value == null) return null;
  if (typeof value === "object") return value;
  if (typeof value !== "string") return value;

  const trimmed = value.trim();
  if (!trimmed) return null;

  if (
    (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
    (trimmed.startsWith("[") && trimmed.endsWith("]"))
  ) {
    try {
      return JSON.parse(trimmed);
    } catch {
      return value;
    }
  }

  return value;
}

function previewText(value, max = 240) {
  if (value == null) return "";
  let text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  text = text.replace(/```[\s\S]*?```/g, "[code block]");
  text = text.replace(/\s+/g, " ").trim();
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1)}…`;
}

function formatDate(value) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function normalizeArtifact(task) {
  const directArtifact = parseMaybeJson(task?.artifact_json);
  const resultJson = parseMaybeJson(task?.result_json);
  const outputPayload = parseMaybeJson(task?.output_payload);

  const nestedArtifact =
    (resultJson && typeof resultJson === "object" && resultJson.artifact) ||
    (outputPayload && typeof outputPayload === "object" && outputPayload.artifact) ||
    null;

  const artifact = directArtifact || nestedArtifact;

  if (artifact && typeof artifact === "object") {
    return {
      type: artifact.type || "markdown",
      title: artifact.title || task.title || "Artifact",
      body:
        artifact.body ||
        artifact.content ||
        artifact.text ||
        resultJson?.raw_text ||
        resultJson?.summary ||
        "",
      href: artifact.href || "",
      path: artifact.path || task.artifact_path || "",
      general_key: artifact.general_key || task.general_key || "",
      task_id: artifact.task_id || task.task_id || "",
      created_at: artifact.created_at || task.updated_at || task.created_at || "",
    };
  }

  const fallbackBody =
    resultJson?.raw_text ||
    resultJson?.summary ||
    outputPayload?.raw_text ||
    task?.artifact_path ||
    "";

  if (!fallbackBody) return null;

  return {
    type: "markdown",
    title: task.title || "Artifact",
    body: String(fallbackBody),
    href: "",
    path: task.artifact_path || "",
    general_key: task.general_key || "",
    task_id: task.task_id || "",
    created_at: task.updated_at || task.created_at || "",
  };
}

export function pickRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.rows)) return payload.rows;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

export function renderMiniHealth(target, health) {
  if (!target) return;
  const ok = !!health?.ok;
  target.innerHTML = `
    <div class="metric-chip">
      <span class="dot ${ok ? "ok" : ""}"></span>
      <span>${esc(ok ? "command link active" : "attention needed")}</span>
    </div>
  `;
}

export function renderHealthCards(target, health) {
  if (!target) return;

  const cards = [
    ["API", health?.ok ? "online" : "degraded", health?.timestamp || ""],
    ["Database", health?.db_ok ? "up" : "down", health?.db_error || "SQLite ready"],
    ["LLM", health?.llm_ok ? "up" : "down", health?.provider || "No provider"],
    ["Environment", health?.app_env || "dev", "current runtime"],
  ];

  target.innerHTML = cards
    .map(
      ([title, value, meta]) => `
      <div class="health-card">
        <div class="card-title">${esc(title)}</div>
        <div style="font-size:28px;font-weight:900;line-height:1.1;margin:10px 0 6px;">${esc(value)}</div>
        <div class="card-meta">${esc(meta)}</div>
      </div>
    `
    )
    .join("");
}

export function renderSignalCorridor(target, state) {
  if (!target) return;

  const queued = state.tasks.filter((t) => t.status === "queued").length;
  const claimed = state.tasks.filter((t) => t.status === "claimed").length;
  const completed = state.tasks.filter((t) => t.status === "completed").length;
  const failed = state.tasks.filter((t) => t.status === "failed").length;

  const cards = [
    ["Runs", state.runs.length, "open mission threads"],
    ["Queued", queued, "awaiting execution"],
    ["Claimed", claimed, "currently owned"],
    ["Completed", completed, "delivered outcomes"],
    ["Failed", failed, "needs operator review"],
    [
      "Artifacts",
      state.tasks.filter((t) => normalizeArtifact(t)).length,
      "dock-ready outputs",
    ],
  ];

  target.innerHTML = cards
    .map(
      ([title, value, meta]) => `
      <div class="signal-card">
        <div class="card-title">${esc(title)}</div>
        <div style="font-size:32px;font-weight:900;line-height:1;margin:8px 0 4px;">${esc(value)}</div>
        <div class="card-meta">${esc(meta)}</div>
      </div>
    `
    )
    .join("");
}

export function renderRuns(target, runs, activeRunId) {
  if (!target) return;

  if (!runs.length) {
    target.innerHTML = `<div class="run-card"><div class="card-title">No runs yet</div><div class="card-meta">Create one to begin.</div></div>`;
    return;
  }

  target.innerHTML = runs
    .map((run) => {
      const runId = run.run_id || run.id || "";
      const isActive = runId === activeRunId;

      return `
        <div class="run-card">
          <div class="card-title">${esc(run.goal || run.title || runId || "Run")}</div>
          <div class="card-meta">
            run_id=${esc(runId)}<br/>
            project_key=${esc(run.project_key || "—")}<br/>
            adapter_key=${esc(run.adapter_key || "—")}<br/>
            status=${esc(run.status || "created")}
          </div>
          <div class="run-actions">
            <button class="ghost-btn sm" data-run-select="${esc(runId)}">
              ${isActive ? "Active run" : "Set active"}
            </button>
          </div>
        </div>
      `;
    })
    .join("");
}

export function renderMemory(target, rows) {
  if (!target) return;

  if (!rows.length) {
    target.innerHTML = `<div class="memory-card"><div class="card-title">No memory yet</div><div class="card-meta">This project has no memory entries right now.</div></div>`;
    return;
  }

  target.innerHTML = rows
    .map((row) => {
      const body = row.body || row.content || "";
      const metaBits = [
        row.memory_type || "note",
        row.source_task_id ? `task=${row.source_task_id}` : "",
        row.created_at ? formatDate(row.created_at) : "",
      ].filter(Boolean);

      return `
        <div class="memory-card">
          <div class="card-title">${esc(row.title || row.memory_id || "Memory entry")}</div>
          <div class="task-tags">
            ${metaBits.map((bit) => `<span class="pill">${esc(bit)}</span>`).join("")}
          </div>
          <div class="card-meta" style="margin-top:12px;">${esc(previewText(body, 420))}</div>
        </div>
      `;
    })
    .join("");
}

export function renderWorkbench(target, files) {
  if (!target) return;

  if (!files.length) {
    target.innerHTML = `<div class="file-card"><div class="card-title">No matching files</div><div class="card-meta">Try a different prefix filter.</div></div>`;
    return;
  }

  target.innerHTML = files
    .map((file) => `
      <div class="file-card">
        <div class="card-title">${esc(file.name || file.path || "file")}</div>
        <div class="card-meta">${esc(file.path || file.name || "")}</div>
      </div>
    `)
    .join("");
}

export function renderArtifacts(target, tasks) {
  if (!target) return;

  const rows = tasks
    .map((task) => ({ task, artifact: normalizeArtifact(task) }))
    .filter((entry) => entry.artifact);

  if (!rows.length) {
    target.innerHTML = `<div class="artifact-card"><div class="card-title">No artifacts</div><div class="card-meta">Run and complete tasks to populate the dock.</div></div>`;
    return;
  }

  target.innerHTML = rows
    .map(({ task, artifact }) => {
      const modalPayload = {
        task_id: task.task_id,
        title: artifact.title,
        general_key: artifact.general_key || task.general_key,
        status: task.status,
        artifact,
      };

      return `
        <div class="artifact-card">
          <div class="card-title">${esc(artifact.title || task.title || "Artifact")}</div>
          <div class="card-meta">
            ${esc(previewText(artifact.body, 220))}
          </div>
          <div class="task-tags">
            <span class="pill">${esc(artifact.type || "markdown")}</span>
            <span class="pill">${esc(task.status || "completed")}</span>
            ${artifact.path ? `<span class="pill">${esc(artifact.path)}</span>` : ""}
          </div>
          <div class="task-actions">
            <button class="ghost-btn sm" data-artifact-open='${esc(JSON.stringify(modalPayload))}'>Open</button>
            ${
              artifact.href
                ? `<a class="ghost-btn sm" href="${esc(artifact.href)}" target="_blank" rel="noreferrer">Open file</a>`
                : ""
            }
          </div>
        </div>
      `;
    })
    .join("");
}

function renderTaskCard(task) {
  const artifact = normalizeArtifact(task);

  return `
    <div class="task-card">
      <div class="task-title">${esc(task.title || "Untitled task")}</div>
      <div class="task-meta">
        task_id=${esc(task.task_id || "")}<br/>
        general=${esc(task.general_key || "")}<br/>
        type=${esc(task.task_type || "")}<br/>
        priority=${esc(task.priority ?? 0)}
      </div>
      ${
        artifact?.body
          ? `<div class="card-meta" style="margin-top:12px;">${esc(previewText(artifact.body, 220))}</div>`
          : ""
      }
      <div class="task-tags">
        <span class="pill">${esc(task.status || "unknown")}</span>
        <span class="pill">${esc(task.project_key || "no-project")}</span>
      </div>
      <div class="task-actions">
        <button class="ghost-btn sm" data-task-requeue="${esc(task.task_id || "")}">Requeue</button>
        <button class="ghost-btn sm" data-task-delete="${esc(task.task_id || "")}">Delete</button>
      </div>
    </div>
  `;
}

export function renderTaskBoard(target, tasks) {
  if (!target) return;

  const lanes = [
    ["queued", "Queued"],
    ["claimed", "Claimed"],
    ["completed", "Completed"],
    ["failed", "Failed"],
  ];

  target.innerHTML = lanes
    .map(([status, label]) => {
      const laneTasks = tasks.filter((task) => task.status === status);
      return `
        <section class="lane">
          <div class="lane-title">${esc(label)} · ${laneTasks.length}</div>
          <div class="lane-meta">${
            status === "queued"
              ? "Awaiting execution"
              : status === "claimed"
              ? "Currently active"
              : status === "completed"
              ? "Delivered outcomes"
              : "Needs review"
          }</div>
          ${
            laneTasks.length
              ? laneTasks.map(renderTaskCard).join("")
              : `<div class="task-card"><div class="task-meta">No tasks in this lane.</div></div>`
          }
        </section>
      `;
    })
    .join("");
}