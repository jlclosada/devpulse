#!/bin/bash
# DevPulse — Script de inicio local (sin Docker)
set -e
cd "$(dirname "$0")"

echo ""
echo "⚡ DevPulse — System Monitor"
echo "────────────────────────────"

if ! command -v python3 &>/dev/null; then echo "❌ Python 3 no encontrado"; exit 1; fi

[ ! -d venv ] && python3 -m venv venv
source venv/bin/activate

python -c "import psutil" 2>/dev/null || pip install -r requirements.txt -q

echo "✓ Listo. Abriendo http://localhost:8080"
(sleep 1.2 && open "http://localhost:8080") &
python -m uvicorn main:app --host 127.0.0.1 --port 8080 --no-access-log
