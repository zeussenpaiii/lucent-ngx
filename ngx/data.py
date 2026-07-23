"""
data.py — Cached data access layer.

The rest of the app talks to the dataset only through here, so the storage
format (CSV today, could be SQLite/API later) stays swappable. All numbers are
coerced to floats once; ratios keep their stored (average-balance) values and
are never silently recomputed.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from . import config

# Use Streamlit's cache when running in the app; fall back to a plain lru_cache
# so the module is importable/testable with bare Python too.
try:
    import streamlit as st
    _cache = st.cache_data
except Exception:  # pragma: no cover
    from functools import lru_cache

    def _cache(func=None, **_kw):
        def wrap(f):
            return lru_cache(maxsize=None)(f)
        return wrap(func) if func else wrap


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / config.DATA_FILE

# All numeric metric columns to coerce.
_NUMERIC = list(config.METRICS.keys())
_META = ["company", "type", "year", "currency", "sector", "pages",
         "balance_check", "status", "status_reason", "correction_log"]


@_cache
def load() -> pd.DataFrame:
    """Load and clean the shipped 2021–2025 dataset (cached)."""
    df = pd.read_csv(DATA_PATH)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    for col in _NUMERIC:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@_cache
def companies() -> list[str]:
    """Raw company keys, ordered by their display name."""
    raw = load()["company"].unique().tolist()
    return sorted(raw, key=lambda c: config.display_name(c).lower())


@_cache
def sectors() -> list[str]:
    return sorted(load()["sector"].unique().tolist())


@_cache
def company_sector(company: str) -> str:
    df = load()
    rows = df[df["company"] == company]
    return rows["sector"].iloc[0] if len(rows) else ""


@_cache
def sector_members(sector: str) -> list[str]:
    df = load()
    raw = df[df["sector"] == sector]["company"].unique().tolist()
    return sorted(raw, key=lambda c: config.display_name(c).lower())


def company_frame(company: str) -> pd.DataFrame:
    """All rows for one company, sorted by year ascending."""
    df = load()
    return df[df["company"] == company].sort_values("year").reset_index(drop=True)


def years_for(company: str) -> list[int]:
    return [int(y) for y in company_frame(company)["year"].tolist()]


def latest_year(company: str) -> int | None:
    ys = years_for(company)
    return max(ys) if ys else None


def series(company: str, metric: str) -> dict[int, float]:
    """{year: value} for a metric, missing years omitted."""
    df = company_frame(company)
    if metric not in df.columns:
        return {}
    out = {}
    for _, row in df.iterrows():
        v = row[metric]
        if pd.notna(v):
            out[int(row["year"])] = float(v)
    return out


def value(company: str, metric: str, year: int) -> float | None:
    df = company_frame(company)
    hit = df[df["year"] == year]
    if not len(hit) or metric not in df.columns:
        return None
    v = hit[metric].iloc[0]
    return float(v) if pd.notna(v) else None


def latest_value(company: str, metric: str) -> tuple[float | None, int | None]:
    """Most recent non-null value for a metric and the year it came from."""
    s = series(company, metric)
    if not s:
        return None, None
    y = max(s)
    return s[y], y


@_cache
def sector_median(sector: str, metric: str, year: int) -> float | None:
    df = load()
    if metric not in df.columns:
        return None
    vals = df[(df["sector"] == sector) & (df["year"] == year)][metric].dropna()
    return float(vals.median()) if len(vals) else None


def provenance(company: str, year: int) -> dict:
    """Extraction/verification metadata for one filing (for the confidence badge)."""
    df = company_frame(company)
    hit = df[df["year"] == year]
    if not len(hit):
        return {}
    r = hit.iloc[0]

    def _s(col: str) -> str:
        v = r.get(col, "")
        return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)

    return {k: _s(k) for k in ["type", "status", "status_reason", "balance_check", "pages", "correction_log"]}


@_cache
def sector_stats(year: int | None = None) -> list[dict]:
    """Per-sector aggregates for one year, richest sector first (by revenue)."""
    df = load()
    if year is None:
        year = int(df["year"].max())
    rows = df[df["year"] == year]
    out = []
    for sec, g in rows.groupby("sector"):
        rev = g["gross_earnings"]
        top_i = rev.idxmax() if rev.notna().any() else None
        out.append({
            "sector": sec,
            "n": int(g["company"].nunique()),
            "revenue": float(rev.sum()) if rev.notna().any() else None,
            "pat": float(g["profit_after_tax"].sum()) if g["profit_after_tax"].notna().any() else None,
            "median_roe": float(g["roe"].median()) if g["roe"].notna().any() else None,
            "median_margin": float(g["net_margin"].median()) if g["net_margin"].notna().any() else None,
            "top_company": g.loc[top_i, "company"] if top_i is not None else None,
        })
    out.sort(key=lambda r: (r["revenue"] is not None, r["revenue"] or 0), reverse=True)
    return out


@_cache
def latest_frame(year: int | None = None):
    """Rows for a single year (defaults to the latest)."""
    df = load()
    if year is None:
        year = int(df["year"].max())
    return df[df["year"] == year].copy()


@_cache
def dataset_summary() -> dict:
    df = load()
    return {
        "companies": df["company"].nunique(),
        "sectors": df["sector"].nunique(),
        "rows": len(df),
        "year_min": int(df["year"].min()),
        "year_max": int(df["year"].max()),
    }
