#!/usr/bin/env bash
# Instalación del bot en Linux / Kali Linux
# Uso: ./install.sh

set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 no está instalado."
    echo "En Kali/Debian: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    exit 1
fi

if ! python3 -c "import venv" 2>/dev/null; then
    echo "Error: falta el módulo venv."
    echo "En Kali/Debian: sudo apt install -y python3-venv"
    exit 1
fi

echo "Creando entorno virtual..."
python3 -m venv venv

echo "Instalando dependencias..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Se creó .env desde .env.example. Edítalo y añade DISCORD_TOKEN y CHANNEL_ID."
else
    echo ".env ya existe; no se sobrescribió."
fi

echo ""
echo "Instalación completada."
echo "1. Edita .env con tu token y el ID del canal."
echo "2. Ejecuta: ./run_bot.sh"
echo "   O una sola vez: ./venv/bin/python bot.py"
