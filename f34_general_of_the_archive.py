import json
import os
from typing import Any, Dict, List

from anthropic import Anthropic


def _safe_input_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("input_payload", {})
    return payload if isinstance(payload, dict) else {}


def _task_goal(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("goal") or task.get("title") or "Archive key learnings and reusable notes.").strip()


def _system_prompt() -> str:
    return """
You are General of the Archive.

Your role:
- preserve reusable knowledge
- write concise archival summaries
- capture durable insights for future runs
- return JSON only
""".strip()


def _user_prompt(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return f"""
Archive the important learnings from this task.

TASK TITLE:
{task.get("title", "Archive Task")}

GOAL:
{_task_goal(task)}

INPUT PAYLOAD:
{json.dumps(payload, indent=2)}

Return a JSON object with exactly these keys:
- archive_summary
- saved_learnings
- reusable_patterns

Rules:
- archive_summary must be markdown
- saved_learnings must be a list of strings
- reusable_patterns must be a list of strings
""".strip()


def _fallback_result(task: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    result = {
        "archive_summary": """## Archive Summary

This run produced reusable planning and execution patterns that should be preserved for future operator workflows.
""",
        "saved_learnings": [
            "Keep outputs concise and handoff-ready.",
            "Prefer modular steps over one-shot complexity.",
            "Preserve risks and next moves with the summary.",
        ],
        "reusable_patterns": [
            "plan → research → engineer → review → archive",
            "workbench-first engineering",
            "operator-readable summaries",
        ],
    }
    if reason:
        result["fallback_reason"] = reason
    return result


def _call_claude(task: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY / CLAUDE_API_KEY")

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=os.getenv("ARCHIVE_CLAUDE_MODEL", os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")),
        max_tokens=1400,
        temperature=0.2,
        system=_system_prompt(),
        messages=[{"role": "user", "content": _user_prompt(task)}],
    )

    text_parts: List[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            text_parts.append(block.text)

    raw = "\n".join(text_parts).strip()
    if not raw:
        raise RuntimeError("Claude returned empty archive output")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = json.loads(raw.replace("```json", "").replace("```", "").strip())

    if not isinstance(parsed, dict):
        raise RuntimeError("Archive output was not a JSON object")

    parsed.setdefault("archive_summary", "")
    parsed.setdefault("saved_learnings", [])
    parsed.setdefault("reusable_patterns", [])
    return parsed


async def run_archive_task(task: Dict[str, Any], context: Any = None, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    try:
        result = _call_claude(task)
        if context is not None:
            result["context_seen"] = True
        return result
    except Exception as exc:
        fallback = _fallback_result(task, str(exc))
        if context is not None:
            fallback["context_seen"] = True
        return fallback