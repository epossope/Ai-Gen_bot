from __future__ import annotations

import html
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import settings


MODEL_CARDS: list[dict[str, Any]] = [
    {
        "id": "flux_2_pro",
        "title": "Flux 2 Pro",
        "mode": "generate",
        "section": "generation",
        "price": 10,
        "description": "Photorealistic generation demo model.",
    },
    {
        "id": "sdxl",
        "title": "SDXL",
        "mode": "generate",
        "section": "generation",
        "price": 5,
        "description": "Universal art and concept generation model.",
    },
    {
        "id": "nano_banana_2_edit",
        "title": "Nano Banana 2 Edit",
        "mode": "edit",
        "section": "editing",
        "price": 8,
        "description": "Editing demo model with prompt guidance.",
    },
    {
        "id": "stylize_cyberpunk",
        "title": "Cyberpunk",
        "mode": "stylize",
        "section": "stylization",
        "price": 12,
        "description": "Template-based stylization preset.",
    },
    {
        "id": "stylize_anime",
        "title": "Anime",
        "mode": "stylize",
        "section": "stylization",
        "price": 12,
        "description": "Template-based stylization preset.",
    },
]

SECTIONS: list[dict[str, str]] = [
    {"id": "generation", "title": "Generation"},
    {"id": "editing", "title": "Editing"},
    {"id": "stylization", "title": "Stylization"},
]


@dataclass
class DemoUser:
    tokens: int
    username: str | None = None


_lock = threading.Lock()
_users: dict[int, DemoUser] = {}
_history: dict[int, list[dict[str, Any]]] = {}
_svg_payloads: dict[str, dict[str, str]] = {}


def _model_by_id(model_id: str) -> dict[str, Any] | None:
    for card in MODEL_CARDS:
        if card["id"] == model_id:
            return card
    return None


def _user_default_tokens(user_id: int) -> int:
    if user_id in settings.admin_ids:
        return settings.admin_tokens
    return settings.initial_tokens


def get_or_create_user(user_id: int, username: str | None = None) -> DemoUser:
    with _lock:
        user = _users.get(user_id)
        if user is None:
            user = DemoUser(tokens=_user_default_tokens(user_id), username=username)
            _users[user_id] = user
        elif user_id in settings.admin_ids and user.tokens < settings.admin_tokens:
            user.tokens = settings.admin_tokens
        if username:
            user.username = username
        return user


def get_history(user_id: int) -> list[dict[str, Any]]:
    with _lock:
        return list(_history.get(user_id, []))


def schema_payload() -> dict[str, Any]:
    return {
        "demo": True,
        "sections": SECTIONS,
        "modelCards": MODEL_CARDS,
    }


def profile_payload(user_id: int, username: str | None = None) -> dict[str, Any]:
    user = get_or_create_user(user_id, username=username)
    return {
        "demo": True,
        "telegramId": user_id,
        "username": user.username,
        "balance": user.tokens,
        "referralBonus": 12,
        "currencyNote": "1 token = demo unit",
    }


def run_generation(
    user_id: int,
    mode: str,
    model_id: str,
    prompt: str,
    username: str | None = None,
) -> dict[str, Any]:
    model = _model_by_id(model_id)
    if model is None:
        raise ValueError(f"Unknown model_id: {model_id}")

    user = get_or_create_user(user_id, username=username)
    price = int(model["price"])
    if user.tokens < price:
        raise RuntimeError("Not enough tokens in demo balance.")

    generation_id = uuid.uuid4().hex[:12]
    prompt_view = (prompt or "Demo prompt").strip()[:120]
    if not prompt_view:
        prompt_view = "Demo prompt"

    with _lock:
        user.tokens -= price
        _svg_payloads[generation_id] = {
            "model_title": str(model["title"]),
            "prompt": prompt_view,
            "mode": mode,
        }
        _history.setdefault(user_id, []).insert(
            0,
            {
                "id": generation_id,
                "modelId": model_id,
                "modelTitle": model["title"],
                "mode": mode,
                "prompt": prompt_view,
                "price": price,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "imageUrl": f"/demo/image/{generation_id}",
            },
        )

    return {
        "generationId": generation_id,
        "mode": mode,
        "modelId": model_id,
        "modelTitle": model["title"],
        "prompt": prompt_view,
        "price": price,
        "imageUrl": f"/demo/image/{generation_id}",
        "balance": user.tokens,
        "demo": True,
    }


def svg_for_generation(generation_id: str) -> str:
    payload = _svg_payloads.get(generation_id)
    if payload is None:
        payload = {
            "model_title": "Unknown",
            "prompt": "No data",
            "mode": "demo",
        }
    model_title = html.escape(payload["model_title"])
    prompt = html.escape(payload["prompt"])
    mode = html.escape(payload["mode"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1f1140"/>
      <stop offset="100%" stop-color="#0e2338"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <rect x="56" y="56" width="912" height="912" rx="28" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.15)"/>
  <text x="88" y="140" fill="#d8ff5d" font-size="38" font-family="Arial, sans-serif">AI Studio Public Demo</text>
  <text x="88" y="200" fill="#ffffff" font-size="30" font-family="Arial, sans-serif">Model: {model_title}</text>
  <text x="88" y="248" fill="#ffffff" font-size="26" font-family="Arial, sans-serif">Mode: {mode}</text>
  <text x="88" y="320" fill="#ffffff" font-size="24" font-family="Arial, sans-serif">Prompt:</text>
  <foreignObject x="88" y="340" width="848" height="300">
    <div xmlns="http://www.w3.org/1999/xhtml"
         style="color:#d7d9e0;font-size:24px;line-height:1.35;font-family:Arial,sans-serif;">
      {prompt}
    </div>
  </foreignObject>
  <text x="88" y="900" fill="#9da3b8" font-size="20" font-family="Arial, sans-serif">Generated at {now}</text>
  <text x="88" y="936" fill="#9da3b8" font-size="20" font-family="Arial, sans-serif">This is a synthetic demo image.</text>
</svg>"""
