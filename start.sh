#!/usr/bin/env bash
# start.sh — SATU command untuk semua: install + minta token bot Telegram + jalankan.
# Pakai:  ./start.sh
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "  Qoder Router — Setup & Jalankan"
echo "=============================================="

# --- 1. Cek dependency ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python3 tidak ada. Install dulu Python 3.10+"; exit 1
fi
if ! command -v node >/dev/null 2>&1; then
  echo "❌ Node.js tidak ada. Install dulu Node 18+ (https://nodejs.org)"; exit 1
fi

# --- 2. Install dependency backend (sekali saja) ---
if [ ! -d backend/.venv ]; then
  echo "→ Install dependency backend (sekali saja, mungkin 1-2 menit)..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install --quiet --upgrade pip
  backend/.venv/bin/pip install --quiet -r backend/requirements.txt
  echo "  ✓ dependency terinstall"
fi

# --- 3. Minta token bot Telegram (simpan ke bot/.env) ---
if [ ! -f bot/.env ] || ! grep -q "TELEGRAM_BOT_TOKEN=." bot/.env 2>/dev/null; then
  echo ""
  echo "→ Masukkan token bot Telegram kamu (dari @BotFather):"
  printf "  Token: "
  read -r TG_TOKEN
  mkdir -p bot
  echo "TELEGRAM_BOT_TOKEN=$TG_TOKEN" > bot/.env
  echo "QODER_BASE_URL=http://localhost:8010/v1" >> bot/.env
  echo "  ✓ token tersimpan di bot/.env"
fi

# --- 4. Jalankan router (background) + bot (foreground) ---
echo ""
echo "→ Menjalankan router (http://localhost:8010)..."
cd backend
setsid ./.venv/bin/python run.py > /tmp/qoder-router.log 2>&1 < /dev/null &
cd ..
sleep 6
if curl -s --max-time 5 http://localhost:8010/api/health >/dev/null 2>&1; then
  echo "  ✓ router jalan di http://localhost:8010"
else
  echo "  ⚠ router belum merespons (cek /tmp/qoder-router.log)"
fi

echo ""
echo "✓ SEMUA SIAP! Sekarang jalankan bot Telegram (di terminal ini):"
echo "  cd bot && ../backend/.venv/bin/python bot.py"
echo ""
echo "  Buka bot kamu di Telegram, kirim file .txt berisi list PAT (pt-... per baris)"
echo "  → kamu akan dapat BASE URL + API key untuk harness."
echo ""
echo "(tekan Ctrl+C untuk berhenti; router tetap jalan di background)"
echo "Menjalankan bot Telegram..."
cd bot
exec ../backend/.venv/bin/python bot.py
