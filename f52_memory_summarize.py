async def summarize_memory_items(items: list[dict]) -> str:
  return "\n".join(f"- {item.get('title', 'untitled')}" for item in items)