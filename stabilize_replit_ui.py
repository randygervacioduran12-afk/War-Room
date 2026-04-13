from pathlib import Path
import re

ROOT = Path(".")

UI_FILES = [
    "f60_ui_shell.html",
    "f61_ui_styles.css",
    "f62_ui_app.js",
    "f63_ui_api.js",
    "f64_ui_components.js",
    "f65_ui_theme.js",
    "f66_ui_workbench.js",
    "f67_ui_artifacts.js",
    "f68_ui_pets.js",
    "f69_ui_motion.js",
]

SMART_MAP = str.maketrans({
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "\u00a0": " ",
})

F64_UI_COMPONENTS = r'''function esc(value) {
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
  const t = value.trim();
  if (!t) return null;
  if ((t.startsWith("{") && t.endsWith("}")) || (t.startsWith("[") && t.endsWith("]"))) {
    try {
      return JSON.parse(t);
    } catch {
      return value;
    }
  }
  return value;
}

function previewText(value, max = 220) {
  if (value == null) return "";
  let text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  text = text.replace(/```[\s\S]*?```/g, "[code block]");
  text = text.replace(/\s+/g, " ").trim();
  return text.length <= max ? text : `${text.slice(0, max - 3)}...`;
}

function formatDate(value) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return String(value);
  }
}

function inferHref(path) {
  if (!path) return "";
  if (String(path).startsWith("/")) return path;
  return `/artifact-files/${String(path).replace(/^\/+/, "")}`;
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
  const fallbackPath = task?.artifact_path || "";

  if (artifact && typeof artifact === "object") {
    const path = artifact.path || fallbackPath || "";
    return {
      type: artifact.type || "markdown",
      title: artifact.title || task.title || "Artifact",
      body:
        artifact.body ||
        artifact.content ||
        artifact.text ||
        resultJson?.raw_text ||
        resultJson?.summary ||
        outputPayload?.summary ||
        "",
      href: artifact.href || inferHref(path),
      path,
      general_key: artifact.general_key || task.general_key || "",
      task_id: artifact.task_id || task.task_id || "",
      created_at: artifact.created_at || task.updated_at || task.created_at || "",
    };
  }

  const summaryBody =
    (resultJson && typeof resultJson === "object" && (resultJson.summary || resultJson.raw_text)) ||
    (outputPayload && typeof outputPayload === "object" && (outputPayload.summary || outputPayload.raw_text)) ||
    "";

  if (summaryBody || fallbackPath) {
    return {
      type: "markdown",
      title: task.title || "Artifact",
      body: String(summaryBody || "Open generated file."),
      href: inferHref(fallbackPath),
      path: fallbackPath,
      general_key: task.general_key || "",
      task_id: task.task_id || "",
      created_at: task.updated_at || task.created_at || "",
    };
  }

  return null;
}

function statusPill(status) {
  const map = {
    queued: "pill pill-queued",
    claimed: "pill pill-claimed",
    completed: "pill pill-completed",
    failed: "pill pill-failed",
  };
  return `<span class="${map[status] || "pill"}">${esc(status || "unknown")}</span>`;
}

function emptyState(icon, message) {
  return `
    <div style="text-align:center;padding:36px 20px;color:var(--text-3);">
      <div style="font-size:32px;margin-bottom:12px;opacity:0.4;">${icon}</div>
      <div style="font-family:var(--f-mono);font-size:12px;">${esc(message)}</div>
    </div>
  `;
}

export function pickRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.rows)) return payload.rows;
  if (Array.isArray(payload?.runs)) return payload.runs;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

export function renderMiniHealth(target, health) {
  if (!target) return;
  const ok = !!health?.ok;
  target.innerHTML = `
    <span class="dot ${ok ? "ok" : "err"}"></span>
    <span style="font-family:var(--f-mono);font-size:11.5px;">
      ${esc(ok ? "command link active" : "attention needed")}
    </span>
  `;
}

export function renderHealthCards(target, health) {
  if (!target) return;
  const cards = [
    ["API", health?.ok ? "online" : "degraded", health?.timestamp || ""],
    ["Database", health?.db_ok ? "up" : "down", health?.db_error || "storage ready"],
    ["LLM", health?.llm_ok ? "up" : "down", health?.provider || "provider missing"],
    ["Environment", health?.app_env || "dev", "current runtime"],
  ];

  target.innerHTML = cards.map(([title, value, meta]) => `
    <div class="health-card">
      <div class="card-title">${esc(title)}</div>
      <div style="font-family:var(--f-display);font-size:26px;font-weight:800;line-height:1.05;margin:8px 0 5px;letter-spacing:-0.025em;">
        ${esc(value)}
      </div>
      <div class="card-meta">${esc(meta)}</div>
    </div>
  `).join("");
}

export function renderSignalCorridor(target, state) {
  if (!target) return;

  const queued = state.tasks.filter(t => t.status === "queued").length;
  const claimed = state.tasks.filter(t => t.status === "claimed").length;
  const completed = state.tasks.filter(t => t.status === "completed").length;
  const failed = state.tasks.filter(t => t.status === "failed").length;
  const artifacts = state.tasks.filter(t => normalizeArtifact(t)).length;

  const cards = [
    ["Runs", state.runs.length, "mission threads", ""],
    ["Queued", queued, "awaiting execution", queued ? "warn" : ""],
    ["Claimed", claimed, "currently owned", claimed ? "ok" : ""],
    ["Completed", completed, "delivered outcomes", completed ? "ok" : ""],
    ["Failed", failed, "needs review", failed ? "err" : ""],
    ["Artifacts", artifacts, "dock-ready outputs", artifacts ? "ok" : ""],
    ["Project", state.activeProjectKey || "-", "current context", ""],
    [
      "Active run",
      state.activeRunId ? `${state.activeRunId.slice(0, 16)}...` : "-",
      "selected mission",
      state.activeRunId ? "ok" : "",
    ],
  ];

  target.innerHTML = cards.map(([title, value, meta, dot]) => `
    <div class="signal-card">
      <div class="card-title">${esc(title)}</div>
      <div style="font-family:var(--f-display);font-size:24px;font-weight:800;line-height:1.05;margin:7px 0 4px;word-break:break-word;letter-spacing:-0.02em;">
        ${dot ? `<span class="dot ${dot}" style="display:inline-block;margin-right:8px;vertical-align:middle;"></span>` : ""}
        ${esc(String(value))}
      </div>
      <div class="card-meta">${esc(meta)}</div>
    </div>
  `).join("");
}

export function renderRuns(target, runs, activeRunId) {
  if (!target) return;
  if (!runs.length) {
    target.innerHTML = emptyState("⚡", "No runs yet - launch one to begin.");
    return;
  }

  target.innerHTML = runs.map(run => {
    const runId = run.run_id || run.id || "";
    const isActive = runId === activeRunId;

    return `
      <div class="run-card ${isActive ? "active-run" : ""}">
        <div class="card-title">${esc(run.goal || run.title || "Mission")}</div>
        <div class="card-meta" style="margin-top:7px;">
          <span style="font-family:var(--f-mono);font-size:11px;opacity:0.7;">
            ${esc(runId)}<br>
            ${esc(run.project_key || "")} · ${esc(run.status || "created")}
          </span>
        </div>
        <div class="run-actions">
          <button class="ghost-btn sm" data-run-select="${esc(runId)}">
            ${isActive ? "✓ Active run" : "Set active"}
          </button>
        </div>
      </div>
    `;
  }).join("");
}

export function renderMemory(target, rows) {
  if (!target) return;
  if (!rows.length) {
    target.innerHTML = emptyState("◉", "No memory entries yet.");
    return;
  }

  target.innerHTML = rows.map(row => {
    const body = row.body || row.content || "";
    const bits = [
      row.memory_type || "note",
      row.source_task_id ? `task=${row.source_task_id.slice(0, 10)}...` : "",
      row.created_at ? formatDate(row.created_at) : "",
    ].filter(Boolean);

    return `
      <div class="memory-card">
        <div class="card-title">${esc(row.title || row.memory_id || "Memory entry")}</div>
        <div class="task-tags">
          ${bits.map(b => `<span class="pill">${esc(b)}</span>`).join("")}
        </div>
        <div class="card-meta" style="margin-top:10px;line-height:1.6;">
          ${esc(previewText(body, 600))}
        </div>
      </div>
    `;
  }).join("");
}

export function renderWorkbench(target, files) {
  if (!target) return;
  if (!files.length) {
    target.innerHTML = emptyState("⌗", "No matching files - try a different prefix.");
    return;
  }

  target.innerHTML = files.map(file => `
    <div class="file-card">
      <div class="card-title">${esc(file.name || file.path || "file")}</div>
      <div class="card-meta" style="font-family:var(--f-mono);font-size:11px;">
        ${esc(file.path || file.name || "")}
      </div>
    </div>
  `).join("");
}

export function renderArtifacts(target, tasks) {
  if (!target) return;

  const rows = tasks
    .map(task => ({ task, artifact: normalizeArtifact(task) }))
    .filter(entry => entry.artifact);

  if (!rows.length) {
    target.innerHTML = emptyState("◎", "Complete tasks to populate the artifact dock.");
    return;
  }

  target.innerHTML = rows.map(({ task, artifact }) => {
    const modalPayload = {
      task_id: task.task_id,
      title: artifact.title,
      general_key: artifact.general_key || task.general_key,
      status: task.status,
      artifact,
    };

    const encoded = esc(JSON.stringify(modalPayload));

    return `
      <div class="artifact-card">
        <div class="card-title">${esc(artifact.general_key || "artifact")}</div>
        <div style="font-family:var(--f-display);font-size:17px;font-weight:700;margin:6px 0 8px;line-height:1.2;">
          ${esc(artifact.title || task.title || "Artifact")}
        </div>
        <div class="card-meta">${esc(previewText(artifact.body, 260))}</div>
        <div class="task-tags">
          <span class="pill">${esc(artifact.type || "markdown")}</span>
          ${statusPill(task.status)}
          ${artifact.general_key ? `<span class="pill">${esc(artifact.general_key)}</span>` : ""}
        </div>
        <div class="artifact-links">
          ${artifact.href ? `<a class="ghost-btn sm" href="${esc(artifact.href)}" target="_blank" rel="noreferrer">Open file</a>` : ""}
          <button class="ghost-btn sm" data-artifact-open='${encoded}'>Preview</button>
        </div>
        ${artifact.path ? `<div class="card-meta" style="margin-top:10px;font-family:var(--f-mono);font-size:10.5px;opacity:0.6;">${esc(artifact.path)}</div>` : ""}
      </div>
    `;
  }).join("");
}

function renderTaskCard(task) {
  const artifact = normalizeArtifact(task);

  return `
    <div class="task-card">
      <div class="task-title">${esc(task.title || "Untitled task")}</div>
      <div class="task-meta" style="font-family:var(--f-mono);font-size:10.5px;margin-top:5px;line-height:1.7;">
        ${esc(task.task_id || "")} · ${esc(task.general_key || "")} · ${esc(task.task_type || "")}
      </div>
      ${artifact?.body ? `<div class="card-meta" style="margin-top:10px;">${esc(previewText(artifact.body, 200))}</div>` : ""}
      <div class="task-tags">
        ${statusPill(task.status)}
        <span class="pill">${esc(task.project_key || "no-project")}</span>
      </div>
      <div class="task-actions">
        <button class="ghost-btn sm" data-task-requeue="${esc(task.task_id || "")}">↺ Requeue</button>
        <button class="ghost-btn sm" data-task-delete="${esc(task.task_id || "")}">✕ Delete</button>
      </div>
    </div>
  `;
}

export function renderTaskBoard(target, tasks) {
  if (!target) return;

  const lanes = [
    ["queued", "Queued", "Awaiting execution"],
    ["claimed", "Claimed", "Currently active"],
    ["completed", "Completed", "Delivered outcomes"],
    ["failed", "Failed", "Needs review"],
  ];

  target.innerHTML = lanes.map(([status, label, meta]) => {
    const lane = tasks.filter(t => t.status === status);
    return `
      <section class="lane">
        <div class="lane-title">${esc(label)} · <span style="color:var(--text-2);">${lane.length}</span></div>
        <div class="lane-meta" style="margin-bottom:12px;">${esc(meta)}</div>
        ${lane.length
          ? lane.map(renderTaskCard).join("")
          : `<div class="task-card"><div class="task-meta">No tasks in this lane.</div></div>`}
      </section>
    `;
  }).join("");
}
'''

