from __future__ import annotations

from typing import Any

import httpx
from anthropic import AsyncAnthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from f20_core_config import get_settings
from f21_core_logging import get_logger
from f25_core_types import LLMProvider

logger = get_logger("llm")

AGENT_PROVIDER_MAP: dict[str, str] = {
    "general_of_the_army": LLMProvider.ANTHROPIC.value,
    "general_of_intelligence": LLMProvider.GEMINI.value,
    "general_of_engineering": LLMProvider.OPENAI.value,
    "general_of_review": LLMProvider.ANTHROPIC.value,
    "general_of_the_archive": LLMProvider.GEMINI.value,
}


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.anthropic_client = (
            AsyncAnthropic(api_key=self.settings.anthropic_api_key)
            if self.settings.anthropic_api_key
            else None
        )
        self.http = httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds)

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.anthropic_api_key
            or self.settings.openai_api_key
            or self.settings.gemini_api_key
        )

    def provider_for_agent(self, agent_name: str | None) -> str:
        if not agent_name:
            return LLMProvider.ANTHROPIC.value
        return AGENT_PROVIDER_MAP.get(agent_name, LLMProvider.ANTHROPIC.value)

    async def close(self) -> None:
        await self.http.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def complete_text(
        self,
        *,
        system: str,
        user_text: str,
        agent_name: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        chosen_provider = provider or self.provider_for_agent(agent_name)

        if chosen_provider == LLMProvider.ANTHROPIC.value:
            return await self._complete_anthropic(
                system=system,
                user_text=user_text,
                model=model or self.settings.anthropic_model_main,
                max_tokens=max_tokens or self.settings.anthropic_max_tokens,
                temperature=self.settings.anthropic_temperature if temperature is None else temperature,
            )

        if chosen_provider == LLMProvider.OPENAI.value:
            return await self._complete_openai(
                system=system,
                user_text=user_text,
                model=model or self.settings.openai_model_main,
                max_output_tokens=max_tokens or self.settings.openai_max_output_tokens,
                temperature=self.settings.openai_temperature if temperature is None else temperature,
            )

        if chosen_provider == LLMProvider.GEMINI.value:
            return await self._complete_gemini(
                system=system,
                user_text=user_text,
                model=model or self.settings.gemini_model_main,
                max_output_tokens=max_tokens or self.settings.gemini_max_output_tokens,
                temperature=self.settings.gemini_temperature if temperature is None else temperature,
            )

        raise RuntimeError(f"Unsupported provider={chosen_provider}")

    async def _complete_anthropic(
        self,
        *,
        system: str,
        user_text: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        if not self.anthropic_client:
            raise RuntimeError("Anthropic not configured. Missing ANTHROPIC_API_KEY.")

        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user_text}],
        )

        parts: list[str] = []
        for block in response.content:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)

        final_text = "\n".join(parts).strip()
        logger.info("llm_complete_text", provider="anthropic", model=model, chars=len(final_text))
        return final_text

    async def _complete_openai(
        self,
        *,
        system: str,
        user_text: str,
        model: str,
        max_output_tokens: int,
        temperature: float,
    ) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OpenAI not configured. Missing OPENAI_API_KEY.")

        payload = {
            "model": model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_text},
            ],
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }

        response = await self.http.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        text = self._extract_openai_text(data).strip()
        logger.info("llm_complete_text", provider="openai", model=model, chars=len(text))
        return text

    async def _complete_gemini(
        self,
        *,
        system: str,
        user_text: str,
        model: str,
        max_output_tokens: int,
        temperature: float,
    ) -> str:
        if not self.settings.gemini_api_key:
            raise RuntimeError("Gemini not configured. Missing GEMINI_API_KEY.")

        payload = {
            "system_instruction": {
                "parts": [{"text": system}],
            },
            "contents": [
                {
                    "parts": [{"text": user_text}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        response = await self.http.post(
            url,
            headers={
                "x-goog-api-key": self.settings.gemini_api_key,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        text = self._extract_gemini_text(data).strip()
        logger.info("llm_complete_text", provider="gemini", model=model, chars=len(text))
        return text

    def _extract_openai_text(self, data: dict[str, Any]) -> str:
        direct = data.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct

        parts: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    parts.append(text)

        if parts:
            return "\n".join(parts)

        return str(data)

    def _extract_gemini_text(self, data: dict[str, Any]) -> str:
        candidates = data.get("candidates", [])
        parts: list[str] = []

        for candidate in candidates:
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = part.get("text")
                if text:
                    parts.append(text)

        if parts:
            return "\n".join(parts)

        return str(data)

    async def provider_health(self) -> dict[str, bool]:
        return {
            "anthropic": bool(self.settings.anthropic_api_key),
            "openai": bool(self.settings.openai_api_key),
            "gemini": bool(self.settings.gemini_api_key),
        }

    async def healthcheck(self) -> bool:
        providers = await self.provider_health()
        return any(providers.values())