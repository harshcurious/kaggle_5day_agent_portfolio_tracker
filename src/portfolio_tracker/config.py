"""Runtime configuration for portfolio tracker tools."""

from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    earningscall_api_key: str | None = None
    google_api_key: str | None = None
    sec_user_agent: str | None = None


def load_settings(*, load_env_file: bool = True) -> Settings:
    if load_env_file:
        load_dotenv()
    return Settings(
        earningscall_api_key=_empty_to_none(os.getenv("EARNINGSCALL_API_KEY")),
        google_api_key=_empty_to_none(os.getenv("GOOGLE_API_KEY")),
        sec_user_agent=_empty_to_none(os.getenv("SEC_USER_AGENT")),
    )


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