F65_UI_THEME = r'''const THEMES = [
  {
    name: "sanctuary",
    label: "Sanctuary",
    bg: "radial-gradient(ellipse 80% 60% at 50% 50%, rgba(210,118,78,0.09) 0%, transparent 55%), radial-gradient(ellipse 65% 55% at 75% 25%, rgba(124,85,248,0.11) 0%, transparent 50%), radial-gradient(ellipse 55% 45% at 20% 70%, rgba(0,180,255,0.07) 0%, transparent 50%), linear-gradient(155deg, #030409 0%, #060812 45%, #030409 100%)",
    orange: "#d97b55",
    cyan: "#00d4ff",
  },
  {
    name: "neon-city",
    label: "Neon City",
    bg: "radial-gradient(ellipse 60% 50% at 12% 0%, rgba(0,197,255,0.15) 0%, transparent 55%), radial-gradient(ellipse 50% 40% at 88% 8%, rgba(255,55,155,0.11) 0%, transparent 50%), radial-gradient(ellipse 40% 40% at 50% 85%, rgba(124,85,248,0.08) 0%, transparent 50%), linear-gradient(155deg, #04060d 0%, #06091a 45%, #030508 100%)",
    orange: "#00c8ff",
    cyan: "#ff3ca0",
  },
  {
    name: "amber-core",
    label: "Amber Core",
    bg: "radial-gradient(ellipse 65% 50% at 15% 5%, rgba(230,180,70,0.13) 0%, transparent 55%), radial-gradient(ellipse 45% 35% at 82% 15%, rgba(210,95,80,0.10) 0%, transparent 50%), linear-gradient(155deg, #080709 0%, #120e0d 45%, #080709 100%)",
    orange: "#e8b450",
    cyan: "#f09050",
  },
  {
    name: "planet-ice",
    label: "Planet Ice",
    bg: "radial-gradient(ellipse 60% 50% at 15% 5%, rgba(88,208,255,0.13) 0%, transparent 55%), radial-gradient(ellipse 45% 38% at 85% 12%, rgba(128,148,255,0.12) 0%, transparent 50%), linear-gradient(155deg, #060e18 0%, #08101c 45%, #050b12 100%)",
    orange: "#58d2ff",
    cyan: "#a0b8ff",
  },
  {
    name: "destiny",
    label: "Destiny HUD",
    bg: "radial-gradient(ellipse 55% 45% at 10% 0%, rgba(255,188,55,0.11) 0%, transparent 55%), radial-gradient(ellipse 40% 35% at 90% 10%, rgba(178,128,48,0.09) 0%, transparent 50%), linear-gradient(155deg, #080700 0%, #100d03 45%, #070600 100%)",
    orange: "#f5bb40",
    cyan: "#c8a838",
  },
  {
    name: "void-noir",
    label: "Void Noir",
    bg: "radial-gradient(ellipse 70% 55% at 5% -5%, rgba(124,85,248,0.15) 0%, transparent 60%), radial-gradient(ellipse 60% 45% at 95% 105%, rgba(210,118,78,0.12) 0%, transparent 55%), radial-gradient(ellipse 40% 35% at 100% 30%, rgba(0,180,255,0.065) 0%, transparent 50%), linear-gradient(155deg, #030409 0%, #050820 45%, #03040a 100%)",
    orange: "#d97b55",
    cyan: "#00d4ff",
  },
];

let idx = 0;

export function applyTheme(i = 0) {
  idx = ((i % THEMES.length) + THEMES.length) % THEMES.length;
  const t = THEMES[idx];

  document.body.style.background = t.bg;
  document.documentElement.style.setProperty("--orange", t.orange);
  document.documentElement.style.setProperty("--amber", t.orange === "#d97b55" ? "#e9a355" : t.orange);
  document.documentElement.style.setProperty("--cyan", t.cyan);

  localStorage.setItem("warroom_theme", String(idx));
}

export function cycleTheme() {
  applyTheme(idx + 1);
  return THEMES[idx].label;
}

export function bootTheme() {
  const saved = parseInt(localStorage.getItem("warroom_theme") || "0", 10);
  applyTheme(Number.isNaN(saved) ? 0 : saved);
}

export function getThemes() {
  return THEMES;
}

export function getCurrentTheme() {
  return THEMES[idx];
}
'''

