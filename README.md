# Qoder Router — Pakai Banyak PAT Qoder dengan Mudah

Router ini membungkus **banyak PAT Qoder** jadi satu **API (OpenAI-compatible)** yang bisa kamu
colok ke harness apa pun (Claude Code, ZCode, 9router, dll). Kelola PAT-nya lewat **bot Telegram**
— tinggal upload list PAT, cek kredit, langsung dapat **Base URL + API key**.

Jalan **di laptop kamu sendiri** (bukan server orang lain) — jadi lebih aman & cepat.

---

## Apa yang didapat

- ✅ **Base URL + API key** — siap dicolok ke harness OpenAI-compatible
- ✅ **Rotasi PAT otomatis ("peluru")** — masukkan banyak PAT, kalau satu habis otomatis pindah ke berikutnya
- ✅ **Cek kredit & tanggal berakhir** tiap PAT lewat Telegram
- ✅ **Reasoning aktif** (bisa atur `low/medium/high/max` per model)
- ✅ **Tool-calling** berfungsi normal
- ✅ **Daftar model** lengkap + info reasoning effort

---

## Cara Pakai (3 langkah)

### 1. Install

Butuh **Python 3.10+** dan **Node.js 18+**.

```bash
# clone repo ini
git clone <url-repo-kamu>
cd qoder-route/backend

# install dependency Python
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Jalankan Router

```bash
cd backend
./start.sh                          # Linux/Mac (Windows: start.bat)
```

Router jalan di `http://localhost:8010`. Catat **API key** yang muncul di layar
(atau buat sendiri lewat bot Telegram).

### 3. Masukkan Token Bot Telegram (UI-nya)

Bot Telegram dipakai untuk **mengelola PAT** (upload, cek kredit, dapat API key).

```bash
cd ../bot
# masukkan token bot Telegram kamu:
echo "TELEGRAM_BOT_TOKEN=token_kamu_di_sini" > .env
# (opsional) alamat router:
echo "QODER_BASE_URL=http://localhost:8010/v1" >> .env

python3 bot.py
```

Cara dapat token bot Telegram: buka **@BotFather** di Telegram → `/newbot` → ikuti
instruksinya → salin token-nya.

---

## Cara Pakai Bot Telegram

Buka bot kamu di Telegram, lalu:

1. **Kirim file `.txt`** berisi list PAT (format `pt-...` per baris) → bot cek
   **sisa kredit** + **tanggal berakhir** tiap PAT, lalu kasih **Base URL + API key**.
2. `/models` — daftar model + info reasoning effort
3. `/status` — cek kredit & expiry semua PAT kamu

PAT yang sudah di-upload otomatis dipakai router (dirotasi saat kredit habis).
Mau tambah PAT lagi? Kirim file `.txt` lagi → **nambah**, bukan ganti.

---

## Colok ke Harness kamu

Di harness OpenAI-compatible (Claude Code / ZCode / 9router / dll):

| Setting | Nilai |
|---|---|
| **Base URL** | `http://localhost:8010/v1` (atau IP laptop kamu) |
| **API key** | dari bot Telegram (atau yang dicetak router) |
| **Model** | lihat `/models` (mis. `kmodel_latest` = Kimi-K3.1-Pro) |

Contoh pakai (curl):
```bash
curl http://localhost:8010/v1/chat/completions \
  -H "Authorization: Bearer API_KEY_KAMU" \
  -H "Content-Type: application/json" \
  -d '{"model":"kmodel_latest","messages":[{"role":"user","content":"halo"}]}'
```

---

## Info Model & Reasoning Effort

Tiap model punya **aturan reasoning sendiri** (tidak bisa disamakan). Ketik `/models`
di bot untuk daftar lengkap. Contoh:

| Model (id) | Nama | Reasoning effort |
|---|---|---|
| `kmodel_latest` | Kimi-K3.1-Pro | `low` / `high` / `max` (default high) |
| `qfmodel` | Qwen3.8-Flash | `low` / `medium` / `xhigh` (default medium), bisa on/off |
| `qmodel_38max` | Qwen3.8-Max | `low` / `medium` / `xhigh` (default medium), bisa on/off |
| `dmodel` | DeepSeek-V4-Pro | `high` / `max` (default max), bisa on/off |
| `gmodel` | GLM-5.3 | `low` / `high` / `max` (default high) |
| `cmodel` | Cantus | `low` / `medium` / `high` / `xhigh` / `max` |

Atur reasoning di request harness: `"reasoning_effort": "high"` (atau `off` untuk mati).
Level yang tidak didukung model otomatis diklam ke yang terdekat.

---

## Cara Kerja (singkat)

- Router menerima request OpenAI-compatible → meneruskan ke Qoder dengan **signing asli**
  (WASM) → hasil dikembalikan ke harness.
- **Rotasi PAT**: PAT dengan kredit habis otomatis dilewati, pindah ke PAT berikutnya.
- **Cek kredit** lewat `openapi.qoder.sh` (jobToken → plan + quota) — real-time saat dicek.
- Request **identik dengan qodercli native** (header, body, signing, endpoint) + punya
  **antre-recovery** (tunggu + retry) seperti native — jadi tidak mudah diantre/ditolak.

---

## Struktur

```
qoder-route/
├── backend/          # router utama (FastAPI + signer WASM)
│   ├── app/          # API OpenAI + Anthropic, routing PAT
│   ├── signer/       # signing WASM (protokol Qoder)
│   └── run.py        # jalankan router
├── bot/              # bot Telegram (kelola PAT)
│   ├── bot.py        # bot utama
│   └── .env          # token Telegram (jangan di-share!)
└── frontend/         # dashboard (opsional)
```

---

## Catatan Penting

- **Token Telegram & API key jangan dibagikan** — simpan di `.env` (sudah di-gitignore).
- Kredit tiap PAT = milikmu; router hanya memakai, tidak menambah.
- Untuk banyak PAT, siapkan file `.txt` (satu PAT per baris) lalu upload ke bot.
