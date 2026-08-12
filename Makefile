.PHONY: help install deploy logs status restart stop start uninstall

SERVICE_NAME = food-tracker-bot

help:
	@echo "Yazio Nutrition Integrator — Makefile"
	@echo ""
	@echo "  make install     — install everything (nginx, ssl, db, systemd)"
	@echo "  make deploy      — git pull + reinstall deps + restart"
	@echo "  make logs        — tail service logs"
	@echo "  make status      — service status"
	@echo "  make restart     — restart service"
	@echo "  make stop        — stop service"
	@echo "  make start       — start service"
	@echo "  make uninstall   — remove everything (keeps source code)"

install:
	@bash install.sh

deploy:
	@git fetch origin main
	@git reset --hard origin/main
	@./.venv/bin/pip install --quiet -r requirements.txt
	@sudo systemctl restart $(SERVICE_NAME)
	@echo "✓ Deployed"

logs:
	@sudo journalctl -u $(SERVICE_NAME) -f

status:
	@sudo systemctl status $(SERVICE_NAME)

restart:
	@sudo systemctl restart $(SERVICE_NAME)
	@echo "✓ Restarted"

stop:
	@sudo systemctl stop $(SERVICE_NAME)
	@echo "✓ Stopped"

start:
	@sudo systemctl start $(SERVICE_NAME)
	@echo "✓ Started"

uninstall:
	@bash uninstall.sh