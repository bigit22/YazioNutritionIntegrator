# 🍽️ Yazio Nutrition Integrator

> A Telegram bot that analyzes food photos with Google Gemini and automatically syncs meals to your **Yazio** food
> diary — no subscription required.

<p align="center">
  <img src="https://github.com/bigit22/YazioNutritionIntegrator/actions/workflows/ci.yml/badge.svg" alt="CI">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white" alt="aiogram">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Gemini-3.5-4285F4?logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

---

## ✨ Features

- 📸 **Photo analysis** — send a food photo, get instant KBJU (calories, protein, fat, carbs) breakdown
- 📝 **Text descriptions** — no photo? Just describe what you ate
- 🌍 **Multilingual input** — write in any language, get consistent English responses
- 🕐 **Smart meal categorization** — automatically detects breakfast / lunch / dinner / snack by time of day
- 🔄 **Yazio auto-sync** — meals are pushed to your Yazio diary the moment they're analyzed
- 📊 **Daily summary** — see your totals with `/today`
- 🗑️ **Full CRUD** — delete meals from both the bot and Yazio in one click
- 📋 **Fallback mode** — if Yazio sync fails, get a copy-friendly text for Yazio AI
- 🔒 **Access control** — bot only responds to whitelisted Telegram IDs

---

## 📸 Screenshots

### Meal Analysis

Send a food photo with optional description — get an instant nutritional breakdown and one-tap sync to Yazio.

<p align="center">
  <img src="docs/meal-analysis.png" width="500">
</p>

### Daily Summary

Use `/today` to see all your meals and totals for the day.

<p align="center">
  <img src="docs/daily-summary.png" width="500">
</p>

### Copy for Yazio AI

If auto-sync fails, get a copy-friendly text to paste into Yazio's own AI parser.

<p align="center">
  <img src="docs/copy-view.png" width="500">
</p>

### Access Denied

Bot silently ignores unauthorized users and shows them their Telegram ID so they can request access.

<p align="center">
  <img src="docs/access-denied.png" width="500">
</p>

---

## 🏗️ Tech Stack

