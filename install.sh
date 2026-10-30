#!/usr/bin/env bash
# install.sh — SATU command install (seperti `npm install -g 9router`).
# Pakai:  curl -fsSL https://raw.githubusercontent.com/pixelbrow720/qoder-router/main/install.sh | bash
# Hasil:  perintah `qoder-router` siap + auto-start saat laptop nyala.
set -e

REPO="https://github.com/pixelbrow720/qoder-router.git"
DIR="$HOME/.qoder-router"
BIN="$HOME/.local/bin"

echo "=============================================="
echo "  Qoder Router — Install"
echo "=============================================="

# cek dependency
command -v python3 >/dev/null 2>&1 || { echo "❌ butuh Python 3.10+ (https://python.org)"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ butuh Node.js 18+ (https://nodejs.org)"; exit 1; }

# 1. ambil kode
echo "→ Mengunduh Qoder Router ke $DIR ..."
rm -rf "$DIR"
git clone --depth 1 "$REPO" "$DIR" 2>/dev/null || {
  # kalau git tidak ada, pakai curl (zip)
  echo "  (git tidak ada, pakai curl)"; command -v git >/dev/null 2>&1 || { echo "❌ butuh git"; exit 1; }
}
cd "$DIR"

# 2. install dependency backend
echo "→ Install dependency (sekali saja, pakai binary wheel — tanpa compile) ..."
python3 -m venv backend/.venv
backend/.venv/bin/pip install --quiet --upgrade pip setuptools wheel
# --prefer-binary: pakai wheel siap pakai (TANPA compile Rust).
# --only-binary pydantic-core: paksa wheel utk bagian yang butuh Rust.
backend/.venv/bin/pip install --quiet --prefer-binary --only-binary pydantic-core -r backend/requirements.txt || {
  echo ""
  echo "❌ Gagal install dependency."
  echo "   Jika error soal Rust/cargo (pydantic-core):"
  echo "   - Pakai Python 3.12 (paling kompatibel), ATAU"
  echo "   - Install Rust:  curl https://sh.rustup.rs -sSf | sh  lalu  rustup default stable"
  exit 1
}

# 3. buat perintah `qoder-router`
mkdir -p "$BIN"
cat > "$BIN/qoder-router" << 'EOF'
#!/usr/bin/env bash
DIR="$HOME/.qoder-router"
LOG="$DIR/qoder-router.log"
PIDF="$DIR/.router.pid"
cd "$DIR/backend"
start_router() {
  setsid ./.venv/bin/python run.py > "$LOG" 2>&1 < /dev/null &
  echo $! > "$PIDF"
}
case "${1:-run}" in
  start)   # background + auto-start saat boot
    [ -f "$PIDF" ] && kill "$(cat $PIDF)" 2>/dev/null
    start_router
    sleep 6
    echo "✓ Qoder Router jalan di http://localhost:8010 (background)"
    echo "  Jalankan bot Telegram:  qoder-router bot"
    ;;
  stop)
    [ -f "$PIDF" ] && kill "$(cat $PIDF)" 2>/dev/null && rm -f "$PIDF" && echo "✓ dihentikan" || echo "tidak jalan"
    ;;
  restart) $0 stop; sleep 1; $0 start ;;
  status)
    if [ -f "$PIDF" ] && kill -0 "$(cat $PIDF)" 2>/dev/null; then
      echo "✓ Qoder Router: JALAN (PID $(cat $PIDF)) — http://localhost:8010"
    else
      echo "✗ Qoder Router: BERHENTI  (jalankan: qoder-router start)"
    fi
    ;;
  logs)    tail -f "$LOG" ;;
  bot)     # jalankan bot Telegram (butuh token di bot/.env)
    cd "$DIR/bot"; exec "$DIR/backend/.venv/bin/python" bot.py ;;
  run)     # jalankan di foreground (tanpa background)
    exec ./.venv/bin/python run.py ;;
  *) echo "Pakai: qoder-router {start|stop|restart|status|logs|bot}"; exit 1 ;;
esac
EOF
chmod +x "$BIN/qoder-router"

# 4. auto-start saat laptop nyala (systemd user service)
if command -v systemctl >/dev/null 2>&1; then
  mkdir -p "$HOME/.config/systemd/user"
  cat > "$HOME/.config/systemd/user/qoder-router.service" << EOF
[Unit]
Description=Qoder Router
After=network-online.target
[Service]
WorkingDirectory=$DIR/backend
ExecStart=$DIR/backend/.venv/bin/python run.py
Restart=on-failure
[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload >/dev/null 2>&1 || true
  systemctl --user enable qoder-router >/dev/null 2>&1 && echo "✓ auto-start saat laptop nyala (systemd)"
  # supaya jalan meski belum login: loginctl enable-linger
  loginctl enable-linger "$USER" >/dev/null 2>&1 || true
fi

# 5. generate admin key (utk keamanan endpoint /api/*)
ADMIN_KEY="adm-$(python3 -c 'import uuid; print(uuid.uuid4().hex)')"
echo "$ADMIN_KEY" > backend/admin.key
chmod 600 backend/admin.key
echo "✓ admin key dibuat (backend/admin.key)"

# 6. minta token bot Telegram
echo ""
echo "→ Masukkan token bot Telegram (dari @BotFather, /newbot):"
printf "  Token: "
read -r TG_TOKEN
mkdir -p bot
echo "TELEGRAM_BOT_TOKEN=$TG_TOKEN" > bot/.env
echo "QODER_BASE_URL=http://localhost:8010/v1" >> bot/.env
echo "QODER_ADMIN_KEY=$ADMIN_KEY" >> bot/.env   # utk bot daftarkan PAT ke router
chmod 600 bot/.env

# 6. jalankan
echo ""
"$BIN/qoder-router" start
echo ""
echo "✓ INSTALL SELESAI!"
echo ""
echo "  Perintah:"
echo "    qoder-router start    # jalan di background + auto-start saat boot"
echo "    qoder-router bot      # jalankan bot Telegram (kirim PAT di sini)"
echo "    qoder-router status   # cek status"
echo "    qoder-router stop     # berhenti"
echo ""
echo "  Buka bot Telegram kamu → kirim file .txt PAT → dapat Base URL + API key."
