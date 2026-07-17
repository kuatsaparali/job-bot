# 🔍 Job Bot KZ — Telegram Job Search Bot

A Telegram bot that helps you quickly find jobs in Kazakhstan: pick a city, select one or more professions you're interested in, and the bot streams matching listings straight into the chat as it finds them.

## ✨ Features

- 🏙 **City selection** — Almaty, Astana, Shymkent, Karaganda, Aktobe, Atyrau, Aktau, Kyzylorda, Uralsk, Taldykorgan, Ust-Kamenogorsk, Pavlodar, or type any other city
- 💼 **Multi-select professions** — 30+ popular job categories as buttons (waiter, cashier, courier, installer, IT, etc.), plus the option to type your own
- ⚡ **Real-time streaming search** — vacancies are sent to the chat as they're found, no need to wait for the whole search to finish
- 🔁 **Smart deduplication** — already-shown vacancies are never sent again, even on repeat searches
- 🛑 **Stop button** — cancel a search at any point
- 🔄 **"Search again"** — the bot immediately offers to start a new search once done
- 🕰 **Stale listing cleanup** — a background job checks vacancy links and flags anything older than 3 days with a dead link as inactive

## 🛠 Tech Stack

| Component            | Technology                          |
|-----------------------|--------------------------------------|
| Bot framework          | [aiogram 3](https://docs.aiogram.dev/) (async, FSM) |
| Database                | PostgreSQL + [asyncpg](https://github.com/MagicStack/asyncpg) |
| OLX.kz scraping         | [Playwright](https://playwright.dev/python/) + BeautifulSoup |
| HH.kz scraping          | REST API (`api.hh.ru`) — *currently disabled, see [Known Issues](#-known-issues)* |
| Embeddings (planned)    | sentence-transformers |
| Config                  | pydantic-settings (`.env`)          |

## 📁 Project Structure

```
job-bot/
├── bot/
│   ├── bot.py              # entry point, router registration
│   ├── keyboards.py        # keyboards (city, categories, stop)
│   ├── states.py           # FSM conversation states
│   └── handlers/
│       ├── start.py        # /start, main menu
│       └── search.py       # the entire search flow
├── db/
│   ├── schema.sql          # database schema
│   ├── connection.py       # asyncpg connection pool
│   ├── save.py              # vacancy insert with deduplication
│   └── link_checker.py     # background job for stale listings
├── parsers/
│   ├── base.py              # shared Vacancy model + parser interface
│   ├── olx_parser.py       # OLX.kz parser (Playwright)
│   └── hh_parser.py        # HH.kz parser (REST API)
├── categories.py            # profession list for buttons
├── cities.py                 # city list for buttons
├── config.py                  # .env loader
└── requirements.txt
```

## 🚀 Getting Started

### 1. Clone and set up the environment

```bash
git clone https://github.com/kuatsaparali/job-bot.git
cd job-bot
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Database

You'll need PostgreSQL installed. Create a database:

```bash
createdb job_bot_db
```

Apply the schema:

```bash
psql "postgresql://USER:PASSWORD@localhost:5432/job_bot_db" -f db/schema.sql
```

### 3. Environment variables

Copy `.env.example` to `.env` and fill in your own values:

```bash
cp .env.example .env
```

```env
BOT_TOKEN=your_token_from_BotFather
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/job_bot_db
```

### 4. Run the bot

```bash
python -m bot.bot
```

### 5. (Optional) Clean up stale listings

Run this periodically (e.g. daily via cron):

```bash
python -m db.link_checker
```

## ⚠️ Known Issues

- **HH.kz is currently disabled.** `api.hh.ru` is now blocking unauthenticated requests (`403 Forbidden`). The `HH_ENABLED` flag in `bot/handlers/search.py` is set to `False`. Planned fix: OAuth authorization or switching to Playwright-based scraping like OLX.
- **The OLX parser depends on the site's markup** (CSS-in-JS classes, card tags) — if OLX changes its design, selectors in `parsers/olx_parser.py` may need updating. Use `scripts/debug_olx.py` to diagnose.

## 🗺 Roadmap

- [ ] Restore HH.kz support (OAuth or Playwright)
- [ ] Saved category subscriptions — background notifications without repeating the dialog
- [ ] Semantic search over vacancy embeddings
- [ ] Docker Compose for one-command deployment

## 📄 License

Personal learning project. No license selected.
