from f51_memory_retrieve import get_relevant_memory


async def build_context_pack(project_key: str, run_id: str | None = None) -> dict:
    items = await get_relevant_memory(project_key=project_key, run_id=run_id, limit=20)
    return {"count": len(items), "items": items}