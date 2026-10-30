# Qoder Router

Bungkus **banyak PAT Qoder** jadi satu **API (OpenAI-compatible)** — kelola PAT-nya
lewat **bot Telegram**, langsung dapat **Base URL + API key** untuk harness kamu
(Claude Code, ZCode, 9router, dll). Jalan di **laptop kamu sendiri**.

## Install & Jalankan (1 command)

```bash
git clone https://github.com/pixelbrow720/qoder-router.git
cd qoder-router
./start.sh
```

`start.sh` otomatis: install dependency → **minta token bot Telegram** → jalankan router + bot.

> Butuh **Python 3.10+** dan **Node.js 18+**.
> Token bot Telegram dapat dari **@BotFather** (Telegram) → `/newbot` → salin token-nya.

## Pakai Bot Telegram

Buka bot kamu di Telegram:

1. **Kirim file `.txt`** berisi list PAT (format `pt-...`, satu per baris) → bot cek
   **sisa kredit + tanggal berakhir** tiap PAT, lalu kasih **Base URL + API key**.
2. `/models` — daftar model + reasoning effort
3. `/status` — cek kredit & expiry semua PAT

Mau tambah PAT lagi? Kirim `.txt` lagi → **nambah**, bukan ganti.

## Colok ke Harness

| Setting | Nilai |
|---|---|
| Base URL | `http://localhost:8010/v1` |
| API key | dari bot Telegram |
| Model | lihat `/models` (mis. `kmodel_latest` = Kimi-K3.1-Pro) |

Contoh:
```bash
curl http://localhost:8010/v1/chat/completions \
  -H "Authorization: Bearer API_KEY_KAMU" \
  -H "Content-Type: application/json" \
  -d '{"model":"kmodel_latest","messages":[{"role":"user","content":"halo"}]}'
```

## Model & Reasoning

Tiap model punya aturan reasoning **berbeda** (tidak bisa disamakan). Ketik `/models`
di bot untuk lengkap. Contoh: `kmodel_latest` (Kimi-K3.1-Pro) = `low/high/max`;
`qfmodel` (Qwen3.8-Flash) = `low/medium/xhigh` + bisa on/off.

Atur di request: `"reasoning_effort": "high"` (atau `off` untuk mati).

## Fitur

- **Rotasi PAT otomatis** — PAT habis kredit → pindah ke berikutnya ("peluru")
- **Cek kredit & expiry** real-time lewat Telegram
- **Reasoning aktif** per-model + **tool-calling** normal
- **Request identik qodercli native** + anti-antre (queue-recovery)

## Catatan

- Token Telegram & API key **jangan dibagikan** (tersimpan di `bot/.env`).
- Kredit tiap PAT = milikmu; router hanya memakai.
