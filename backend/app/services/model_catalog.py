"""Canonical Qoder model catalog used by routing, UI and public APIs.

Credit factors and capabilities mirror the current Qoder catalog-v6. They are
multipliers, not fixed per-request prices; upstream billing and request shape
can change the final credit charge reported by upstream.
"""
from __future__ import annotations

from typing import Any


MODEL_CATALOG: tuple[dict[str, Any], ...] = (
    # Tier routing (internal — tidak diiklankan di /v1/models; "auto" = fallback).
    {"key": "auto", "name": "Auto", "credit_factor": 1.0, "is_reasoning": False, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [], "kind": "tier"},
    {"key": "ultimate", "name": "Ultimate", "credit_factor": 1.6, "is_reasoning": True, "is_vision": True, "max_input_tokens": 1_000_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "tier"},
    {"key": "performance", "name": "Performance", "credit_factor": 1.1, "is_reasoning": False, "is_vision": True, "max_input_tokens": 1_000_000, "context_windows": [272_000, 400_000, 1_000_000], "kind": "tier"},
    {"key": "efficient", "name": "Efficient", "credit_factor": 0.3, "is_reasoning": False, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [], "kind": "tier"},
    {"key": "lite", "name": "Lite", "credit_factor": 0.0, "is_reasoning": False, "is_vision": False, "max_input_tokens": 180_000, "context_windows": [], "kind": "tier"},
    # 11 model nyata sesuai Qoder (2 bawaan: Sonus + Cantus). ID = slug name.
    {"key": "smodel", "name": "Sonus", "credit_factor": 3.2, "is_reasoning": True, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "cmodel", "name": "Cantus", "credit_factor": 3.2, "is_reasoning": True, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "qmodel_38max", "name": "Qwen3.8-Max", "credit_factor": 0.5, "is_reasoning": True, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "qfmodel", "name": "Qwen3.8-Flash", "credit_factor": 0.1, "is_reasoning": True, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "kmodel_latest", "name": "Kimi-K3.1-Pro", "credit_factor": 0.8, "is_reasoning": False, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "kmodel", "name": "Kimi-K2.8-Preview", "credit_factor": 0.3, "is_reasoning": False, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "gmodel", "name": "GLM-5.3", "credit_factor": 0.6, "is_reasoning": True, "is_vision": True, "max_input_tokens": 180_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "gfmodel", "name": "GLM-5.3-Flash", "credit_factor": 0.05, "is_reasoning": True, "is_vision": True, "max_input_tokens": 1_000_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "dmodel", "name": "DeepSeek-V4-Pro", "credit_factor": 0.8, "is_reasoning": True, "is_vision": True, "max_input_tokens": 1_000_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "dfmodel", "name": "DeepSeek-V4.1-Flash-1017", "credit_factor": 0.3, "is_reasoning": True, "is_vision": True, "max_input_tokens": 1_000_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
    {"key": "mmodel", "name": "MiniMax-M3.1-Flash", "credit_factor": 0.2, "is_reasoning": False, "is_vision": True, "max_input_tokens": 1_000_000, "context_windows": [200_000, 400_000, 1_000_000], "kind": "model"},
)

MODEL_BY_KEY = {entry["key"]: entry for entry in MODEL_CATALOG}
MODEL_KEYS = frozenset(MODEL_BY_KEY)

# Qoder exposes this independently from ``is_reasoning``.  A model such as
# Kimi-K3 is catalogued as non-reasoning while still offering a controllable
# thinking mode.  Keeping the two flags separate prevents the UI from implying
# that Kimi cannot emit thinking blocks.
THINKING_CONFIG_BY_MODEL: dict[str, dict[str, Any]] = {
    # SUMBER: live GET /algo/api/v2/model/list (COSY-signed) — tangkap
    # 2026-10-30 dari Qoder, BUKAN tebakan (harnes/cek-model-list.mjs).
    # Tiap model punya sistem effort BERBEDA; jangan disamakan.
    #   efforts       = level yang DITERIMA model (urut low<medium<high<xhigh<max)
    #   default_effort = nilai default model (tanda is_default di respons Qoder)
    #   can_disable   = ada thinking_config.disabled => bisa mati total (on/off);
    #                   kalau False = thinking selalu hidup, cuma ganti level.
    "ultimate":      {"efforts": ["low", "medium", "high", "xhigh", "max"], "default_effort": "high",   "can_disable": False},
    "qmodel_38max":  {"efforts": ["low", "medium", "xhigh"],                 "default_effort": "medium", "can_disable": True},
    "qfmodel":       {"efforts": ["low", "medium", "xhigh"],                 "default_effort": "medium", "can_disable": True},
    "kmodel_latest": {"efforts": ["low", "high", "max"],                     "default_effort": "high",   "can_disable": False},
    "kmodel":        {"efforts": ["low", "high", "max"],                     "default_effort": "high",   "can_disable": False},
    "gmodel":        {"efforts": ["low", "high", "max"],                     "default_effort": "high",   "can_disable": False},
    "gfmodel":       {"efforts": ["high", "max"],                            "default_effort": "max",    "can_disable": False},
    "dmodel":        {"efforts": ["high", "max"],                            "default_effort": "max",    "can_disable": True},
    "dfmodel":       {"efforts": ["low", "high", "max"],                     "default_effort": "high",   "can_disable": True},
    # Sonus/Cantus TIDAK muncul di model/list utk akun trial (kemungkinan
    # premium/plan-gated). Effort di bawah dari capture BEDAH-REASONING-MATI §1
    # (low,medium,high*,xhigh,max) — bukan karangan, tapi juga bukan live.
    "cmodel":        {"efforts": ["low", "medium", "high", "xhigh", "max"], "default_effort": "high",   "can_disable": False},
    "smodel":        {"efforts": ["low", "medium", "high", "xhigh", "max"], "default_effort": "high",   "can_disable": False},
}
# Model TANPA thinking_config sama sekali (is_reasoning false, tanpa knob) —
# effort klien diabaikan, jangan kirim thinking switch (auto/efficient/mmodel/...).
THINKING_NONE_MODELS = {"auto", "efficient", "mmodel", "performance", "lite",
                        "qmodel", "qmodel_latest"}


def context_length_of(entry: dict[str, Any]) -> int:
    """Largest advertised context window, else the catalog max_input_tokens."""
    windows = entry.get("context_windows") or []
    if windows:
        return int(max(windows))
    return int(entry["max_input_tokens"])


def public_model_catalog() -> list[dict[str, Any]]:
    """Return detached JSON-safe rows so callers cannot mutate constants."""
    rows: list[dict[str, Any]] = []
    for entry in MODEL_CATALOG:
        thinking = THINKING_CONFIG_BY_MODEL.get(str(entry["key"]))
        row = {
            key: list(value) if isinstance(value, list) else value
            for key, value in entry.items()
        }
        row["context_length"] = context_length_of(entry)
        row["supports_thinking"] = thinking is not None
        row["thinking_efforts"] = list(thinking["efforts"]) if thinking else []
        row["default_thinking_effort"] = (
            thinking["default_effort"] if thinking else None
        )
        rows.append(row)
    return rows
