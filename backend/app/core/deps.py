"""deps.py — dependency auth utk endpoint management (/api/*).

require_admin: wajib header `Authorization: Bearer <admin_key>`.
Admin key dibaca dari FILE admin.key (bukan env — pydantic bentrok dgn env var).
Mencegah siapa pun mencuri PAT lewat /api/accounts/{id}/pat. (audit 2026-10-30)
"""
from __future__ import annotations

import os
from fastapi import Header, HTTPException

_KEY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "admin.key")


def _admin_key() -> str:
    try:
        return open(_KEY_FILE).read().strip()
    except Exception:
        return ""


async def require_admin(authorization: str = Header(default="")) -> None:
    key = _admin_key()
    if not key:
        raise HTTPException(status_code=403, detail="Admin key belum dikonfigurasi (admin.key)")
    got = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    if got != key:
        raise HTTPException(status_code=401, detail="Admin key tidak valid")
