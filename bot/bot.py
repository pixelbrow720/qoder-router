#!/usr/bin/env python3
"""bot.py — Telegram bot untuk Qoder Router (tanpa UI).

Alur:
  /start        -> penjelasan
  /models       -> daftar model id + reasoning effort
  /status       -> cek kredit + tanggal berakhir semua PAT milik user
  kirim .txt    -> parse list PAT, cek kredit/expiry tiap PAT, keluarkan
                   BASE URL + API key (siap dicolok ke harness)

Token dari env TELEGRAM_BOT_TOKEN (file .env / config — TIDAK ikut git).
Pakai:  ./venv/bin/python bot.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests

import qoder_pat
import store

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    # fallback: baca dari file .env se-folder (jangan commit!)
    for nama in (".env", "token.txt"):
        p = os.path.join(HERE, nama)
        if os.path.exists(p):
            for baris in open(p):
                baris = baris.strip()
                if baris.startswith("TELEGRAM_BOT_TOKEN="):
                    TOKEN = baris.split("=", 1)[1].strip().strip('"')
                elif baris and not baris.startswith("#") and not TOKEN:
                    TOKEN = baris
            break
if not TOKEN:
    print("TELEGRAM_BOT_TOKEN belum diisi (env / .env)"); sys.exit(1)

API = f"https://api.telegram.org/bot{TOKEN}"
BASE_URL = os.environ.get("QODER_BASE_URL", "http://localhost:8010/v1")

# Daftar model (sumber: live model/list Qoder 2026-10-30) — id, nama, efforts, default
MODELS = [
    ("auto", "Auto", [], "-", "routing otomatis (server pilih)"),
    ("ultimate", "Ultimate", ["low", "medium", "high", "xhigh", "max"], "high", "top-tier"),
    ("efficient", "Efficient", [], "-", "cepat/murah"),
    ("qmodel_38max", "Qwen3.8-Max", ["low", "medium", "xhigh"], "medium", "bisa on/off"),
    ("qfmodel", "Qwen3.8-Flash", ["low", "medium", "xhigh"], "medium", "bisa on/off"),
    ("kmodel_latest", "Kimi-K3.1-Pro", ["low", "high", "max"], "high", "thinking selalu"),
    ("kmodel", "Kimi-K2.8-Preview", ["low", "high", "max"], "high", "thinking selalu"),
    ("gmodel", "GLM-5.3", ["low", "high", "max"], "high", "thinking selalu"),
    ("gfmodel", "GLM-5.3-Flash", ["high", "max"], "max", "thinking selalu"),
    ("dmodel", "DeepSeek-V4-Pro", ["high", "max"], "max", "bisa on/off"),
    ("dfmodel", "DeepSeek-Flash", ["low", "high", "max"], "high", "bisa on/off"),
    ("mmodel", "MiniMax-M3.1-Flash", [], "-", "tanpa thinking"),
]


def tg(method: str, **params) -> dict:
    try:
        r = requests.post(f"{API}/{method}", json=params, timeout=30)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def kirim(chat_id: int, teks: str, parse="Markdown"):
    # Telegram pesan maks ~4096 char — potong aman
    for i in range(0, len(teks), 3900):
        tg("sendMessage", chat_id=chat_id, text=teks[i:i + 3900],
           parse_mode=parse, disable_web_page_preview=True)


def unduh_file(file_id: str) -> str | None:
    try:
        f = tg("getFile", file_id=file_id)
        fp = (f.get("result") or {}).get("file_path")
        if not fp:
            return None
        url = f"https://api.telegram.org/file/bot{TOKEN}/{fp}"
        return urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "replace")
    except Exception:
        return None


def parse_pats(teks: str) -> list[str]:
    import re
    return re.findall(r"pt-[A-Za-z0-9_\-]+", teks)


def cek_banyak(pats: list[str], workers: int = 32) -> list[dict]:
    """Cek banyak PAT SECARA PARALEL (tiap PAT 4 request HTTP berurutan,
    tapi antar PAT jalan bersamaan) -> ratusan PAT selesai dalam detik."""
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(qoder_pat.cek_pat, pats))


def register_ke_router(api_key: str, pats: list[str]) -> dict:
    """Daftarkan PAT ke router (jadi akun milik api_key) — tanpa validasi ulang."""
    if not pats:
        return {"masuk": 0, "dilewati": 0}
    try:
        r = requests.post("http://127.0.0.1:8010/api/accounts/bulk",
                          json={"owner_key": api_key, "pats": pats}, timeout=60)
        return r.json() if r.status_code == 200 else {"masuk": 0, "dilewati": len(pats)}
    except Exception:
        return {"masuk": 0, "dilewati": len(pats)}


def hari_sisa(tgl: str | None) -> int | None:
    """Berapa hari lagi sampai tanggal 'YYYY-MM-DD'. None bila tidak diketahui."""
    if not tgl:
        return None
    try:
        from datetime import date
        d = date.fromisoformat(tgl)
        return (d - date.today()).days
    except Exception:
        return None


def ringkasan(hasil: list[dict]) -> tuple[str, list[str]]:
    """Buat ringkasan ringkas: total kredit, grup sisa hari, auto-buang Free/0.
    Kembalikan (teks_ringkasan, daftar_PAT_valid_yang_disimpan)."""
    valid, buang = [], []
    for h in hasil:
        if not h.get("ok"):
            buang.append(h); continue
        rem = h.get("quota_remaining") or 0
        plan = (h.get("plan_name") or "").lower()
        if h.get("status") != "AKTIF" or rem <= 0 or plan == "free":
            buang.append(h)     # auto-remove: Free / 0 kredit / habis
        else:
            valid.append(h)

    total_kredit = sum((h.get("quota_remaining") or 0) for h in valid)
    # grup berdasar sisa hari
    grup: dict[int, int] = {}
    tgl: dict[int, str] = {}
    for h in valid:
        sisa = hari_sisa(h.get("expired"))
        k = sisa if sisa is not None else -1
        grup[k] = grup.get(k, 0) + 1
        if sisa is not None:
            tgl[k] = h.get("expired")

    L = []
    L.append(f"✅ *PAT aktif:* {len(valid)}  ·  🗑 *auto-dibuang* (Free/0 kredit): {len(buang)}")
    L.append(f"💰 *Total kredit:* {total_kredit:,.0f}")
    L.append("")
    L.append("📅 *Masa berlaku (sisa hari):*")
    for k in sorted(grup.keys(), reverse=True):
        if k < 0:
            L.append(f"   • tidak diketahui: {grup[k]} PAT")
        else:
            L.append(f"   • sisa *{k} hari* (s/d {tgl[k]}): {grup[k]} PAT")
    pats_valid = [h["pat"] for h in valid]
    return "\n".join(L), pats_valid


def handle_start(chat_id):
    kirim(chat_id,
          "🤖 *Qoder Router Bot*\n\n"
          "Kirim *file .txt* berisi list PAT (`pt-...` per baris) — aku akan:\n"
          "  • cek *sisa kredit* tiap PAT\n"
          "  • cek *tanggal berakhir* (trial ±2 minggu)\n"
          "  • keluarkan *Base URL + API key* untuk harness kamu\n\n"
          "Perintah:\n"
          "  /models — daftar model + reasoning effort\n"
          "  /status — kredit + expiry PAT kamu\n\n"
          "Contoh isi .txt:\n"
          "```\npt-AbC123...\npt-XyZ456...\n```")


def handle_models(chat_id):
    # Daftar model ID dlm blok kode (tap utk salin) + info reasoning effort
    ids = "\n".join(mid for mid, *_ in MODELS)
    baris = [
        "🗂 *Model ID* (tap blok utk salin):",
        f"```\n{ids}\n```",
        "",
        "*Reasoning effort per model:*",
    ]
    for mid, nama, eff, defau, ket in MODELS:
        eff_s = "/".join(eff) if eff else "tanpa thinking"
        baris.append(f"`{mid}` — *{nama}*: {eff_s} (default `{defau}`)")
    baris.append("")
    baris.append("_`off`/`none` = mati (model yg bisa on/off). Level tak didukung otomatis diklam ke terdekat._")
    kirim(chat_id, "\n".join(baris))


def handle_status(chat_id):
    u = store.get_user(chat_id)
    api_key = u.get("api_key") or store.api_key_untuk(chat_id)
    pats = u.get("pats") or []
    if not pats:
        kirim(chat_id, f"Belum ada PAT. Kirim file .txt berisi list PAT dulu.\n\n"
                       f"🔑 *API key* kamu (tap utk salin):\n`{api_key}`")
        return
    kirim(chat_id, "⏳ Mengecek %d PAT…" % len(pats))
    hasil = cek_banyak(pats)
    ringkas, pats_valid = ringkasan(hasil)
    kirim(chat_id, "\n".join([
        f"📊 *Status {len(pats)} PAT kamu*",
        "",
        ringkas,
        "",
        f"🔗 *Base URL* (tap utk salin):",
        f"`{BASE_URL}`",
        f"🔑 *API key* (tap utk salin):",
        f"`{api_key}`",
    ]))


def handle_patfile(chat_id, teks: str):
    pats = parse_pats(teks)
    if not pats:
        kirim(chat_id, "Tidak menemukan PAT (`pt-...`) di file itu.")
        return
    pats = list(dict.fromkeys(pats))  # unik, urut
    kirim(chat_id, "⏳ Mengecek %d PAT…" % len(pats))

    hasil = cek_banyak(pats)          # PARALEL — cepat utk ribuan
    ringkas, pats_valid = ringkasan(hasil)   # auto-buang Free/0 kredit

    api_key = store.api_key_untuk(chat_id)
    semua_pats = store.add_pats(chat_id, pats_valid)   # TAMBAH (merge) ke pool
    reg = register_ke_router(api_key, pats_valid)      # daftarkan yang baru ke router

    teks_out = "\n".join([
        f"📋 *Ringkasan {len(pats)} PAT masuk*",
        "",
        ringkas,
        "",
        f"➕ Total PAT di pool kamu: *{len(semua_pats)}*",
        "",
        f"🔗 *Base URL* (tap utk salin):",
        f"`{BASE_URL}`",
        f"🔑 *API key* (tap utk salin):",
        f"`{api_key}`",
        "",
        f"✅ {reg.get('masuk', 0) + reg.get('diklaim', 0)} PAT ditambahkan ke router.",
        "_PAT bisa ditambah kapan saja (kirim .txt lagi = nambah, bukan ganti)._",
    ])
    kirim(chat_id, teks_out)


def proses(msg: dict):
    chat = (msg.get("chat") or {}).get("id")
    if not chat:
        return
    tipe_chat = (msg.get("chat") or {}).get("type", "private")
    privat = (tipe_chat == "private")   # API key hanya utk chat pribadi (anti bocor)
    text = (msg.get("text") or "").strip()
    doc = msg.get("document")

    if text.startswith("/start"):
        handle_start(chat)
    elif text.startswith("/models"):
        handle_models(chat)
    elif text.startswith("/status"):
        if not privat:
            kirim(chat, "⚠️ Cek PAT & API key hanya lewat *chat pribadi* (biar key tidak bocor).")
            return
        handle_status(chat)
    elif doc:
        if not privat:
            kirim(chat, "⚠️ Upload PAT hanya lewat *chat pribadi* (biar API key tidak bocor).")
            return
        fn = (doc.get("file_name") or "").lower()
        if fn.endswith(".txt") or doc.get("mime_type") in ("text/plain", "application/octet-stream"):
            isi = unduh_file(doc.get("file_id"))
            if isi is None:
                kirim(chat, "Gagal mengunduh file.")
            else:
                handle_patfile(chat, isi)
        else:
            kirim(chat, "Kirim file *.txt* berisi list PAT (`pt-...` per baris).")
    elif text.startswith("/"):
        kirim(chat, "Perintah tidak dikenal. Coba /start.")


def utama():
    # Auto-sync saat start: pastikan semua PAT di store terdaftar di router
    # (menambal kasus PAT di-upload sebelum fitur register ada, atau router
    # sempat restart). Tanpa ini request bisa "No available accounts".
    try:
        for tg, u in store.semua().items():
            pats = u.get("pats") or []
            key = u.get("api_key")
            if pats and key:
                register_ke_router(key, pats)
        print("[bot] sinkron PAT -> router selesai")
    except Exception as e:
        print("[bot] sinkron gagal (tak fatal):", e)
    print(f"[bot] @qoder_router_pixestlab_bot siap | base URL: {BASE_URL}")
    offset = None
    while True:
        try:
            params = {"timeout": 50}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{API}/getUpdates", params=params, timeout=60)
            d = r.json()
            for upd in d.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                if msg:
                    try:
                        proses(msg)
                    except Exception as e:
                        print("[bot] error proses:", e)
        except KeyboardInterrupt:
            print("[bot] stop"); break
        except Exception as e:
            print("[bot] polling error:", e); time.sleep(3)


if __name__ == "__main__":
    utama()