F67_UI_ARTIFACTS = r'''function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function looksLikeJson(value) {
  if (typeof value !== "string") return false;
  const trimmed = value.trim();
  return (
    (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
    (trimmed.startsWith("[") && trimmed.endsWith("]"))
  );
}

function renderJsonBlock(obj) {
  const entries = Object.entries(obj || {});
  return `
    <div class="kv">
      ${entries.map(([key, val]) => `
        <div class="kv-row">
          <div class="kv-key">${esc(key)}</div>
          <div>${
            typeof val === "object" && val !== null
              ? `<pre>${esc(JSON.stringify(val, null, 2))}</pre>`
              : esc(val)
          }</div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderMarkdownish(text) {
  const source = String(text || "");
  const fenceMatches = [];

  const withoutFences = source.replace(
    /```([a-zA-Z0-9_-]+)?\n([\s\S]*?)```/g,
    (_, _lang, code) => {
      const token = `__CODE_BLOCK_${fenceMatches.length}__`;
      fenceMatches.push(`<pre><code>${esc(code.trim())}</code></pre>`);
      return token;
    }
  );

  const lines = withoutFences.split("\n");
  const out = [];
  let inList = false;

  const flushList = () => {
    if (inList) {
      out.push("</ul>");
      inList = false;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      continue;
    }

    if (line.startsWith("### ")) {
      flushList();
      out.push(`<h3>${esc(line.slice(4))}</h3>`);
      continue;
    }

    if (line.startsWith("## ")) {
      flushList();
      out.push(`<h2>${esc(line.slice(3))}</h2>`);
      continue;
    }

    if (line.startsWith("# ")) {
      flushList();
      out.push(`<h1>${esc(line.slice(2))}</h1>`);
      continue;
    }

    if (line.startsWith("- ") || line.startsWith("* ")) {
      if (!inList) {
        out.push("<ul>");
        inList = true;
      }
      const item = esc(line.slice(2))
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
      out.push(`<li>${item}</li>`);
      continue;
    }

    flushList();

    const html = esc(line)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");

    out.push(`<p>${html}</p>`);
  }

  flushList();

  let html = out.join("");
  fenceMatches.forEach((block, index) => {
    html = html.replace(`__CODE_BLOCK_${index}__`, block);
  });

  return `<div class="markdown-view">${html || "<p>No artifact body</p>"}</div>`;
}

function inferHref(path) {
  if (!path) return "";
  if (String(path).startsWith("/")) return path;
  return `/artifact-files/${String(path).replace(/^\/+/, "")}`;
}

function normalizeArtifactPayload(payload) {
  if (!payload) return null;

  const artifact = payload.artifact || payload;
  if (!artifact || typeof artifact !== "object") return null;

  const path = artifact.path || "";
  const href = artifact.href || inferHref(path);

  return {
    title: artifact.title || payload.title || payload.task_id || "Artifact",
    body: artifact.body || artifact.content || artifact.text || "",
    href,
    path,
    type: artifact.type || "markdown",
  };
}

export function openArtifactModal(modal, subtitleEl, bodyEl, payload) {
  if (!modal || !subtitleEl || !bodyEl) return;

  const artifact = normalizeArtifactPayload(payload);
  subtitleEl.textContent =
    artifact?.title || payload?.title || payload?.task_id || "Artifact";

  const parts = [];

  if (artifact?.href || artifact?.path || artifact?.type) {
    parts.push(`
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;">
        ${artifact?.href ? `
          <a
            href="${esc(artifact.href)}"
            target="_blank"
            rel="noreferrer"
            class="ghost-btn sm"
            style="display:inline-flex;align-items:center;justify-content:center;"
          >
            Open file
          </a>
        ` : ""}
        ${artifact?.path ? `<div class="pill">${esc(artifact.path)}</div>` : ""}
        ${artifact?.type ? `<div class="pill">${esc(artifact.type)}</div>` : ""}
      </div>
    `);
  }

  const raw = artifact?.body ?? payload?.artifact ?? "";

  if (typeof raw === "object" && raw !== null) {
    parts.push(renderJsonBlock(raw));
  } else if (looksLikeJson(raw)) {
    try {
      const parsed = JSON.parse(raw);
      parts.push(renderJsonBlock(parsed));
    } catch {
      parts.push(renderMarkdownish(String(raw || "")));
    }
  } else {
    parts.push(renderMarkdownish(String(raw || "No artifact body")));
  }

  bodyEl.innerHTML = parts.join("");
  modal.classList.remove("hidden");
}

export function closeArtifactModal(modal) {
  if (!modal) return;
  modal.classList.add("hidden");
}
'''

