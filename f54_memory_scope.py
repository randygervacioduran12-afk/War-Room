from f25_core_types import MemoryScope


def build_memory_scope_list(run_id: str | None, project_key: str) -> list[tuple[str, str | None]]:
    scopes: list[tuple[str, str | None]] = [
        (MemoryScope.PROJECT.value, None),
        (MemoryScope.GLOBAL.value, None),
    ]
    if run_id:
        scopes.insert(0, (MemoryScope.RUN.value, run_id))
    return scopes