import json
import os
import urllib.error
import urllib.request
from typing import Any


def _safe_json_loads(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return value


def _task_payload(task: dict[str, Any]) -> dict[str, Any]:
    payload = _safe_json_loads(task.get("payload_json"))
    if isinstance(payload, dict):
        return payload
    return {}


def _system_prompt(general_key: str) -> str:
    systems = {
        "general_of_the_army": (
            "You are General of the Army, the strategic orchestrator. "
            "Convert the operator's request into a practical execution plan with priorities, next actions, dependencies, and handoff notes."
        ),
        "general_of_intelligence": (
            "You are General of Intelligence, focused on research and discovery. "
            "Return findings, assumptions, unknowns, risks, and recommended follow-up research."
        ),
        "general_of_engineering": (
            "You are General of Engineering, focused on build output. "
            "Return implementation-ready work: architecture, file plan, code strategy, concrete next steps, and artifact-ready output."
        ),
        "general_of_review": (
            "You are General of Review, focused on critique and validation. "
            "Assess quality, risks, gaps, contradictions, and recommend corrections."
        ),
        "general_of_the_archive": (
            "You are General of the Archive, focused on memory and summaries. "
            "Compress the important information into a durable summary, preserving decisions, outcomes, risks, and next steps."
        ),
    }
    return systems.get(
        general_key,
        "You are a precise execution assistant. Produce a useful, structured result."
    )


def _user_prompt(task: dict[str, Any]) -> str:
    payload = _task_payload(task)
    operator_message = task.get("operator_message") or payload.get("operator_message") or ""
    return f"""
TASK CONTEXT
task_id: {task.get("task_id")}
run_id: {task.get("run_id")}
project_key: {task.get("project_key")}
general_key: {task.get("general_key")}
task_type: {task.get("task_type")}
title: {task.get("title")}

OPERATOR MESSAGE
{operator_message}

PAYLOAD JSON
{json.dumps(payload, indent=2, ensure_ascii=False)}

Return a structured response in markdown with these sections:
1. Objective
2. Assessment
3. Deliverable
4. Risks
5. Next actions

Be concrete and execution-ready.
""".strip()


def _call_anthropic(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    body = {
        "model": model,
        "max_tokens": 1800,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
    }

    req = urllib.request.Request(
        url="https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Anthropic HTTP {e.code}: {detail}") from e

    parts = data.get("content") or []
    text_blocks: list[str] = []
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "text":
            text_blocks.append(part.get("text", ""))

    text = "\n\n".join(block for block in text_blocks if block).strip()
    if not text:
        raise RuntimeError("Anthropic returned no text")

    return {
        "provider": "anthropic",
        "model": model,
        "text": text,
        "raw": data,
    }


def _call_gemini(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    combined = f"{system_prompt}\n\n{user_prompt}"
    body = {
        "contents": [
            {
                "parts": [
                    {"text": combined}
                ]
            }
        ]
    }

    req = urllib.request.Request(
        url=url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini HTTP {e.code}: {detail}") from e

    candidates = data.get("candidates") or []
    text_parts: list[str] = []

    for cand in candidates:
        content = cand.get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            if "text" in part:
                text_parts.append(part["text"])

    text = "\n\n".join(block for block in text_parts if block).strip()
    if not text:
        raise RuntimeError("Gemini returned no text")

    return {
        "provider": "gemini",
        "model": model,
        "text": text,
        "raw": data,
    }


def run_general_task(task: dict[str, Any]) -> dict[str, Any]:
    general_key = task.get("general_key") or "general_of_the_army"
    system_prompt = _system_prompt(general_key)
    user_prompt = _user_prompt(task)

    provider_result: dict[str, Any]
    if os.getenv("ANTHROPIC_API_KEY"):
        provider_result = _call_anthropic(system_prompt, user_prompt)
    elif os.getenv("GEMINI_API_KEY"):
        provider_result = _call_gemini(system_prompt, user_prompt)
    else:
        raise RuntimeError("No model provider configured. Add ANTHROPIC_API_KEY or GEMINI_API_KEY.")

    text = provider_result["text"]

    return {
        "ok": True,
        "general_key": general_key,
        "provider": provider_result["provider"],
        "model": provider_result["model"],
        "summary": text[:600],
        "artifact": {
            "type": "markdown",
            "title": task.get("title") or f"{general_key} output",
            "content": text,
        },
        "raw_text": text,
    }


# Compatibility alias
def route_task(task: dict[str, Any]) -> dict[str, Any]:
    return run_general_task(task)