def backup(path: Path):
    bak = path.with_suffix(path.suffix + ".bak")
    if path.exists() and not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")

def write_file(name: str, text: str):
    path = ROOT / name
    if path.exists():
      backup(path)
    path.write_text(text, encoding="utf-8")

def sanitize_text(name: str, text: str) -> str:
    text = text.translate(SMART_MAP)

    if name == "f60_ui_shell.html":
        text = "\n".join(line for line in text.splitlines() if line.strip() != "```")
        text = text.replace("?v=300", "?v=301")

    if name == "f61_ui_styles.css":
        if "--text-2:" not in text and ":root {" in text:
            text = text.replace(
                ":root {",
                ":root {\n  --text-2: var(--t2);\n  --text-3: var(--t3);\n  --f-mono: var(--f-m);\n  --f-display: var(--f-d);\n",
                1,
            )

    return text.rstrip() + "\n"

def patch_replit():
    path = ROOT / ".replit"
    if not path.exists():
        return

    backup(path)
    text = path.read_text(encoding="utf-8", errors="replace")

    if "externalPort" not in text:
        text = text.replace(
            "[[ports]]\nlocalPort = 8000",
            "[[ports]]\nlocalPort = 8000\nexternalPort = 80"
        )

    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    print("[patched] .replit")

