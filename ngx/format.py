"""
format.py — Consistent, finance-grade formatting for every number shown.

Values in the dataset are absolute Naira (e.g. 29_957_525_000_000 = ₦29.96trn)
and ratios are decimals (0.2601 = 26.0%). Everything user-facing goes through
here so the app never leaks a raw float.
"""
from __future__ import annotations
import math
from .config import METRICS

DASH = "—"  # shown for any missing / not-reported value


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def naira(v, *, sign: bool = False) -> str:
    """Auto-scaled Naira: ₦29.96trn, ₦456.7bn, ₦89.0m, ₦12.3k."""
    if _is_missing(v):
        return DASH
    v = float(v)
    neg = v < 0
    a = abs(v)
    if a >= 1e12:
        s = f"₦{a/1e12:.2f}trn"
    elif a >= 1e9:
        s = f"₦{a/1e9:.2f}bn"
    elif a >= 1e6:
        s = f"₦{a/1e6:.1f}m"
    elif a >= 1e3:
        s = f"₦{a/1e3:.1f}k"
    else:
        s = f"₦{a:.0f}"
    if neg:
        return f"({s})"
    return f"+{s}" if sign else s


def count(v) -> str:
    """Plain scaled number (shares/units), no currency."""
    if _is_missing(v):
        return DASH
    v = float(v)
    a = abs(v)
    if a >= 1e9:
        return f"{v/1e9:.2f}bn"
    if a >= 1e6:
        return f"{v/1e6:.1f}m"
    if a >= 1e3:
        return f"{v/1e3:.1f}k"
    return f"{v:.0f}"


def pct(v, *, digits: int = 1, sign: bool = False) -> str:
    """Decimal ratio -> percentage. 0.2601 -> 26.0%."""
    if _is_missing(v):
        return DASH
    v = float(v) * 100
    return f"{v:+.{digits}f}%" if sign else f"{v:.{digits}f}%"


def multiple(v, *, digits: int = 2) -> str:
    """Ratio shown as a multiple. 1.32 -> 1.32x."""
    if _is_missing(v):
        return DASH
    return f"{float(v):.{digits}f}x"


def per_share(v) -> str:
    """Per-share amounts in Naira with kobo. 32.87 -> ₦32.87."""
    if _is_missing(v):
        return DASH
    v = float(v)
    return f"(₦{abs(v):.2f})" if v < 0 else f"₦{v:.2f}"


def metric(key: str, v) -> str:
    """Format a value using the registry's rule for that metric key."""
    fmt = METRICS.get(key, {}).get("fmt", "naira")
    return {
        "naira": naira,
        "pct": pct,
        "x": multiple,
        "per_share": per_share,
        "count": count,
    }.get(fmt, naira)(v)


def delta_pct(new, old) -> float | None:
    """Signed fractional change new/old-1, guarding zero/sign edge cases."""
    if _is_missing(new) or _is_missing(old):
        return None
    old = float(old)
    if old == 0:
        return None
    # If the base is negative, a naive ratio flips sign misleadingly.
    return (float(new) - old) / abs(old)
