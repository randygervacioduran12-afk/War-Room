const JSON_HEADERS = {
  "Content-Type": "application/json",
};

async function parseResponse(res) {
  const text = await res.text();
  let data = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

export async function getHealth() {
  const res = await fetch("/health");
  return parseResponse(res);
}

export async function listRuns() {
  const res = await fetch("/runs");
  return parseResponse(res);
}

export async function createRun(payload) {
  const res = await fetch("/runs", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  return parseResponse(res);
}

export async function listTasks(runId = "") {
  const url = runId ? `/tasks?run_id=${encodeURIComponent(runId)}` : "/tasks";
  const res = await fetch(url);
  return parseResponse(res);
}

export async function createTask(payload) {
  const res = await fetch("/tasks", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  return parseResponse(res);
}

export async function listMemory(projectKey) {
  const res = await fetch(`/memory?project_key=${encodeURIComponent(projectKey)}`);
  return parseResponse(res);
}

export async function createMemory(payload) {
  const res = await fetch("/memory", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  return parseResponse(res);
}

export async function listWorkbenchFiles(prefix = "") {
  const url = `/workbench/files?prefix=${encodeURIComponent(prefix)}`;
  const res = await fetch(url);
  return parseResponse(res);
}

export async function requeueTask(taskId) {
  const res = await fetch(`/admin/tasks/${encodeURIComponent(taskId)}/requeue`, {
    method: "POST",
  });
  return parseResponse(res);
}

export async function deleteTask(taskId) {
  const res = await fetch(`/admin/tasks/${encodeURIComponent(taskId)}`, {
    method: "DELETE",
  });
  return parseResponse(res);
}