function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
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
    <div class="metric-chip wide">
      <span class="dot ${ok ? "ok" : ""}"></span>
      <span>${ok ? "command link active" : "attention needed"}</span>
    </div>
  `;
}

export function renderHealthCards(target, health) {
  if (!target) return;

  const rows = [
    ["App", health?.app_env || "dev", !!health?.ok],
    ["DB", health?.db_ok ? "connected" : "down", !!health?.db_ok],
    ["LLM", health?.llm_ok ? "ready" : "down", !!health?.llm_ok],
    ["App runtime", `env=${health?.app_env || "dev"}`, !!health?.ok],
    ["Database", health?.db_ok ? "storage online" : "storage down", !!health?.db_ok],
    ["LLM path", health?.llm_ok ? "generation path ready" : "generation path down", !!health?.llm_ok],
    ["Timestamp", health?.timestamp || "n/a", false],
  ];

  target.innerHTML = rows
    .map(
      ([title, meta, ok]) => `
      <div class="health-card">
        <div class="card-title">${esc(title)}</div>
        <div class="card-meta">${esc(meta)}</div>
        <div class="task-tags">
          <span class="pill">${ok ? "● live" : "• info"}</span>
        </div>
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
    ["Artifacts", state.tasks.filter((t) => t.artifact_json || t.artifact_path || t.output_payload || t.result_json).length, "dock-ready outputs"],
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
    .map((row) => `
      <div class="memory-card">
        <div class="card-title">${esc(row.title || row.memory_id || "Memory entry")}</div>
        <div class="card-meta">${esc(row.summary || row.content || row.body || "")}</div>
      </div>
    `)
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

function readArtifact(task) {
  return (
    task.artifact_json ||
    task.result_json ||
    task.output_payload ||
    task.payload_json ||
    task.artifact_path ||
    ""
  );
}

export function renderArtifacts(target, tasks) {
  if (!target) return;

  const rows = tasks.filter((t) => t.artifact_json || t.artifact_path || t.output_payload || t.result_json);

  if (!rows.length) {
    target.innerHTML = `<div class="artifact-card"><div class="card-title">No artifacts</div><div class="card-meta">Run and complete tasks to populate the dock.</div></div>`;
    return;
  }

  target.innerHTML = rows
    .map((task) => {
      const payload = {
        task_id: task.task_id,
        title: task.title,
        general_key: task.general_key,
        status: task.status,
        artifact: readArtifact(task),
      };

      return `
        <div class="artifact-card">
          <div class="card-title">${esc(task.title || "Artifact")}</div>
          <div class="card-meta">
            task_id=${esc(task.task_id || "")}<br/>
            general=${esc(task.general_key || "")}<br/>
            status=${esc(task.status || "")}
          </div>
          <div class="task-actions">
            <button class="ghost-btn sm" data-artifact-open='${esc(JSON.stringify(payload))}'>Open</button>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderTaskCard(task) {
  return `
    <div class="task-card">
      <div class="task-title">${esc(task.title || "Untitled task")}</div>
      <div class="task-meta">
        task_id=${esc(task.task_id || "")}<br/>
        general=${esc(task.general_key || "")}<br/>
        type=${esc(task.task_type || "")}<br/>
        priority=${esc(task.priority ?? 0)}
      </div>
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
          <div class="lane-meta">${status === "queued" ? "Awaiting execution" : status === "claimed" ? "Currently active" : status === "completed" ? "Delivered outcomes" : "Needs review"}</div>
          ${laneTasks.length ? laneTasks.map(renderTaskCard).join("") : `<div class="task-card"><div class="task-meta">No tasks in this lane.</div></div>`}
        </section>
      `;
    })
    .join("");
}