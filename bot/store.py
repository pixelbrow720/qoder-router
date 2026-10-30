"""store.py — penyimpanan user Telegram -> PAT + API key.

Format JSON sederhana (data/store.json) supaya mudah dibaca juga oleh router:
  {
    "users": {
      "<telegram_id>": {
        "api_key": "sk-qoder-...",
        "pats": ["pt-...", ...],
        "created": 1793...,
        "last_check": {...}
      }
    }
  }

Ditulis oleh bot Telegram, dibaca oleh router utk routing per-API-key.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "data")
STORE = os.path.join(DATA_DIR, "store.json")
_kunci = threading.Lock()


def _muat() -> dict:
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}}


def _simpan(d: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def api_key_untuk(tg_id: int) -> str:
    """Ambil / buat API key utk user Telegram (persisten)."""
    with _kunci:
        d = _muat()
        u = d["users"].setdefault(str(tg_id), {})
        if not u.get("api_key"):
            u["api_key"] = "sk-qoder-" + uuid.uuid4().hex
            u.setdefault("pats", [])
            u["created"] = int(time.time())
        _simpan(d)
        return u["api_key"]


def set_pats(tg_id: int, pats: list[str]):
    with _kunci:
        d = _muat()
        u = d["users"].setdefault(str(tg_id), {})
        u["pats"] = pats
        u.setdefault("api_key", "sk-qoder-" + uuid.uuid4().hex)
        u["updated"] = int(time.time())
        _simpan(d)


def add_pats(tg_id: int, pats: list[str]) -> list[str]:
    """TAMBAH PAT ke pool yang sudah ada (merge, unik) — utk user yang beli
    lagi. Kembalikan daftar PAT gabungan (lama + baru)."""
    with _kunci:
        d = _muat()
        u = d["users"].setdefault(str(tg_id), {})
        lama = list(u.get("pats") or [])
        gabung = list(dict.fromkeys(lama + pats))   # unik, urut, tambah di akhir
        u["pats"] = gabung
        u.setdefault("api_key", "sk-qoder-" + uuid.uuid4().hex)
        u["updated"] = int(time.time())
        _simpan(d)
        return gabung


def get_user(tg_id: int) -> dict:
    d = _muat()
    return d["users"].get(str(tg_id), {})


def semua() -> dict:
    return _muat()["users"]


def cari_dengan_api_key(api_key: str) -> tuple[int | None, list[str]]:
    """Untuk router: cari pemilik API key -> (telegram_id, daftar PAT)."""
    d = _muat()
    for tg, u in d["users"].items():
        if u.get("api_key") == api_key:
            return int(tg), list(u.get("pats") or [])
    return None, []
