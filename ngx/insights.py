"""
insights.py — "What stands out": comparative, non-obvious findings.

The Narrative Engine describes a company; this module tries to say something a
reader could NOT get by glancing at the table — how it ranks against its actual
sector peers, where a trend diverges from the pack, and which numbers are traps.

Each insight is (weight, tone, text); higher weight = more notable. Everything
is computed from the dataset, so it stays as grounded as the rest of the app.
"""
from __future__ import annotations
from functools import lru_cache

from . import data, metrics
from .config import display_name
from . import format as fmt

POS, NEG, WARN, INFO = "pos", "neg", "warn", "info"


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


@lru_cache(maxsize=None)
def for_company(company: str) -> list[tuple[str, str]]:
    """Ranked list of (tone, text) insights for a company."""
    sector = data.company_sector(company)
    yr = data.latest_year(company)
    out: list[tuple[float, str, str]] = []
    if yr is None:
        return []

    rev = data.series(company, "gross_earnings")
    pat = data.series(company, "profit_after_tax")
    rev_cagr = metrics.cagr(rev)
    pat_cagr = metrics.cagr(pat)

    # --- size / rank within sector -----------------------------------------
    r = metrics.rank_in_sector(company, "gross_earnings", yr)
    if r:
        rank, n = r
        if rank == 1:
            out.append((9, POS, f"Largest {sector.lower()} company on the exchange by revenue."))
        elif rank <= 3:
            out.append((6, INFO, f"{_ordinal(rank)} largest of {n} {sector.lower()} companies by revenue."))

    # --- growth vs the sector bar -------------------------------------------
    med = metrics.sector_median_cagr(sector, "gross_earnings")
    if rev_cagr is not None and med is not None and med > 0:
        ratio = rev_cagr / med
        if ratio >= 1.5:
            out.append((9, POS, f"Revenue grew {fmt.pct(rev_cagr)} a year — {ratio:.1f}× the "
                                f"{sector.lower()} median of {fmt.pct(med)}."))
        elif ratio <= 0.6:
            out.append((8, NEG, f"Revenue grew {fmt.pct(rev_cagr)} a year, well behind the "
                                f"{sector.lower()} median of {fmt.pct(med)}."))

    # --- profit vs revenue divergence ---------------------------------------
    if rev_cagr is not None and pat_cagr is not None:
        if pat_cagr > rev_cagr + 0.10:
            out.append((7, POS, "Profit is compounding faster than revenue — margins are widening, "
                                "not just the top line."))
        elif rev_cagr > 0.10 > pat_cagr:
            out.append((8, NEG, "Revenue is growing but profit is not — growth is being eaten by "
                                "costs, finance charges or FX."))

    # --- returns rank --------------------------------------------------------
    roe_rank = metrics.rank_in_sector(company, "roe", yr)
    roe_val = data.value(company, "roe", yr)
    if roe_rank and roe_val is not None and not metrics.roe_not_meaningful(company, yr):
        rank, n = roe_rank
        if rank == 1:
            out.append((9, POS, f"Highest return on equity of the {n} {sector.lower()} companies "
                                f"({fmt.pct(roe_val)})."))
        elif rank >= n - 1:
            out.append((7, NEG, f"Among the weakest returns in its sector — {_ordinal(rank)} of {n} on ROE."))

    # --- margin direction vs peers -------------------------------------------
    nm = data.series(company, "net_margin")
    if len(nm) >= 3:
        ys = sorted(nm)
        chg = nm[ys[-1]] - nm[ys[0]]
        if chg <= -0.05:
            out.append((7, NEG, f"Net margin compressed {fmt.pct(abs(chg))} since {ys[0]} — each naira of "
                                f"sales earns materially less than it used to."))
        elif chg >= 0.05:
            out.append((7, POS, f"Net margin expanded {fmt.pct(chg)} since {ys[0]} — the business is "
                                f"converting sales to profit better than it did."))

    # --- turnaround ----------------------------------------------------------
    flip = metrics.turnaround_year(company)
    if flip:
        out.append((8, POS, f"Swung back to profit in FY{flip} after a loss the year before."))

    # --- balance-sheet traps -------------------------------------------------
    if metrics.roe_not_meaningful(company, yr):
        out.append((10, WARN, "Equity has been nearly wiped out, so ROE and debt ratios look extreme. "
                              "Judge this one on ROA and cash generation instead."))
    mc = metrics.margin_caution(company, yr)
    if mc:
        out.append((10, WARN, "Headline profit is flattered by one-off, non-operating gains — the "
                              "underlying business earns considerably less."))

    # --- cash quality --------------------------------------------------------
    cfo, _ = data.latest_value(company, "net_cash_from_operations")
    pat_last, _ = data.latest_value(company, "profit_after_tax")
    if cfo is not None and pat_last and pat_last > 0:
        conv = cfo / pat_last
        if conv < 0.4:
            out.append((8, WARN, f"Only {fmt.pct(conv)} of reported profit showed up as operating cash — "
                                 f"profit is not converting into money in the bank."))
        elif conv > 1.3:
            out.append((5, POS, "Generates more operating cash than it books as profit — high-quality earnings."))

    # --- dividend behaviour ---------------------------------------------------
    d = metrics.dividend_profile(company)
    if d["consistent"] and d["dps_cagr"] is not None and d["dps_cagr"] > 0.15:
        out.append((7, POS, f"Paid a dividend every year and grew it {fmt.pct(d['dps_cagr'])} a year."))
    elif d["latest_dps"] and d["payout"] and d["payout"] > 1.0:
        out.append((8, WARN, f"Paid out {fmt.pct(d['payout'])} of earnings — more than it earned, which "
                             f"is not sustainable without a profit recovery."))
    elif d["years_paid"] == 0:
        out.append((4, INFO, "Has not declared a dividend in this period."))

    # --- leverage -------------------------------------------------------------
    de, _ = data.latest_value(company, "debt_to_equity")
    if de is not None and not metrics.roe_not_meaningful(company, yr):
        if de > 1.5:
            out.append((6, NEG, f"Carries {fmt.multiple(de)} of debt for every naira of equity — "
                                f"leverage is high for its size."))
        elif de < 0.15:
            out.append((4, POS, "Runs with almost no debt."))

    out.sort(key=lambda r: r[0], reverse=True)
    seen, final = set(), []
    for _, tone, text in out:
        if text in seen:
            continue
        seen.add(text)
        final.append((tone, text))
    return final[:6]
