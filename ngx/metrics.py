"""
metrics.py — Derived analytics computed on top of the stored data.

Deliberately small and defensive: every helper tolerates missing years and
non-positive bases, because the dataset has gaps (e.g. Chapel Hill = 3 years).
Stored ratios (ROE/ROA/margins) are used as-is elsewhere; this module only adds
growth/aggregation views on top.
"""
from __future__ import annotations
from functools import lru_cache
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


@lru_cache(maxsize=None)
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


@lru_cache(maxsize=None)
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


@lru_cache(maxsize=None)
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


@lru_cache(maxsize=None)
def dividend_profile(company: str) -> dict:
    """Everything the dividend tracker needs for one company.

    Note: dividend *yield* is deliberately absent — it needs a share price, and
    this dataset is fundamentals-only. Everything here comes from declared DPS,
    payout ratio and share count.
    """
    dps = data.series(company, "dividend_per_share")
    years = data.years_for(company)
    paid = {y: v for y, v in dps.items() if v and v > 0}
    latest_dps, latest_yr = data.latest_value(company, "dividend_per_share")
    shares, _ = data.latest_value(company, "shares_outstanding")
    payout, _ = data.latest_value(company, "payout_ratio")
    eps, _ = data.latest_value(company, "eps_basic")

    # consecutive years paid, counting back from the most recent year
    streak = 0
    for y in sorted(years, reverse=True):
        if paid.get(y):
            streak += 1
        else:
            break

    growth = cagr(paid) if len(paid) >= 2 else None
    total_payout = (latest_dps * shares) if (latest_dps and shares) else None
    return {
        "company": company,
        "dps": dps,
        "latest_dps": latest_dps if (latest_dps and latest_dps > 0) else None,
        "latest_year": latest_yr,
        "years_paid": len(paid),
        "years_total": len(years),
        "streak": streak,
        "consistent": len(paid) == len(years) and len(years) >= 3,
        "dps_cagr": growth,
        "payout": payout,
        "eps": eps,
        "total_payout": total_payout,
        "covered": (payout is not None and 0 < payout <= 1.0),
    }


@lru_cache(maxsize=None)
def dividend_table() -> list[dict]:
    """Dividend profile for every company, biggest total payout first."""
    rows = [dividend_profile(c) for c in data.companies()]
    rows.sort(key=lambda r: (r["total_payout"] is not None, r["total_payout"] or 0), reverse=True)
    return rows


@lru_cache(maxsize=None)
def dividend_market_summary() -> dict:
    rows = dividend_table()
    payers = [r for r in rows if r["latest_dps"]]
    total = sum(r["total_payout"] for r in payers if r["total_payout"])
    payouts = sorted(r["payout"] for r in payers if r["payout"] is not None)
    med_payout = payouts[len(payouts) // 2] if payouts else None
    return {
        "payers": len(payers),
        "total_companies": len(rows),
        "total_declared": total,
        "median_payout": med_payout,
        "consistent": sum(1 for r in rows if r["consistent"]),
    }


@lru_cache(maxsize=None)
def rank_in_sector(company: str, metric: str, year: int,
                   higher_is_better: bool = True) -> tuple[int, int] | None:
    """(rank, peers) for a company's metric within its sector. 1 = best."""
    sector = data.company_sector(company)
    peers = []
    for c in data.sector_members(sector):
        v = data.value(c, metric, year)
        if v is not None:
            peers.append((c, v))
    if len(peers) < 3:
        return None
    peers.sort(key=lambda r: r[1], reverse=higher_is_better)
    for i, (c, _) in enumerate(peers, start=1):
        if c == company:
            return i, len(peers)
    return None


@lru_cache(maxsize=None)
def sector_median_cagr(sector: str, metric: str) -> float | None:
    """Median growth rate across a sector — the bar a company should beat."""
    vals = []
    for c in data.sector_members(sector):
        g = cagr(data.series(c, metric))
        if g is not None:
            vals.append(g)
    if not vals:
        return None
    vals.sort()
    return vals[len(vals) // 2]


def turnaround_year(company: str) -> int | None:
    """Year the company swung from loss to profit (most recent such flip)."""
    s = data.series(company, "profit_after_tax")
    ys = sorted(s)
    flip = None
    for i in range(1, len(ys)):
        if s[ys[i - 1]] < 0 <= s[ys[i]]:
            flip = ys[i]
    return flip


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
