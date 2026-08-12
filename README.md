# 🍽️ Yazio Nutrition Integrator

> A Telegram bot that analyzes food photos with Google Gemini and automatically syncs meals to your **Yazio** food
> diary with no subscription.

<p align="center">
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

<table>
  <tr>
    <td align="center">
      <img src="docs/meal-analysis.png" width="300"><br>
      <b>Meal Analysis</b>
    </td>
    <td align="center">
      <img src="docs/daily-summary.png" width="300"><br>
      <b>Daily Summary</b>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/copy-view.png" width="300"><br>
      <b>Copy for Yazio AI</b>
    </td>
    <td align="center">
      <img src="docs/yazio-proof.png" width="300"><br>
      <b>Synced to Yazio</b>
    </td>
  </tr>
</table>
---

## 🏗️ Tech Stack

| Layer             | Technology                                                                        |
|-------------------|-----------------------------------------------------------------------------------|
| **Bot framework** | [aiogram 3](https://docs.aiogram.dev/)                                            |
| **Web server**    | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)    |
| **AI model**      | [Google Gemini](https://ai.google.dev/) (2.0 Flash)                               |
| **Database**      | PostgreSQL + [asyncpg](https://github.com/MagicStack/asyncpg)                     |
| **HTTP client**   | [httpx](https://www.python-httpx.org/) (with HTTP/2)                              |
| **Config**        | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| **Deployment**    | systemd + nginx + Let's Encrypt                                                   |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Public HTTPS endpoint (for Telegram webhook)
- Telegram Bot Token → [@BotFather](https://t.me/BotFather)
- Google Gemini API Key → [Google AI Studio](https://aistudio.google.com/apikey)
- Yazio Bearer Token → see [How to get Yazio token](#-how-to-get-yazio-bearer-token)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/YazioNutritionIntegrator.git
cd YazioNutritionIntegrator
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER foodbot WITH PASSWORD 'foodbotpass';"
sudo -u postgres psql -c "CREATE DATABASE foodbot OWNER foodbot;"
```

### 4. Configure environment

```bash
cp .env.example .env
nano .env
```

Fill in all the required values (see [Configuration](#️-configuration)).

### 5. Run

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If deployed behind nginx with SSL, the bot will automatically register its webhook on startup.

---

## ⚙️ Configuration

All settings live in `.env`.

| Variable             | Description                                                   | Example                                       |
|----------------------|---------------------------------------------------------------|-----------------------------------------------|
| `BOT_TOKEN`          | Telegram bot token from BotFather                             | `123456:ABC...`                               |
| `ALLOWED_USER_IDS`   | JSON array of your Telegram account IDs which can use the bot | `[123456789]`                                 |
| `WEBHOOK_BASE_URL`   | Your server's HTTPS URL                                       | `https://your-domain.com`                     |
| `WEBHOOK_SECRET`     | Random string for webhook verification                        | `super-secret-string`                         |
| `DATABASE_URL`       | PostgreSQL connection string                                  | `postgresql://foodbot:pass@127.0.0.1/foodbot` |
| `GEMINI_API_KEY`     | Google Gemini API key                                         | `AIza...`                                     |
| `GEMINI_MODEL`       | Gemini model name                                             | `gemini-2.0-flash`                            |
| `USER_TIMEZONE`      | IANA timezone for meal detection                              | `Asia/Krasnoyarsk`                            |
| `YAZIO_BEARER_TOKEN` | Your Yazio bearer token                                       | `c7bbe97050...`                               |
| `YAZIO_USER_AGENT`   | User-Agent header (mimics Yazio iOS app)                      | `YAZIO/26.31.0 ...`                           |

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

## 🔑 How to Get Yazio Bearer Token

> ⚠️ Yazio has no public API. The bot works by reverse-engineering the mobile app's HTTP traffic. Use at your own risk.

You'll need to intercept your Yazio app traffic once to extract the bearer token.

### Using mitmproxy (recommended)

1. Install mitmproxy:
   ```bash
   pip install mitmproxy
   ```

2. Start it:
   ```bash
   mitmweb --listen-host 0.0.0.0 --listen-port 8080
   ```

3. On your phone:
    - Connect to the same Wi-Fi as your computer
    - Set HTTP proxy to your computer's IP:8080
    - Open `http://mitm.it` and install the CA certificate
    - Trust the certificate in system settings

4. Open Yazio and add any food item

5. In mitmweb, find the request:
   ```
   POST https://yzapi.yazio.com/v22/user/consumed-items
   ```

6. Copy the `Authorization: Bearer <TOKEN>` value into your `.env`

### Token expiration

Tokens don't last forever. When you see `⚠️ Not synced` errors in the bot with a 401 message, just repeat the extraction
and update `YAZIO_BEARER_TOKEN`.

---

## 🖥️ Production Deployment

### 1. systemd service

```ini
# /etc/systemd/system/food-tracker-bot.service
[Unit]
Description = Yazio Nutrition Integrator
After = network-online.target postgresql.service
Wants = network-online.target

[Service]
User = your_user
WorkingDirectory = /home/your_user/YazioNutritionIntegrator
Environment = PYTHONUNBUFFERED=1
ExecStart = /home/your_user/YazioNutritionIntegrator/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart = always
RestartSec = 3

[Install]
WantedBy = multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now food-tracker-bot
```

### 2. nginx reverse proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Let's Encrypt SSL

```bash
sudo certbot --nginx -d your-domain.com
```

### 4. One-command redeploy

```bash
# deploy.sh
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "== Pull latest code =="
git fetch origin main
git reset --hard origin/main

echo "== Install deps =="
./.venv/bin/pip install --quiet -r requirements.txt

echo "== Restart service =="
sudo /bin/systemctl restart food-tracker-bot

echo "== Done =="
```

Add sudoers rule to allow restart without password:

```bash
sudo visudo -f /etc/sudoers.d/food-tracker-bot
```

```
your_user ALL=(ALL) NOPASSWD: /bin/systemctl restart food-tracker-bot
```

Now you can redeploy with a single SSH command:

```bash
ssh user@server "cd YazioNutritionIntegrator && ./deploy.sh"
```

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
│   ├── db.py                 # asyncpg pool + repository
│   ├── models.py             # Domain models
│   └── main.py               # FastAPI app + webhook
├── deploy.sh                 # Redeploy script
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🗺️ Roadmap

- [ ] Per-user Yazio credentials (bring-your-own-token)
- [ ] Automatic Yazio token refresh
- [ ] Meal reminders
- [ ] Weekly / monthly summary
- [ ] Image compression before Gemini upload
- [ ] Docker Compose setup

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