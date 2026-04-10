import json
import os
from typing import Any, Dict, List

from anthropic import Anthropic


def _safe_input_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("input_payload", {})
    return payload if isinstance(payload, dict) else {}


def _task_goal(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("goal") or task.get("title") or "Prepare an engineering execution approach.").strip()


def _task_project_key(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("project_key") or "demo-project").strip()


def _task_adapter_key(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("adapter_key") or "research_project").strip()


def _system_prompt() -> str:
    return """
You are General of Engineering.

Your role:
- turn the objective into a build-ready engineering plan
- suggest concrete files, modules, interfaces, and implementation steps
- make the output practical for a workbench/operator
- return JSON only
""".strip()


def _user_prompt(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return f"""
Prepare a draft engineering execution approach.

TASK TITLE:
{task.get("title", "Engineering Task")}

PROJECT KEY:
{_task_project_key(task)}

ADAPTER KEY:
{_task_adapter_key(task)}

GOAL:
{_task_goal(task)}

INPUT PAYLOAD:
{json.dumps(payload, indent=2)}

Return a JSON object with exactly these keys:
- engineering_plan
- target_files
- implementation_steps
- workbench_actions

Rules:
- engineering_plan must be markdown
- target_files must be a list of strings
- implementation_steps must be a list of strings
- workbench_actions must be a list of strings
""".strip()


def _fallback_result(task: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    goal = _task_goal(task)
    result = {
        "engineering_plan": f"""## Engineering Plan

### Objective
{goal}

### Build Direction
- Convert the objective into concrete files and interface updates.
- Keep changes modular and easy to test in Replit.
- Prefer simple, recoverable workbench actions over risky one-shot edits.
""",
        "target_files": [
            "frontend/src/App.jsx",
            "f16_api_ui.py",
            "f17_api_workbench.py",
        ],
        "implementation_steps": [
            "Identify the smallest working file changes.",
            "Create or update the required UI/API pieces.",
            "Compile and validate the changed modules.",
        ],
        "workbench_actions": [
            "Open the target file.",
            "Patch one section at a time.",
            "Compile after each major change.",
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
        model=os.getenv("ENGINEER_CLAUDE_MODEL", os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")),
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
        raise RuntimeError("Claude returned empty engineering output")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = json.loads(raw.replace("```json", "").replace("```", "").strip())

    if not isinstance(parsed, dict):
        raise RuntimeError("Engineering output was not a JSON object")

    parsed.setdefault("engineering_plan", "")
    parsed.setdefault("target_files", [])
    parsed.setdefault("implementation_steps", [])
    parsed.setdefault("workbench_actions", [])
    return parsed


async def run_engineering_task(task: Dict[str, Any], context: Any = None, *args: Any, **kwargs: Any) -> Dict[str, Any]:
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