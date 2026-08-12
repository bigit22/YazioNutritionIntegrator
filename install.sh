#!/usr/bin/env bash
set -euo pipefail

# ========================================================
# Yazio Nutrition Integrator - Installer
# ========================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
SERVICE_NAME="food-tracker-bot"
CURRENT_USER="$(whoami)"

DB_NAME="foodbot"
DB_USER="foodbot"
DB_PASSWORD="foodbotpass"

# Colors
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; N='\033[0m'
info() { echo -e "${B}==>${N} $1"; }
ok()   { echo -e "${G}✓${N} $1"; }
warn() { echo -e "${Y}!${N} $1"; }
err()  { echo -e "${R}✗${N} $1"; exit 1; }

# --------------------------------------------------------
# Preflight
# --------------------------------------------------------
[[ $EUID -eq 0 ]] && err "Do NOT run as root. Run as your regular user (sudo will be invoked when needed)."

command -v sudo >/dev/null || err "sudo is required"
command -v python3 >/dev/null || err "python3 is required"

info "Installing to: $PROJECT_DIR"
info "As user: $CURRENT_USER"

# --------------------------------------------------------
# .env check
# --------------------------------------------------------
if [[ ! -f "$PROJECT_DIR/.env" ]]; then
    if [[ -f "$PROJECT_DIR/.env.example" ]]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        warn ".env created from .env.example — EDIT IT NOW and re-run install.sh"
        warn "  nano $PROJECT_DIR/.env"
        exit 1
    else
        err ".env not found and no .env.example to copy from"
    fi
fi
ok ".env exists"

# Load .env for domain/user extraction
set -a
source "$PROJECT_DIR/.env"
set +a

DOMAIN="$(echo "$WEBHOOK_BASE_URL" | sed -E 's~https?://~~; s~/.*~~')"
[[ -z "$DOMAIN" ]] && err "WEBHOOK_BASE_URL is empty in .env"
ok "Domain: $DOMAIN"

# --------------------------------------------------------
# System packages
# --------------------------------------------------------
info "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-venv python3-pip \
    postgresql \
    nginx \
    certbot python3-certbot-nginx \
    git curl
ok "System packages installed"

# --------------------------------------------------------
# PostgreSQL
# --------------------------------------------------------
info "Setting up PostgreSQL..."
sudo systemctl enable --now postgresql

if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    ok "DB user '$DB_USER' already exists"
else
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" >/dev/null
    ok "DB user '$DB_USER' created"
fi

if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    ok "DB '$DB_NAME' already exists"
else
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" >/dev/null
    ok "DB '$DB_NAME' created"
fi

# --------------------------------------------------------
# Python venv
# --------------------------------------------------------
info "Setting up Python venv..."
if [[ ! -d "$PROJECT_DIR/.venv" ]]; then
    python3 -m venv "$PROJECT_DIR/.venv"
    ok "venv created"
fi
"$PROJECT_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"
ok "Python deps installed"

# --------------------------------------------------------
# systemd
# --------------------------------------------------------
info "Setting up systemd service..."
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null <<EOF
[Unit]
Description=Yazio Nutrition Integrator
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$PROJECT_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
ok "systemd unit created"

# sudoers for passwordless restart
sudo tee "/etc/sudoers.d/${SERVICE_NAME}" > /dev/null <<EOF
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart ${SERVICE_NAME}
$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl status ${SERVICE_NAME}
EOF
sudo chmod 440 "/etc/sudoers.d/${SERVICE_NAME}"
ok "sudoers rule added"

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"
sleep 2
ok "systemd service started"

# --------------------------------------------------------
# nginx
# --------------------------------------------------------
info "Setting up nginx..."
sudo tee "/etc/nginx/sites-available/${SERVICE_NAME}" > /dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
sudo nginx -t
sudo systemctl reload nginx
ok "nginx configured"

# --------------------------------------------------------
# SSL
# --------------------------------------------------------
if [[ ! -d "/etc/letsencrypt/live/$DOMAIN" ]]; then
    info "Getting SSL certificate for $DOMAIN..."
    sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
        --register-unsafely-without-email --redirect
    ok "SSL certificate installed"
else
    ok "SSL certificate already exists"
fi

# --------------------------------------------------------
# Done
# --------------------------------------------------------
echo
echo -e "${G}================================================${N}"
echo -e "${G}✓ Installation complete!${N}"
echo -e "${G}================================================${N}"
echo
echo "  Domain:  https://$DOMAIN"
echo "  Health:  https://$DOMAIN/health"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo
echo "  Now open your bot in Telegram and send /start"
echo