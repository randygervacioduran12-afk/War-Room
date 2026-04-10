import json
import os
from typing import Any, Dict, List

from anthropic import Anthropic


def _safe_input_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("input_payload", {})
    return payload if isinstance(payload, dict) else {}


def _task_goal(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("goal") or task.get("title") or "Research the current objective.").strip()


def _task_project_key(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("project_key") or "demo-project").strip()


def _task_adapter_key(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("adapter_key") or "research_project").strip()


def _system_prompt() -> str:
    return """
You are General of Intelligence.

Your role:
- research the objective deeply
- identify important findings, gaps, and opportunities
- produce a clean research brief
- be concise, useful, and operational
- return JSON only
""".strip()


def _user_prompt(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return f"""
Research this objective and prepare a concise brief.

TASK TITLE:
{task.get("title", "Research Task")}

PROJECT KEY:
{_task_project_key(task)}

ADAPTER KEY:
{_task_adapter_key(task)}

GOAL:
{_task_goal(task)}

INPUT PAYLOAD:
{json.dumps(payload, indent=2)}

Return a JSON object with exactly these keys:
- research_brief
- key_findings
- risks
- recommended_next_steps

Rules:
- research_brief must be markdown
- key_findings must be a list of strings
- risks must be a list of strings
- recommended_next_steps must be a list of strings
""".strip()


def _fallback_result(task: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    goal = _task_goal(task)
    result = {
        "research_brief": f"""## Research Brief

### Objective
{goal}

### Initial Observations
- The request needs structured evidence gathering.
- A usable overnight output should prioritize clarity, traceability, and actionability.
- The project should balance speed with reliable handoff quality.

### Working Recommendation
Focus first on high-signal findings, key blockers, and the next concrete move.
""",
        "key_findings": [
            "Objective requires structured research and prioritization.",
            "Output should be handoff-ready and easy to review.",
            "The system benefits from concise, reusable summaries.",
        ],
        "risks": [
            "Scope drift",
            "Low-quality sources",
            "Unclear handoff formatting",
        ],
        "recommended_next_steps": [
            "Collect the strongest facts and signals first.",
            "Summarize findings into a clean operator-ready brief.",
            "Pass build-relevant details to engineering.",
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
        model=os.getenv("INTEL_CLAUDE_MODEL", os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")),
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
        raise RuntimeError("Claude returned empty research output")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = json.loads(raw.replace("```json", "").replace("```", "").strip())

    if not isinstance(parsed, dict):
        raise RuntimeError("Research output was not a JSON object")

    parsed.setdefault("research_brief", "")
    parsed.setdefault("key_findings", [])
    parsed.setdefault("risks", [])
    parsed.setdefault("recommended_next_steps", [])
    return parsed


async def run_intelligence_task(task: Dict[str, Any], context: Any = None, *args: Any, **kwargs: Any) -> Dict[str, Any]:
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