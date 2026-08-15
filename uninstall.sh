#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
SERVICE_NAME="food-tracker-bot"

DB_NAME="foodbot"
DB_USER="foodbot"

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; N='\033[0m'
info() { echo -e "${B}==>${N} $1"; }
ok()   { echo -e "${G}✓${N} $1"; }
warn() { echo -e "${Y}!${N} $1"; }

[[ $EUID -eq 0 ]] && { echo "Do NOT run as root"; exit 1; }

# Get domain from .env (may fail — that's ok)
DOMAIN=""
if [[ -f "$PROJECT_DIR/.env" ]]; then
    WEBHOOK_BASE_URL="$(grep -E '^WEBHOOK_BASE_URL=' "$PROJECT_DIR/.env" | head -n1 | cut -d'=' -f2- | tr -d '"' | tr -d "'")"
    DOMAIN="$(echo "${WEBHOOK_BASE_URL:-}" | sed -E 's~https?://~~; s~/.*~~')"
fi

echo
warn "This will remove:"
echo "  - systemd service: $SERVICE_NAME"
echo "  - nginx config for the bot"
echo "  - sudoers rule"
echo "  - PostgreSQL database '$DB_NAME' and user '$DB_USER' (INCLUDING ALL DATA)"
echo "  - Python .venv"
[[ -n "$DOMAIN" ]] && echo "  - SSL certificate for $DOMAIN"
echo
warn "Project source code and .env will BE KEPT (delete manually if needed)"
echo
read -rp "Are you sure? Type 'yes' to continue: " CONFIRM
[[ "$CONFIRM" != "yes" ]] && { echo "Aborted."; exit 0; }

# --------------------------------------------------------
# systemd
# --------------------------------------------------------
info "Removing systemd service..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
sudo rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl reset-failed 2>/dev/null || true
ok "systemd removed"

# --------------------------------------------------------
# sudoers
# --------------------------------------------------------
info "Removing sudoers rule..."
sudo rm -f "/etc/sudoers.d/${SERVICE_NAME}"
ok "sudoers removed"

# --------------------------------------------------------
# nginx
# --------------------------------------------------------
info "Removing nginx config..."
sudo rm -f "/etc/nginx/sites-enabled/${SERVICE_NAME}"
sudo rm -f "/etc/nginx/sites-available/${SERVICE_NAME}"
sudo nginx -t 2>/dev/null && sudo systemctl reload nginx || warn "nginx reload skipped"
ok "nginx config removed"

# --------------------------------------------------------
# SSL
# --------------------------------------------------------
if [[ -n "$DOMAIN" && -d "/etc/letsencrypt/live/$DOMAIN" ]]; then
    info "Removing SSL certificate..."
    sudo certbot delete --cert-name "$DOMAIN" --non-interactive 2>/dev/null || warn "cert delete skipped"
    ok "SSL certificate removed"
fi

# --------------------------------------------------------
# PostgreSQL
# --------------------------------------------------------
info "Dropping PostgreSQL database and user..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" >/dev/null 2>&1 || true
sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" >/dev/null 2>&1 || true
ok "PostgreSQL cleaned"

# --------------------------------------------------------
# venv
# --------------------------------------------------------
info "Removing Python venv..."
rm -rf "$PROJECT_DIR/.venv"
ok "venv removed"

echo
echo -e "${G}================================================${N}"
echo -e "${G}✓ Uninstall complete!${N}"
echo -e "${G}================================================${N}"
echo
echo "  Source code kept at: $PROJECT_DIR"
echo "  To fully remove:     rm -rf $PROJECT_DIR"
echo
