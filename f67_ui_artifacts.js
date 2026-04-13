function esc(value) {
return String(value ?? “”)
.replaceAll(”&”, “&”)
.replaceAll(”<”, “<”)
.replaceAll(”>”, “>”)
.replaceAll(’”’, ‘”’);
}

function looksLikeJson(value) {
if (typeof value !== “string”) return false;
const trimmed = value.trim();
return (
(trimmed.startsWith(”{”) && trimmed.endsWith(”}”)) ||
(trimmed.startsWith(”[”) && trimmed.endsWith(”]”))
);
}

function renderJsonBlock(obj) {
const entries = Object.entries(obj || {});
return `<div class="kv"> ${entries .map( ([key, val]) =>`

<div class="kv-row">
<div class="kv-key">${esc(key)}</div>
<div>${
typeof val === "object" && val !== null
? `<pre>${esc(JSON.stringify(val, null, 2))}</pre>`
: esc(val)
}</div>
</div>
`) .join("")} </div>`;
}

function renderMarkdownish(text) {
const source = String(text || “”);

const fenceMatches = [];
const withoutFences = source.replace(
/`([a-zA-Z0-9_-]+)?\n([\s\S]*?)`/g,
(_, _lang, code) => {
const token = `__CODE_BLOCK_${fenceMatches.length}__`;
fenceMatches.push(`<pre><code>${esc(code.trim())}</code></pre>`);
return token;
}
);

const lines = withoutFences.split(”\n”);
const out = [];
let inList = false;

const flushList = () => {
if (inList) {
out.push(”</ul>”);
inList = false;
}
};

for (const rawLine of lines) {
const line = rawLine.trim();

if (!line) {
flushList();
continue;
}

if (line.startsWith(”# “)) {
flushList();
out.push(`<h1>${esc(line.slice(2))}</h1>`);
continue;
}

if (line.startsWith(”## “)) {
flushList();
out.push(`<h2>${esc(line.slice(3))}</h2>`);
continue;
}

if (line.startsWith(”### “)) {
flushList();
out.push(`<h3>${esc(line.slice(4))}</h3>`);
continue;
}

if (line.startsWith(”- “) || line.startsWith(”* “)) {
if (!inList) {
out.push(”<ul>”);
inList = true;
}
out.push(`<li>${esc(line.slice(2))}</li>`);
continue;
}

flushList();

const html = esc(line)
.replace(g, “<strong>$1</strong>”)
.replace(/`([^`]+)`/g, “<code>$1</code>”);

out.push(`<p>${html}</p>`);

}

flushList();

let html = out.join(””);
fenceMatches.forEach((block, index) => {
html = html.replace(`__CODE_BLOCK_${index}__`, block);
});

return `<div class="markdown-view">${html || "<p>No artifact body</p>"}</div>`;
}

function inferHref(path) {
if (!path) return “”;
if (String(path).startsWith(”/”)) return path;
return `/artifact-files/${String(path).replace(/^\/+/, "")}`;
}

function normalizeArtifactPayload(payload) {
if (!payload) return null;

const artifact = payload.artifact || payload;
if (!artifact || typeof artifact !== “object”) return null;

const path = artifact.path || “”;
const href = artifact.href || inferHref(path);

return {
title: artifact.title || payload.title || payload.task_id || “Artifact”,
body: artifact.body || artifact.content || artifact.text || “”,
href,
path,
type: artifact.type || “markdown”,
};
}

export function openArtifactModal(modal, subtitleEl, bodyEl, payload) {
if (!modal || !subtitleEl || !bodyEl) return;

const artifact = normalizeArtifactPayload(payload);
subtitleEl.textContent =
artifact?.title || payload?.title || payload?.task_id || “Artifact”;

const parts = [];

if (artifact?.href || artifact?.path || artifact?.type) {
parts.push(`<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;"> ${ artifact?.href ?`
<a
href=”${esc(artifact.href)}”
target=”_blank”
rel=“noreferrer”
class=“ghost-btn sm”
style=“display:inline-flex;align-items:center;justify-content:center;”

Open file
</a>
`: "" } ${artifact?.path ?`<div class="pill">${esc(artifact.path)}</div>`: ""} ${artifact?.type ?`<div class="pill">${esc(artifact.type)}</div>`: ""} </div>`);
}

const raw = artifact?.body ?? payload?.artifact ?? “”;

if (typeof raw === “object” && raw !== null) {
parts.push(renderJsonBlock(raw));
} else if (looksLikeJson(raw)) {
try {
const parsed = JSON.parse(raw);
parts.push(renderJsonBlock(parsed));
} catch {
parts.push(renderMarkdownish(String(raw || “”)));
}
} else {
parts.push(renderMarkdownish(String(raw || “No artifact body”)));
}

bodyEl.innerHTML = parts.join(””);
modal.classList.remove(“hidden”);
}

export function closeArtifactModal(modal) {
if (!modal) return;
modal.classList.add(“hidden”);
}