#!/usr/bin/env bash
# Ejecuta el bot y lo reinicia automáticamente si se cae (corte de red, error, etc.)
# Uso: ./run_bot.sh

set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${BOT_DIR}/venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "No se encuentra el entorno virtual."
    echo "Ejecuta primero: ./install.sh"
    echo "O manualmente:"
    echo "  python3 -m venv venv"
    echo "  ./venv/bin/pip install -r requirements.txt"
    exit 1
fi

cd "$BOT_DIR"
echo "Bot de Gamer Tags - Reinicio automático activado."
echo "Si el bot se cae por corte de red o error, se reiniciará en 10 segundos."
echo "Para detener: pulsa Ctrl+C."
echo ""

while true; do
    "$PYTHON" bot.py
    exit_code=$?
    echo ""
    echo "[$(date +%H:%M:%S)] El bot terminó (código ${exit_code}). Reiniciando en 10 segundos..."
    sleep 10
done
