import {
  getHealth,
  listRuns,
  createRun,
  listTasks,
  createTask,
  listMemory,
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

import { bootTheme, cycleTheme } from "/f65_ui_theme.js";
import { normalizeWorkbenchPayload } from "/f66_ui_workbench.js";
import { openArtifactModal, closeArtifactModal } from "/f67_ui_artifacts.js";
import { getPets, awardPetXp, renderPets } from "/f68_ui_pets.js";

const state = {
  activeRunId: localStorage.getItem("warroom_active_run_id") || "",
  activeProjectKey: localStorage.getItem("warroom_project_key") || "demo-project",
  autoPollTasks: true,
  health: null,
  runs: [],
  tasks: [],
  memory: [],
  workbench: [],
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
    "run-project-key",
    "run-adapter-key",
    "run-goal",
    "dispatch-general-key",
    "dispatch-task-type",
    "dispatch-title",
    "dispatch-message",
    "health-cards",
    "signal-corridor",
    "task-board",
    "runs-list",
    "memory-list",
    "workbench-grid",
    "artifact-grid",
    "pet-list",
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

function setActiveRun(runId) {
  state.activeRunId = runId || "";
  localStorage.setItem("warroom_active_run_id", state.activeRunId);
  renderHeaderMetrics();
  renderRuns(el["runs-list"], state.runs, state.activeRunId);
}

function renderHeaderMetrics() {
  if (el["active-run-id"]) {
    el["active-run-id"].textContent = state.activeRunId || "No active run";
  }

  if (el["active-run-meta"]) {
    el["active-run-meta"].textContent = state.activeRunId
      ? "Context locked to this mission"
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
    (t) => t.artifact_json || t.artifact_path || t.output_payload || t.result_json
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
    if (el["health-overview"]) el["health-overview"].textContent = "Health check failed";
    if (el["health-meta"]) el["health-meta"].textContent = "Unable to reach /health";
  }
}

async function refreshRuns() {
  try {
    const payload = await listRuns();
    state.runs = pickRows(payload);
    renderRuns(el["runs-list"], state.runs, state.activeRunId);

    if (!state.activeRunId && state.runs.length) {
      const first = state.runs[0];
      setActiveRun(first.run_id || first.id || "");
    }

    renderSignalCorridor(el["signal-corridor"], state);
  } catch (err) {
    console.error(err);
    el["runs-list"].innerHTML = `<div class="run-card"><div class="card-title">Run load failed</div><div class="card-meta">${escapeError(err)}</div></div>`;
  }
}

async function refreshTasks() {
  try {
    const payload = await listTasks(state.activeRunId);
    state.tasks = pickRows(payload);
    renderTaskBoard(el["task-board"], state.tasks);
    renderArtifacts(el["artifact-grid"], state.tasks);
    renderHeaderMetrics();
    renderSignalCorridor(el["signal-corridor"], state);
  } catch (err) {
    console.error(err);
    el["task-board"].innerHTML = `<div class="task-card"><div class="task-title">Task load failed</div><div class="task-meta">${escapeError(err)}</div></div>`;
  }
}

async function refreshMemory() {
  try {
    const payload = await listMemory(state.activeProjectKey);
    state.memory = pickRows(payload);
    renderMemory(el["memory-list"], state.memory);
  } catch (err) {
    console.error(err);
    el["memory-list"].innerHTML = `<div class="memory-card"><div class="card-title">Memory load failed</div><div class="card-meta">${escapeError(err)}</div></div>`;
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

function refreshArtifactsOnly() {
  renderArtifacts(el["artifact-grid"], state.tasks);
}

function renderPetsNow() {
  renderPets(el["pet-list"], getPets());
}

function switchView(view) {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === view);
  });

  document.querySelectorAll(".view-panel").forEach((section) => {
    section.classList.toggle("active-view", section.id === `view-${view}`);
  });
}

async function handleCreateRun() {
  const payload = {
    project_key: el["run-project-key"].value.trim(),
    adapter_key: el["run-adapter-key"].value.trim(),
    goal: el["run-goal"].value.trim(),
  };

  state.activeProjectKey = payload.project_key || "demo-project";
  localStorage.setItem("warroom_project_key", state.activeProjectKey);

  try {
    const data = await createRun(payload);
    el["launch-result"].textContent = JSON.stringify(data, null, 2);

    const runId = data?.run_id || data?.id || data?.run?.run_id || "";
    if (runId) setActiveRun(runId);

    await refreshRuns();
    await refreshTasks();
    switchView("signals");
  } catch (err) {
    console.error(err);
    el["launch-result"].textContent = JSON.stringify(
      {
        error: "Run creation failed",
        detail: err?.data || err?.message || String(err),
      },
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

  const payload = {
    run_id: state.activeRunId,
    general_key: el["dispatch-general-key"].value.trim(),
    task_type: el["dispatch-task-type"].value.trim(),
    title: el["dispatch-title"].value.trim(),
    project_key: state.activeProjectKey,
    operator_message: el["dispatch-message"].value.trim(),
    input_payload: {},
    payload_json: {
      operator_message: el["dispatch-message"].value.trim(),
    },
  };

  try {
    const data = await createTask(payload);
    el["dispatch-result"].textContent = JSON.stringify(data, null, 2);

    await refreshTasks();

    awardPetXp(payload.general_key, 8);
    renderPetsNow();
    switchView("signals");
  } catch (err) {
    console.error(err);
    el["dispatch-result"].textContent = JSON.stringify(
      {
        error: "Task dispatch failed",
        detail: err?.data || err?.message || String(err),
      },
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
  } catch (err) {
    console.error(err);
    alert(`Requeue failed: ${escapeError(err)}`);
  }
}

async function handleDelete(taskId) {
  if (!taskId) return;
  try {
    await deleteTask(taskId);
    await refreshTasks();
  } catch (err) {
    console.error(err);
    alert(`Delete failed: ${escapeError(err)}`);
  }
}

async function refreshAll() {
  await refreshHealth();
  await refreshRuns();
  await refreshTasks();
  await refreshMemory();
  await refreshWorkbench();
  refreshArtifactsOnly();
  renderPetsNow();
}

function bindEvents() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
  });

  document.getElementById("theme-cycle-btn")?.addEventListener("click", cycleTheme);
  document.getElementById("refresh-all-btn")?.addEventListener("click", refreshAll);
  document.getElementById("health-refresh-btn")?.addEventListener("click", refreshHealth);
  document.getElementById("load-runs-btn")?.addEventListener("click", refreshRuns);
  document.getElementById("load-tasks-btn")?.addEventListener("click", refreshTasks);
  document.getElementById("load-memory-btn")?.addEventListener("click", refreshMemory);
  document.getElementById("load-workbench-btn")?.addEventListener("click", refreshWorkbench);
  document.getElementById("load-artifacts-btn")?.addEventListener("click", refreshArtifactsOnly);

  document.getElementById("create-run-btn")?.addEventListener("click", handleCreateRun);
  document.getElementById("dispatch-task-btn")?.addEventListener("click", handleDispatchTask);

  document.getElementById("open-launch-btn")?.addEventListener("click", () => switchView("operations"));
  document.getElementById("hero-launch-btn")?.addEventListener("click", () => switchView("operations"));
  document.getElementById("hero-dispatch-btn")?.addEventListener("click", () => switchView("operations"));

  document.getElementById("auto-poll-tasks-btn")?.addEventListener("click", (e) => {
    state.autoPollTasks = !state.autoPollTasks;
    e.currentTarget.textContent = `Auto poll: ${state.autoPollTasks ? "on" : "off"}`;
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
        await refreshTasks();
      }
    } catch (err) {
      console.error(err);
    }
  }, 7000);
}

async function boot() {
  cacheDom();
  bootTheme();
  bindEvents();
  renderPetsNow();
  switchView("overview");
  await refreshAll();
  startPolling();
}

boot();