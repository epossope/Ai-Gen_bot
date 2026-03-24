from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .backend import create_app
from .bot import start_bot_polling_task
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task: asyncio.Task[None] | None = None
    if settings.start_bot_in_api and settings.telegram_bot_token:
        bot_task = await start_bot_polling_task()
    try:
        yield
    finally:
        if bot_task:
            bot_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await bot_task


app = create_app()
app.router.lifespan_context = lifespan
