from __future__ import annotations

import asyncio
import contextlib

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from .config import settings
from .demo_data import run_generation

router = Router()


class DemoStates(StatesGroup):
    waiting_prompt = State()


def _main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Generate demo", callback_data="demo_generate")],
            [InlineKeyboardButton(text="Stylization demo", callback_data="demo_stylize")],
            [InlineKeyboardButton(text="Open Mini App", web_app=WebAppInfo(url=settings.webapp_url))],
        ]
    )


def _stylization_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Cyberpunk", callback_data="style:stylize_cyberpunk")],
            [InlineKeyboardButton(text="Anime", callback_data="style:stylize_anime")],
            [InlineKeyboardButton(text="Back", callback_data="menu_back")],
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "AI Studio Demo\n\n"
        "This public bot version shows basic user flow without production integrations.",
        reply_markup=_main_menu_kb(),
    )


@router.callback_query(F.data == "menu_back")
async def menu_back(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            "AI Studio Demo\n\nChoose an action:",
            reply_markup=_main_menu_kb(),
        )


@router.callback_query(F.data == "demo_generate")
async def menu_generate(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(DemoStates.waiting_prompt)
    if callback.message:
        await callback.message.edit_text(
            "Send a text prompt for demo generation.\n\nExample: neon city at night",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Back", callback_data="menu_back")]]
            ),
        )


@router.message(DemoStates.waiting_prompt)
async def handle_prompt(message: Message, state: FSMContext) -> None:
    prompt = (message.text or "").strip()
    if not prompt:
        await message.answer("Prompt is empty. Try one more time.")
        return
    user = message.from_user
    user_id = int(user.id) if user else 1
    username = user.username if user else None
    try:
        result = run_generation(
            user_id=user_id,
            mode="generate",
            model_id="flux_2_pro",
            prompt=prompt,
            username=username,
        )
    except RuntimeError as exc:
        await message.answer(f"Demo balance issue: {exc}")
        await state.clear()
        return

    image_url = f"{settings.app_base_url}{result['imageUrl']}"
    await message.answer_photo(
        image_url,
        caption=(
            f"Demo result\n"
            f"Model: {result['modelTitle']}\n"
            f"Prompt: {result['prompt']}\n"
            f"Spent: {result['price']} tokens\n"
            f"Balance: {result['balance']} tokens"
        ),
    )
    await state.clear()
    await message.answer("Continue:", reply_markup=_main_menu_kb())


@router.callback_query(F.data == "demo_stylize")
async def menu_stylize(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text("Choose a style preset:", reply_markup=_stylization_kb())


@router.callback_query(F.data.startswith("style:"))
async def apply_style(callback: CallbackQuery) -> None:
    await callback.answer()
    style_model_id = callback.data.split(":", 1)[1]
    user = callback.from_user
    user_id = int(user.id) if user else 1
    username = user.username if user else None

    try:
        result = run_generation(
            user_id=user_id,
            mode="stylize",
            model_id=style_model_id,
            prompt="Template-based style demo",
            username=username,
        )
    except RuntimeError as exc:
        if callback.message:
            await callback.message.answer(f"Demo balance issue: {exc}")
        return

    image_url = f"{settings.app_base_url}{result['imageUrl']}"
    if callback.message:
        await callback.message.answer_photo(
            image_url,
            caption=(
                f"Stylization demo done\n"
                f"Style: {result['modelTitle']}\n"
                f"Spent: {result['price']} tokens\n"
                f"Balance: {result['balance']} tokens"
            ),
        )
        await callback.message.answer("Continue:", reply_markup=_main_menu_kb())


async def start_bot_polling() -> None:
    if not settings.telegram_bot_token:
        return
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    try:
        await dp.start_polling(bot)
    finally:
        with contextlib.suppress(Exception):
            await bot.session.close()


async def start_bot_polling_task() -> asyncio.Task[None] | None:
    if not settings.telegram_bot_token:
        return None
    return asyncio.create_task(start_bot_polling(), name="demo-bot-polling")
