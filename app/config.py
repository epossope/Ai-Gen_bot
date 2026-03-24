from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    admin_ids_raw: str = os.getenv("ADMIN_IDS", "").strip()
    app_base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8000").strip()
    webapp_url: str = os.getenv("WEBAPP_URL", "http://localhost:8000/webapp").strip()
    start_bot_in_api: bool = _as_bool(os.getenv("START_BOT_IN_API", "true"), True)
    initial_tokens: int = int(os.getenv("INITIAL_TOKENS", "50"))
    admin_tokens: int = int(os.getenv("ADMIN_TOKENS", "500"))

    @property
    def admin_ids(self) -> set[int]:
        out: set[int] = set()
        for chunk in self.admin_ids_raw.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                out.add(int(chunk))
            except ValueError:
                continue
        return out


settings = Settings()
