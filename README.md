# Qoder Router

Bungkus **banyak PAT Qoder** jadi **API (OpenAI-compatible)** — kelola PAT lewat
**bot Telegram**, dapat **Base URL + API key** untuk harness (Claude Code, ZCode, 9router, dll).
Jalan di laptop kamu sendiri.

## Install (1 command)

```bash
curl -fsSL https://raw.githubusercontent.com/pixelbrow720/qoder-router/main/install.sh | bash
```

Saat install, kamu akan diminta **token bot Telegram** (dari **@BotFather** → `/newbot` → salin token).

## Jalankan

```bash
qoder-router start     # jalan di background + auto-start saat laptop nyala
qoder-router bot       # jalankan bot Telegram (kirim PAT di sini)
```

## Pakai Bot Telegram

Kirim **file `.txt`** berisi list PAT (`pt-...`, satu per baris) ke bot →
dapat **Base URL + API key**. `/models` = daftar model, `/status` = cek kredit.

## Colok ke Harness

- **Base URL:** `http://localhost:8010/v1`
- **API key:** dari bot Telegram
- **Model:** `kmodel_latest` (Kimi-K3.1-Pro) — daftar lengkap di `/models`

```bash
curl http://localhost:8010/v1/chat/completions \
  -H "Authorization: Bearer API_KEY_KAMU" \
  -H "Content-Type: application/json" \
  -d '{"model":"kmodel_latest","messages":[{"role":"user","content":"halo"}]}'
```

## Perintah

| Perintah | Fungsi |
|---|---|
| `qoder-router start` | jalan background + auto-start saat boot |
| `qoder-router stop` | berhenti |
| `qoder-router status` | cek status |
| `qoder-router logs` | lihat log |
| `qoder-router bot` | jalankan bot Telegram |

## Fitur

- **Rotasi PAT otomatis** — PAT habis → pindah ke berikutnya
- **Cek kredit & expiry** lewat Telegram
- **Reasoning aktif** per-model + **tool-calling** normal
- **Anti-antre** — request identik qodercli native + auto-retry
