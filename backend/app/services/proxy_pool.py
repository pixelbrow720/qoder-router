"""Rotasi proxy utk request upstream ke Qoder.

Tujuan: sebar request ke banyak IP (proxy datacenter) supaya TIDAK menumpuk di
1 IP VPS yang mudah kena throttle Qoder ("replaying too fast makes the throttle
worse", lihat 9router open-sse/shared/qoder/queue.js).  Dengan rotasi, tiap
request keluar dari IP berbeda -> throttle tidak menumpuk di satu IP.

Sumber proxy (salah satu):
  * env QODER_PROXIES  = "host:port:user:pass,host:port:user:pass,..."
  * env QODER_PROXY_FILE = path file (satu baris per proxy, format sama)
Format tiap baris:  host:port:user:pass   ATAU   http://user:pass@host:port
Bila kosong -> request langsung (tanpa proxy), perilaku lama.
"""
from __future__ import annotations

import itertools
import os
from typing import Optional

_proxies: list[str] = []
_cycle: Optional[itertools.cycle] = None
_loaded = False


def _parse_line(line: str) -> Optional[str]:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("http://") or line.startswith("https://"):
        return line
    parts = line.split(":")
    if len(parts) == 4:
        host, port, user, pw = parts
        return f"http://{user}:{pw}@{host}:{port}"
    return None


def _load() -> None:
    global _proxies, _cycle, _loaded
    lines: list[str] = []
    raw = os.getenv("QODER_PROXIES", "")
    if raw:
        lines.extend(raw.split(","))
    path = os.getenv("QODER_PROXY_FILE", "")
    if path and os.path.exists(path):
        with open(path) as f:
            lines.extend(f.readlines())
    parsed = [p for p in (_parse_line(l) for l in lines) if p]
    _proxies = parsed
    _cycle = itertools.cycle(_proxies) if _proxies else None
    _loaded = True


def next_proxy() -> Optional[str]:
    """URL proxy berikutnya (round-robin), atau None bila tak ada proxy."""
    global _loaded
    if not _loaded:
        _load()
    if _cycle is None:
        return None
    return next(_cycle)


def count() -> int:
    if not _loaded:
        _load()
    return len(_proxies)
