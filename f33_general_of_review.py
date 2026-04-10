import json
import os
from typing import Any, Dict, List

from anthropic import Anthropic


def _safe_input_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    payload = task.get("input_payload", {})
    return payload if isinstance(payload, dict) else {}


def _task_goal(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return str(payload.get("goal") or task.get("title") or "Review the output quality and risks.").strip()


def _system_prompt() -> str:
    return """
You are General of Review.

Your role:
- evaluate output quality
- identify risks, weaknesses, and missing pieces
- produce a usable review note
- return JSON only
""".strip()


def _user_prompt(task: Dict[str, Any]) -> str:
    payload = _safe_input_payload(task)
    return f"""
Review this work and produce a concise quality/risk note.

TASK TITLE:
{task.get("title", "Review Task")}

GOAL:
{_task_goal(task)}

INPUT PAYLOAD:
{json.dumps(payload, indent=2)}

Return a JSON object with exactly these keys:
- review_notes
- strengths
- weaknesses
- recommended_fixes

Rules:
- review_notes must be markdown
- strengths must be a list of strings
- weaknesses must be a list of strings
- recommended_fixes must be a list of strings
""".strip()


def _fallback_result(task: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    result = {
        "review_notes": """## Review Notes

### Overall
The output is directionally useful but should be checked for clarity, completeness, and implementation readiness.

### Focus Areas
- confirm scope
- remove ambiguity
- ensure handoff usability
""",
        "strengths": [
            "Structured approach",
            "Good handoff potential",
            "Action-oriented direction",
        ],
        "weaknesses": [
            "May still need tighter scope",
            "Could use more concrete implementation detail",
        ],
        "recommended_fixes": [
            "Tighten the next action list.",
            "Make file/module targets explicit.",
            "Remove repeated or vague language.",
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
        model=os.getenv("REVIEW_CLAUDE_MODEL", os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")),
        max_tokens=1600,
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
        raise RuntimeError("Claude returned empty review output")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = json.loads(raw.replace("```json", "").replace("```", "").strip())

    if not isinstance(parsed, dict):
        raise RuntimeError("Review output was not a JSON object")

    parsed.setdefault("review_notes", "")
    parsed.setdefault("strengths", [])
    parsed.setdefault("weaknesses", [])
    parsed.setdefault("recommended_fixes", [])
    return parsed


async def run_review_task(task: Dict[str, Any], context: Any = None, *args: Any, **kwargs: Any) -> Dict[str, Any]:
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