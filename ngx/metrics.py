"""
metrics.py — Derived analytics computed on top of the stored data.

Deliberately small and defensive: every helper tolerates missing years and
non-positive bases, because the dataset has gaps (e.g. Chapel Hill = 3 years).
Stored ratios (ROE/ROA/margins) are used as-is elsewhere; this module only adds
growth/aggregation views on top.
"""
from __future__ import annotations
import math

from . import data


def cagr(s: dict[int, float]) -> float | None:
    """Compound annual growth rate across the span of a {year: value} series."""
    if not s or len(s) < 2:
        return None
    ys = sorted(s)
    start, end = s[ys[0]], s[ys[-1]]
    years = ys[-1] - ys[0]
    # CAGR is undefined when the base is non-positive or sign flips.
    if start is None or end is None or start <= 0 or end <= 0 or years <= 0:
        return None
    return (end / start) ** (1 / years) - 1


def total_growth(s: dict[int, float]) -> float | None:
    """Simple start->end fractional change (works when CAGR can't)."""
    if not s or len(s) < 2:
        return None
    ys = sorted(s)
    start, end = s[ys[0]], s[ys[-1]]
    if start is None or start == 0:
        return None
    return (end - start) / abs(start)


def yoy(s: dict[int, float]) -> dict[int, float | None]:
    """Year-on-year fractional change for each year after the first."""
    out: dict[int, float | None] = {}
    ys = sorted(s)
    for i in range(1, len(ys)):
        prev, cur = s[ys[i - 1]], s[ys[i]]
        out[ys[i]] = None if prev in (None, 0) else (cur - prev) / abs(prev)
    return out


def trend_direction(s: dict[int, float]) -> str:
    """Coarse label for a series: 'rising', 'falling', 'volatile', 'flat'."""
    if not s or len(s) < 2:
        return "n/a"
    ys = sorted(s)
    diffs = [s[ys[i]] - s[ys[i - 1]] for i in range(1, len(ys))]
    ups = sum(1 for d in diffs if d > 0)
    downs = sum(1 for d in diffs if d < 0)
    g = total_growth(s) or 0
    if ups and not downs:
        return "rising"
    if downs and not ups:
        return "falling"
    if abs(g) < 0.05:
        return "flat"
    return "volatile" if abs(g) < 0.15 else ("rising" if g > 0 else "falling")


def sector_percentile(company: str, sector: str, metric: str, year: int) -> float | None:
    """Where a company's metric sits within its sector that year (0–100)."""
    df = data.load()
    if metric not in df.columns:
        return None
    peers = df[(df["sector"] == sector) & (df["year"] == year)][["company", metric]].dropna()
    if len(peers) < 3:
        return None
    row = peers[peers["company"] == company]
    if not len(row):
        return None
    v = float(row[metric].iloc[0])
    below = (peers[metric] < v).sum()
    return round(100 * below / (len(peers) - 1)) if len(peers) > 1 else None


def vs_sector_median(company: str, sector: str, metric: str, year: int) -> tuple[float | None, float | None]:
    """(company value, sector median) for a metric/year."""
    return data.value(company, metric, year), data.sector_median(sector, metric, year)


def company_cagr(company: str, metric: str) -> float | None:
    return cagr(data.series(company, metric))


def biggest_movers(metric: str = "gross_earnings", min_years: int = 3) -> list[tuple[str, float, float | None]]:
    """(company, CAGR, latest value) for every company, best growth first."""
    rows = []
    for c in data.companies():
        s = data.series(c, metric)
        g = cagr(s)
        if g is not None and len(s) >= min_years:
            rows.append((c, g, data.latest_value(c, metric)[0]))
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows


def margin_movers() -> list[tuple[str, float]]:
    """(company, net-margin change first->last), biggest expansion first."""
    rows = []
    for c in data.companies():
        s = data.series(c, "net_margin")
        if len(s) >= 3:
            ys = sorted(s)
            rows.append((c, s[ys[-1]] - s[ys[0]]))
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows


def market_summary() -> dict:
    """Headline, market-level facts for the home hero."""
    df = data.load()
    yN = int(df["year"].max())
    latest = df[df["year"] == yN]
    combined_rev = float(latest["gross_earnings"].sum())
    roe_vals = latest["roe"].dropna()
    pat_vals = latest["profit_after_tax"].dropna()
    growths = [g for _, g, _ in biggest_movers("gross_earnings")]
    median_growth = sorted(growths)[len(growths) // 2] if growths else None
    profitable = int((pat_vals > 0).sum())
    return {
        "year": yN,
        "combined_revenue": combined_rev,
        "median_roe": float(roe_vals.median()) if len(roe_vals) else None,
        "median_growth": median_growth,
        "profitable": profitable,
        "total_reporting": int(pat_vals.shape[0]),
    }


def equity_ratio(company: str, year: int) -> float | None:
    eq = data.value(company, "total_equity", year)
    ta = data.value(company, "total_assets", year)
    return (eq / ta) if (eq is not None and ta) else None


def roe_not_meaningful(company: str, year: int) -> bool:
    """True when equity is near-zero/negative, so ROE is not a meaningful figure."""
    er = equity_ratio(company, year)
    return er is not None and er < 0.05


def margin_caution(company: str, year: int) -> str | None:
    """Flag a net margin inflated by one-off / non-operating gains.

    A net margin above 100% (profit exceeds revenue) is a red flag that earnings
    include large non-operating items — e.g. Aradel FY2025, where ~73% of pre-tax
    profit was a bargain-purchase / translation gain from acquisitions.
    """
    nm = data.value(company, "net_margin", year)
    rev = data.value(company, "gross_earnings", year)
    pat = data.value(company, "profit_after_tax", year)
    if (nm is not None and nm > 1.0) or (rev and pat and pat > rev):
        return "Net margin exceeds 100% — profit is inflated by one-off/non-operating gains; operating margin is the truer guide"
    return None


def roe_caution(company: str, year: int, roe: float | None = None) -> str | None:
    """Short caution if a ROE should be read with care, else None.

    Two cases the dataset actually contains: (1) a near-zero equity base makes
    ROE meaningless (e.g. Nestlé, FX-depleted equity); (2) an unusually high ROE
    that — whether from a thin/volatile equity base or a genuine blowout year —
    should be read alongside ROA rather than taken at face value.
    """
    if roe is None:
        roe = data.value(company, "roe", year)
    if roe_not_meaningful(company, year):
        return "ROE not meaningful — near-zero equity base; use ROA"
    if roe is not None and roe > 0.75:
        return "Unusually high for a single year — read alongside ROA"
    return None
