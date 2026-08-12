### настройка systemd
```bash
sudo tee /etc/systemd/system/food-tracker-bot.service > /dev/null <<EOF
[Unit]
Description=Food Tracker Bot
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
User=whoami
WorkingDirectory=/home/whoami/YazioNutritionIntegrator
Environment=PYTHONUNBUFFERED=1
ExecStart=/home/whoami/YazioNutritionIntegrator/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable food-tracker-bot
sudo systemctl start food-tracker-bot
sudo systemctl status food-tracker-bot
```

### логи systemd
```bash
sudo journalctl -u food-tracker-bot -f
```

### deploy script
```bash
nano /home/USERNAME/YazioNutritionIntegrator/deploy.sh
```

insert this
```text
#!/usr/bin/env bash
set -euo pipefail

cd /home/USERNAME/YazioNutritionIntegrator

echo "== Pull latest code =="
git fetch origin main
git reset --hard origin/main

echo "== Install deps =="
./.venv/bin/pip install --quiet -r requirements.txt

echo "== Restart service =="
sudo /bin/systemctl restart food-tracker-bot

echo "== Done =="
```

make it executable
```bash
chmod +x deploy.sh
```

let your user reload service without password
```bash
USERNAME ALL=(ALL) NOPASSWD: /bin/systemctl restart food-tracker-bot
```