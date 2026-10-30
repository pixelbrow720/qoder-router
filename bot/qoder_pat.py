"""qoder_pat.py — cek 1 PAT Qoder: sisa kredit, total, tanggal berakhir, plan.

Endpoint (sama dgn backend router, openapi.qoder.sh):
  POST /api/v1/jobToken/exchange  {personal_token} -> token
  GET  /api/v2/user/plan          -> plan tier / nama / end date
  GET  /api/v2/quota/usage        -> total/used/remaining/isQuotaExceeded/expires
  GET  /api/v1/userinfo           -> uid / email

Dipakai bot Telegram utk menampilkan "ada berapa kredit & kapan berakhirnya".
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

QODER_BASE = "https://openapi.qoder.sh"
EXCHANGE = f"{QODER_BASE}/api/v1/jobToken/exchange"
PLAN = f"{QODER_BASE}/api/v2/user/plan"
QUOTA = f"{QODER_BASE}/api/v2/quota/usage"
USERINFO = f"{QODER_BASE}/api/v1/userinfo"

HDR = {
    "Content-Type": "application/json",
    "User-Agent": "qoder-router-bot/1.0",
    "Cosy-Version": "1.1.81",
}


def _job_token(pat: str, timeout=20) -> str | None:
    try:
        r = requests.post(EXCHANGE, json={"personal_token": pat},
                          headers=HDR, timeout=timeout)
        if r.status_code != 200:
            return None
        d = r.json() or {}
        return d.get("token") or d.get("device_token") or d.get("access_token")
    except Exception:
        return None


def _get(url: str, token: str, timeout=20) -> dict:
    try:
        r = requests.get(url, headers={**HDR, "Authorization": f"Bearer {token}"}, timeout=timeout)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def _ms_to_date(v) -> str | None:
    if v is None:
        return None
    try:
        n = float(v)
        if n > 1e11:   # milidetik
            n /= 1000.0
        if n <= 0 or n > 4e9:   # bukan timestamp valid (mis. 9999-12-31)
            return None
        return datetime.fromtimestamp(n).strftime("%Y-%m-%d")
    except Exception:
        return None


def cek_pat(pat: str) -> dict:
    """Kembalikan dict info PAT: ok, credit, expiry, plan, email, uid, alasan."""
    pat = pat.strip()
    out = {"pat": pat, "ok": False}
    if not pat.startswith("pt-"):
        out["alasan"] = "format bukan pt-"
        return out
    token = _job_token(pat)
    if not token:
        out["alasan"] = "token tidak valid / login gagal"
        return out

    plan = _get(PLAN, token)
    quota = _get(QUOTA, token)
    info = _get(USERINFO, token)

    # --- plan --- (struktur asli: plan_tier_name / user_type / end_date)
    tier = plan.get("user_type") or plan.get("plan_tier") or plan.get("planTier") or ""
    plan_name = plan.get("plan_tier_name") or plan.get("planName") or plan.get("plan_name") or ""
    plan_end = plan.get("end_date") or plan.get("planEndDate") or plan.get("expiresAt")

    # --- quota ---
    uq = quota.get("userQuota") if isinstance(quota.get("userQuota"), dict) else {}
    total = uq.get("total")
    used = uq.get("used")
    remaining = uq.get("remaining")
    if remaining is None and isinstance(total, (int, float)):
        remaining = float(total) - (float(used) if isinstance(used, (int, float)) else 0.0)
    exceeded = bool(quota.get("isQuotaExceeded"))
    expires = quota.get("expiresAt") or quota.get("expires_at")

    out.update({
        "ok": True,
        "uid": info.get("id") or "",
        "email": info.get("email") or "",
        "plan_tier": str(tier),
        "plan_name": str(plan_name),
        "quota_total": float(total) if isinstance(total, (int, float)) else None,
        "quota_used": float(used) if isinstance(used, (int, float)) else None,
        "quota_remaining": float(remaining) if isinstance(remaining, (int, float)) else None,
        "is_quota_exceeded": exceeded,
        "expired": _ms_to_date(expires) or _ms_to_date(plan_end),
        "raw_expired": expires or plan_end,
    })
    # vonis sederhana
    if exceeded or (out["quota_remaining"] is not None and out["quota_remaining"] <= 0):
        out["status"] = "HABIS"
    elif out["quota_remaining"] is not None:
        out["status"] = "AKTIF"
    else:
        out["status"] = "TIDAK DIKETAHUI"
    return out


def ringkas(p: dict) -> str:
    """Baris ringkas utk ditampilkan di Telegram."""
    if not p.get("ok"):
        return f"❌ `{p['pat'][:18]}…` — {p.get('alasan')}"
    rem = p.get("quota_remaining")
    tot = p.get("quota_total")
    rem_s = f"{rem:.0f}" if rem is not None else "?"
    tot_s = f"{tot:.0f}" if tot is not None else "?"
    exp = p.get("expired") or "?"
    return (f"✅ `{p['pat'][:18]}…` — {p.get('plan_name') or p.get('plan_tier') or '?'} | "
            f"kredit **{rem_s}/{tot_s}** | s/d **{exp}** | {p.get('status')}")


if __name__ == "__main__":
    import sys
    for a in sys.argv[1:]:
        print(ringkas(cek_pat(a)))
