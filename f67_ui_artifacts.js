function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function looksLikeJson(value) {
  if (typeof value !== "string") return false;
  const trimmed = value.trim();
  return (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
         (trimmed.startsWith("[") && trimmed.endsWith("]"));
}

function renderJsonBlock(obj) {
  const entries = Object.entries(obj || {});
  return `
    <div class="kv">
      ${entries.map(([key, val]) => `
        <div class="kv-row">
          <div class="kv-key">${esc(key)}</div>
          <div>${typeof val === "object" && val !== null ? `<pre>${esc(JSON.stringify(val, null, 2))}</pre>` : esc(val)}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderMarkdownish(text) {
  const html = esc(text)
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");

  return `<div class="markdown-view">${html}</div>`;
}

export function openArtifactModal(modal, subtitleEl, bodyEl, payload) {
  if (!modal || !subtitleEl || !bodyEl) return;

  subtitleEl.textContent = payload?.title || payload?.task_id || "Artifact";

  const raw = payload?.artifact;

  if (typeof raw === "object" && raw !== null) {
    bodyEl.innerHTML = renderJsonBlock(raw);
  } else if (looksLikeJson(raw)) {
    try {
      const parsed = JSON.parse(raw);
      bodyEl.innerHTML = renderJsonBlock(parsed);
    } catch {
      bodyEl.innerHTML = renderMarkdownish(String(raw || ""));
    }
  } else {
    bodyEl.innerHTML = renderMarkdownish(String(raw || "No artifact body"));
  }

  modal.classList.remove("hidden");
}

export function closeArtifactModal(modal) {
  if (!modal) return;
  modal.classList.add("hidden");
}