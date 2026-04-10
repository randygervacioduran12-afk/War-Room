import json
import os
from typing import Any, Dict, List

from anthropic import Anthropic


def _safe_input_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("input_payload", {})
    return payload if isinstance(payload, dict) else {}


def _task_goal(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("goal") or task.get("title") or "Create an execution plan.").strip()


def _task_project_key(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("project_key") or "demo-project").strip()


def _task_adapter_key(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("adapter_key") or "research_project").strip()


def _system_prompt() -> str:
    return """
You are General of the Army.

Your role:
- turn the operator objective into a structured execution plan
- produce a practical overnight mission plan
- clearly define outputs, risks, and handoff steps
- return JSON only
""".strip()


def _user_prompt(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return f"""
Prepare an execution plan for this task.

TASK TITLE:
{task.get("title", "Initial planning")}

PROJECT KEY:
{_task_project_key(task)}

ADAPTER KEY:
{_task_adapter_key(task)}

GOAL:
{_task_goal(task)}

INPUT PAYLOAD:
{json.dumps(payload, indent=2)}

Return a JSON object with exactly these keys:
- objective
- project_key
- adapter_key
- plan_summary
- spawned_tasks

Rules:
- objective must be a string
- project_key must be a string
- adapter_key must be a string
- plan_summary must be markdown
- spawned_tasks must be a list of strings chosen from:
  ["research", "engineer", "review", "archive"]
""".strip()


def _fallback_result(task: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    result = {
        "objective": _task_goal(task),
        "project_key": _task_project_key(task),
        "adapter_key": _task_adapter_key(task),
        "plan_summary": f"""# Overnight Execution Plan

## Objective
{_task_goal(task)}

## Command Intent
Create a clear overnight plan that moves from research to engineering, then review, then archival capture.

## Tasks
1. Research the goal and surface the strongest findings.
2. Draft an engineering execution approach.
3. Review risks and output quality.
4. Archive the useful learnings for future runs.

## Outputs
- research brief
- engineering plan
- review notes
- archive summary
""",
        "spawned_tasks": ["research", "engineer", "review", "archive"],
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
        model=os.getenv("ARMY_CLAUDE_MODEL", os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")),
        max_tokens=1800,
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
        raise RuntimeError("Claude returned empty army output")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = json.loads(raw.replace("```json", "").replace("```", "").strip())

    if not isinstance(parsed, dict):
        raise RuntimeError("Army output was not a JSON object")

    parsed.setdefault("objective", _task_goal(task))
    parsed.setdefault("project_key", _task_project_key(task))
    parsed.setdefault("adapter_key", _task_adapter_key(task))
    parsed.setdefault("plan_summary", "")
    parsed.setdefault("spawned_tasks", ["research", "engineer", "review", "archive"])
    return parsed


async def run_army_task(task: Dict[str, Any], context: Any = None, *args: Any, **kwargs: Any) -> Dict[str, Any]:
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