| Layer             | Technology                                                                        |
|-------------------|-----------------------------------------------------------------------------------|
| **Bot framework** | [aiogram 3](https://docs.aiogram.dev/)                                            |
| **Web server**    | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)    |
| **AI model**      | [Google Gemini](https://ai.google.dev/) (3.5 Flash Lite)                          |
| **Database**      | PostgreSQL + [asyncpg](https://github.com/MagicStack/asyncpg)                     |
| **HTTP client**   | [httpx](https://www.python-httpx.org/) (with HTTP/2)                              |
| **Config**        | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| **Deployment**    | systemd + nginx + Let's Encrypt (auto-configured via `make install`)              |

---

## 🚀 Quick Start

### Prerequisites

- Ubuntu 22.04+ (or any Debian-based distro)
- Python 3.11+
- A domain name pointing to your server (needed for HTTPS webhook)
- Telegram Bot Token → [@BotFather](https://t.me/BotFather)
- Google Gemini API Key → [Google AI Studio](https://aistudio.google.com/apikey)
- Yazio account + ability to run mitmproxy once → see [How to get Yazio tokens](#-how-to-get-yazio-tokens)

### 1. Clone the repo

```bash
git clone https://github.com/bigit22/YazioNutritionIntegrator.git
cd YazioNutritionIntegrator
```

### 2. Configure

```bash
cp .env.example .env
nano .env  # fill in your tokens and settings
```

See [Configuration](#️-configuration) for details.

### 3. Install everything

```bash
make install
```

This single command will:

- Install system packages (PostgreSQL, nginx, certbot)
- Create the database and user
- Set up a Python virtual environment and install dependencies
- Register a systemd service
- Configure nginx + Let's Encrypt SSL
- Start the bot

### 4. Seed Yazio tokens (one-time)

See [How to get Yazio tokens](#-how-to-get-yazio-tokens) below.

### 5. Verify

```bash
make status       # check that the service is running
make logs         # follow logs in real time
```

Open your bot in Telegram, send `/start` — done ✅

---

## 🛠️ Management

All operations are wrapped in a `Makefile` for convenience:

| Command          | Description                                                   |
|------------------|---------------------------------------------------------------|
| `make install`   | Install everything from scratch (idempotent — safe to re-run) |
| `make deploy`    | Pull latest code from `main`, reinstall deps, restart service |
| `make restart`   | Restart the bot service                                       |
| `make logs`      | Tail service logs                                             |
| `make status`    | Show systemd service status                                   |
| `make stop`      | Stop the service                                              |
| `make start`     | Start the service                                             |
| `make uninstall` | Remove everything (systemd, nginx, SSL, DB) — keeps source    |

### Redeploy from your local machine

After pushing changes to `main`, redeploy with a single SSH command:

```bash
ssh user@server "cd YazioNutritionIntegrator && make deploy"
```

---

## ⚙️ Configuration

All settings live in `.env`.

| Variable           | Description                                            | Example                                       |
|--------------------|--------------------------------------------------------|-----------------------------------------------|
| `BOT_TOKEN`        | Telegram bot token from BotFather                      | `123456:ABC...`                               |
| `ALLOWED_USER_IDS` | JSON array of Telegram user IDs allowed to use the bot | `[123456789]`                                 |
| `WEBHOOK_BASE_URL` | Your server's HTTPS URL                                | `https://your-domain.com`                     |
| `WEBHOOK_SECRET`   | Random string for webhook verification                 | `super-secret-string`                         |
| `DATABASE_URL`     | PostgreSQL connection string                           | `postgresql://foodbot:pass@127.0.0.1/foodbot` |
| `GEMINI_API_KEY`   | Google Gemini API key                                  | `AIza...`                                     |
| `GEMINI_MODEL`     | Gemini model name                                      | `gemini-3.5-flash-lite`                       |
| `USER_TIMEZONE`    | IANA timezone for meal detection                       | `Asia/Krasnoyarsk`                            |
| `YAZIO_USER_AGENT` | User-Agent header (mimics Yazio iOS app)               | `YAZIO/26.31.0 ...`                           |

> 💡 Yazio tokens (`access_token` + `refresh_token`) live in the database, not in `.env`. See the section below.

---

## 🕘 Meal Time Ranges

Meals are automatically categorized based on the user's local time:

| Time            | Meal Type    |
|-----------------|--------------|
| 09:00 – 11:59   | 🌅 Breakfast |
| 12:00 – 15:59   | ☀️ Lunch     |
| 17:00 – 21:59   | 🌙 Dinner    |
| Everything else | 🍿 Snack     |

You can adjust these in `app/services/meals.py` → `detect_meal_type()`.

---

## 🔑 How to Get Yazio Tokens

> ⚠️ Yazio has no public API. The bot works by reverse-engineering the mobile app's HTTP traffic. Use at your own risk.

You need to intercept a token pair (`access_token` + `refresh_token`) from Yazio's OAuth endpoint once. After that, the bot refreshes tokens automatically — you won't need to touch mitmproxy again unless Yazio invalidates your session (e.g. after logout or password change).

### Using mitmproxy

1. Install mitmproxy:

   ```bash
   pip install mitmproxy
   ```

2. Start it:

   ```bash
   mitmweb --listen-host 0.0.0.0 --listen-port 8080
   ```

   > 💡 If you sign in to Yazio via Apple ID, add `--ignore-hosts '^(.*\.)?apple\.com:443$' --ignore-hosts '^(.*\.)?icloud\.com:443$'` — Apple's certificate pinning blocks mitmproxy otherwise.

3. On your phone:
    - Connect to the same Wi-Fi as your computer
    - Set HTTP proxy to your computer's IP:8080
    - Open `http://mitm.it` and install the CA certificate
    - Trust the certificate in system settings

4. Trigger a token refresh in the Yazio app. Easiest way — log out and log back in. You can also just wait until the app refreshes on its own (happens every ~48 hours).

5. In mitmweb, find the request:

   ```
   POST https://yzapi.yazio.com/v22/oauth/token
   ```

6. Copy `access_token` and `refresh_token` from the response body:

   ```json
   {
       "access_token": "...",
       "refresh_token": "...",
       "expires_in": 172800
   }
   ```

### Seed the tokens

Run once from the project root:

```bash
PYTHONPATH=. ./.venv/bin/python scripts/seed_yazio_tokens.py <access_token> <refresh_token>
```

Done — the bot will keep tokens fresh automatically from now on.

---

## 📁 Project Structure

```
YazioNutritionIntegrator/
├── app/
│   ├── bot/
│   │   ├── handlers.py       # Telegram message handlers
│   │   ├── keyboards.py      # Inline keyboards
│   │   └── middleware.py     # Access control
│   ├── services/
│   │   ├── gemini.py         # Google Gemini API client
│   │   ├── meals.py          # Formatting & meal-type logic
│   │   └── yazio.py          # Yazio API client
│   ├── config.py             # Pydantic settings
│   ├── db.py                 # asyncpg pool + repositories
│   ├── models.py             # Domain models
│   └── main.py               # FastAPI app + webhook
├── docs/                     # Screenshots for README
├── scripts/
│   └── seed_yazio_tokens.py  # One-time token seeder
├── install.sh                # One-command installer
├── uninstall.sh              # One-command uninstaller
├── Makefile                  # Convenience commands
├── requirements.txt
├── .env.example
├── LICENSE
└── README.md
```

---

## 🗺️ Roadmap

Planned features and current progress live on the [project board](https://github.com/users/bigit22/projects/1).

Recently shipped:
- ✅ Automatic Yazio token refresh

---

## ⚠️ Disclaimer

This project is **not affiliated with, endorsed by, or sponsored by Yazio GmbH**. It uses reverse-engineered private API
endpoints. Use responsibly and at your own risk. The maintainer is not responsible for any account suspension or data
loss.

---

## 📄 License

[MIT](LICENSE) — do whatever you want, just don't blame me.

---

<p align="center">Made with 🍜 and Python</p>
