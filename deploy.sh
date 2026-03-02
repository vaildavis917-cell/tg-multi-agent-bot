#!/bin/bash
# ============================================================
# Скрипт деплоя бота на VPS
# Использование: bash deploy.sh
# ============================================================

set -e

APP_DIR="/opt/tg-multi-agent-bot"
SERVICE_NAME="tg-multi-agent-bot"
PYTHON="python3"

echo "══════════════════════════════════════════════════"
echo "  Деплой мульти-агентного TG бота"
echo "══════════════════════════════════════════════════"

# 1. Обновление системы и установка Python
echo "[1/6] Установка зависимостей системы..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv

# 2. Создание директории
echo "[2/6] Создание директории $APP_DIR..."
sudo mkdir -p "$APP_DIR"
sudo cp -r ./* "$APP_DIR/"
sudo cp .env "$APP_DIR/.env" 2>/dev/null || true

# 3. Виртуальное окружение
echo "[3/6] Создание виртуального окружения..."
cd "$APP_DIR"
$PYTHON -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. Создание директории логов
echo "[4/6] Создание директории логов..."
mkdir -p "$APP_DIR/logs"

# 5. Systemd сервис
echo "[5/6] Настройка systemd сервиса..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Multi-Agent Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/python bot.py
Restart=always
RestartSec=5
EnvironmentFile=${APP_DIR}/.env

[Install]
WantedBy=multi-user.target
EOF

# 6. Запуск
echo "[6/6] Запуск сервиса..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo ""
echo "══════════════════════════════════════════════════"
echo "  ✅ Бот успешно развёрнут!"
echo ""
echo "  Команды управления:"
echo "    sudo systemctl status  ${SERVICE_NAME}"
echo "    sudo systemctl restart ${SERVICE_NAME}"
echo "    sudo systemctl stop    ${SERVICE_NAME}"
echo "    sudo journalctl -u ${SERVICE_NAME} -f"
echo "══════════════════════════════════════════════════"