def quick_scan():
    bad = []
    for name in UI_FILES:
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for ch in ('“', '”', '‘', '’'):
            if ch in text:
                bad.append((name, ch))
    return bad

def main():
    for name in UI_FILES:
        path = ROOT / name
        if not path.exists():
            print(f"[missing] {name}")
            continue
        cleaned = sanitize_text(name, path.read_text(encoding="utf-8", errors="replace"))
        write_file(name, cleaned)
        print(f"[sanitized] {name}")

    write_file("f64_ui_components.js", F64_UI_COMPONENTS.strip() + "\n")
    print("[rewritten] f64_ui_components.js")

    write_file("f65_ui_theme.js", F65_UI_THEME.strip() + "\n")
    print("[rewritten] f65_ui_theme.js")

    write_file("f67_ui_artifacts.js", F67_UI_ARTIFACTS.strip() + "\n")
    print("[rewritten] f67_ui_artifacts.js")

    patch_replit()

    remaining = quick_scan()
    if remaining:
        print("[warning] remaining smart quotes found:")
        for item in remaining:
            print(" -", item[0], item[1])
    else:
        print("[ok] no smart quotes found in UI files")

    print("\nNext steps:")
    print("1. Stop the app")
    print("2. Run: python stabilize_replit_ui.py")
    print("3. Run: python app.py")
    print("4. Reopen Preview")
    print("5. Hard refresh the page")
    print("6. If Preview still stalls, use the Networking/Ports panel and confirm 8000 -> 80")

if __name__ == "__main__":
    main()