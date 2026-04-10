import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProviderConfig:
    enabled: bool = False
    api_key: Optional[str] = None
    model: Optional[str] = None


@dataclass
class Settings:
    app_name: str = "War Room Universal Adapter"
    app_env: str = "dev"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: Optional[str] = None

    anthropic: ProviderConfig = field(default_factory=ProviderConfig)
    openai: ProviderConfig = field(default_factory=ProviderConfig)
    gemini: ProviderConfig = field(default_factory=ProviderConfig)

    providers: Dict[str, ProviderConfig] = field(default_factory=dict)

    @property
    def claude(self) -> ProviderConfig:
        return self.anthropic

    def provider(self, name: str) -> ProviderConfig:
        return self.providers.get(name, ProviderConfig())


_cached_settings: Optional[Settings] = None


def _bool_from_env(value: Optional[str], fallback: bool) -> bool:
    if value is None:
        return fallback
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_from_env(value: Optional[str], fallback: int) -> int:
    if value is None or not str(value).strip():
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback


def get_settings() -> Settings:
    global _cached_settings

    if _cached_settings is not None:
        return _cached_settings

    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    anthropic_cfg = ProviderConfig(
        enabled=_bool_from_env(os.getenv("ANTHROPIC_ENABLED"), bool(anthropic_key)),
        api_key=anthropic_key,
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
    )

    openai_cfg = ProviderConfig(
        enabled=_bool_from_env(os.getenv("OPENAI_ENABLED"), bool(openai_key)),
        api_key=openai_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )

    gemini_cfg = ProviderConfig(
        enabled=_bool_from_env(os.getenv("GEMINI_ENABLED"), bool(gemini_key)),
        api_key=gemini_key,
        model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    )

    _cached_settings = Settings(
        app_name=os.getenv("APP_NAME", "War Room Universal Adapter"),
        app_env=os.getenv("APP_ENV", "dev"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=_int_from_env(os.getenv("APP_PORT"), 8000),
        database_url=os.getenv("DATABASE_URL"),
        anthropic=anthropic_cfg,
        openai=openai_cfg,
        gemini=gemini_cfg,
        providers={
            "anthropic": anthropic_cfg,
            "claude": anthropic_cfg,
            "openai": openai_cfg,
            "gemini": gemini_cfg,
        },
    )

    return _cached_settings