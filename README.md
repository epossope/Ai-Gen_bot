# AI Studio Demo (Public GitHub Version)

This is a safe demo version of the Telegram bot + Mini App.
It is designed for public GitHub publishing and client showcase.

## What is included
- Demo Telegram bot flows:
  - Start menu
  - Demo generation by prompt
  - Demo stylization shortcuts
  - Open Mini App button
- Demo Mini App:
  - Sections: Generation, Editing, Stylization
  - Profile and history
  - Fake generation result image
- Backend API with in-memory demo storage

## What is intentionally removed
- Real AI provider integrations (Replicate/OpenRouter/etc.)
- Real payments (Stars/YooKassa/CryptoCloud)
- Admin production tools
- Database and production logs pipeline
- Any secret keys, tokens, private IDs

## Quick start
1. Create virtual env and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Copy env template:
   ```bash
   copy .env.example .env
   ```
3. Set at least:
   - `TELEGRAM_BOT_TOKEN` (optional if you only want Mini App/API)
   - `APP_BASE_URL`
   - `WEBAPP_URL`
4. Run:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

Open:
- API health: `http://localhost:8000/health`
- Mini App: `http://localhost:8000/webapp`

## Notes for clients
- This repository is a showcase/demo only.
- All billing and external provider actions are mocked.
- Generation output is a synthetic SVG placeholder.
