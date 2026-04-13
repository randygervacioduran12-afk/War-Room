export function normalizeWorkbenchPayload(payload) {
if (Array.isArray(payload)) return payload;
if (Array.isArray(payload?.files)) return payload.files;
if (Array.isArray(payload?.items)) return payload.items;
if (Array.isArray(payload?.rows)) return payload.rows;
return [];
}