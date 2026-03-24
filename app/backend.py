from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .demo_data import get_history, profile_payload, run_generation, schema_payload, svg_for_generation


class ProfileRequest(BaseModel):
    tg_user_id: int = Field(default=1, ge=1)
    username: str | None = None


class HistoryRequest(BaseModel):
    tg_user_id: int = Field(default=1, ge=1)


class GenerateRequest(BaseModel):
    tg_user_id: int = Field(default=1, ge=1)
    username: str | None = None
    mode: str = Field(default="generate")
    model_id: str
    prompt: str = Field(default="")


def create_app() -> FastAPI:
    app = FastAPI(title="AI Studio Demo API", version="1.0.0-demo")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    webapp_dir = Path(__file__).resolve().parents[1] / "webapp"
    app.mount("/webapp", StaticFiles(directory=str(webapp_dir), html=True), name="webapp")

    @app.get("/")
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/webapp")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"ok": True, "demo": True}

    @app.get("/schema")
    async def schema() -> dict[str, Any]:
        return schema_payload()

    @app.post("/miniapp/profile")
    async def miniapp_profile(payload: ProfileRequest) -> dict[str, Any]:
        return profile_payload(payload.tg_user_id, payload.username)

    @app.post("/miniapp/history")
    async def miniapp_history(payload: HistoryRequest) -> dict[str, Any]:
        return {"items": get_history(payload.tg_user_id), "demo": True}

    @app.post("/miniapp/generate")
    async def miniapp_generate(payload: GenerateRequest) -> dict[str, Any]:
        try:
            result = run_generation(
                user_id=payload.tg_user_id,
                mode=payload.mode,
                model_id=payload.model_id,
                prompt=payload.prompt,
                username=payload.username,
            )
            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=402, detail=str(exc)) from exc

    @app.get("/demo/image/{generation_id}")
    async def demo_image(generation_id: str) -> Response:
        svg = svg_for_generation(generation_id)
        return Response(content=svg, media_type="image/svg+xml")

    return app
