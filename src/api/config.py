"""Server-side configuration for the portfolio demo API."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_MAX_PROMPT_LENGTH = 4_000


@dataclass(frozen=True)
class DemoAPIConfig:
    """Non-sensitive settings used by the API transport layer."""

    live_enabled: bool = False
    cors_origins: tuple[str, ...] = ()
    max_prompt_length: int = DEFAULT_MAX_PROMPT_LENGTH

    @classmethod
    def from_environment(cls):
        """Load public server behavior without exposing environment values."""
        load_dotenv(ENV_FILE)
        return cls(
            live_enabled=_environment_flag("DEMO_LIVE_ENABLED", default=False),
            cors_origins=_environment_origins("DEMO_CORS_ORIGINS"),
        )


def _environment_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError("{} must be a boolean value.".format(name))


def _environment_origins(name: str) -> tuple[str, ...]:
    value = os.getenv(name, "")
    return tuple(origin.strip() for origin in value.split(",") if origin.strip())
