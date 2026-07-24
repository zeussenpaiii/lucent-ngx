"""
narrative.py — Deterministic Narrative Engine ("AI Analyst", offline).

Generates the executive-summary sections required by the spec purely from
computed metrics. Because every sentence is templated around numbers that were
just calculated from the dataset, it is grounded by construction: it cannot
state a figure the data doesn't support, and it needs no API or model weights.

Returns an ordered dict of section -> str | list[str].
"""
from __future__ import annotations
from functools import lru_cache

from . import config, data, metrics
from .config import display_name, profile_for
from . import format as fmt


def _fv(company, metric):
    return data.latest_value(company, metric)  # (value, year)


def _pct_word(v, hi, mid, lo_neg_label="a loss"):
    if v is None:
        return None
    if v < 0:
        return lo_neg_label
    if v >= hi:
        return "strong"
    if v >= mid:
        return "moderate"
    return "modest"


@lru_cache(maxsize=None)
def generate(company: str) -> dict:
    name = display_name(company)
    sector = data.company_sector(company)
    profile = profile_for(sector)
    years = data.years_for(company)
    if not years:
        return {"Executive Summary": "No data available for this company."}
    y0, yN = min(years), max(years)
    span = f"{y0}–{yN}"

    rev = data.series(company, "gross_earnings")
    pat = data.series(company, "profit_after_tax")
    rev_cagr = metrics.cagr(rev)
    pat_cagr = metrics.cagr(pat)
    rev_last, rev_yr = _fv(company, "gross_earnings")
    pat_last, _ = _fv(company, "profit_after_tax")

    nm_last, _ = _fv(company, "net_margin")
    nm_series = data.series(company, "net_margin")
    roe_last, roe_yr = _fv(company, "roe")
    roa_last, _ = _fv(company, "roa")
    de_last, _ = _fv(company, "debt_to_equity")
    cr_last, _ = _fv(company, "current_ratio")
    cfo_last, _ = _fv(company, "net_cash_from_operations")
    fcf_last, _ = _fv(company, "free_cash_flow")
    dps = data.series(company, "dividend_per_share")
    payout_last, _ = _fv(company, "payout_ratio")

    roe_med = data.sector_median(sector, "roe", roe_yr) if roe_yr else None

    # Equity-quality check: a collapsed/negative equity base (common after the
    # 2023-24 Naira devaluation) makes ROE and debt-to-equity look extreme and
    # misleading. Detect it so we caveat rather than celebrate those numbers.
    eq_last, _ = _fv(company, "total_equity")
    ta_last, _ = _fv(company, "total_assets")
    equity_ratio = (eq_last / ta_last) if (eq_last is not None and ta_last not in (None, 0)) else None
    neg_equity = eq_last is not None and eq_last <= 0
    thin_equity = equity_ratio is not None and 0 < equity_ratio < 0.05
    distorted = neg_equity or thin_equity
    margin_note = metrics.margin_caution(company, yN)

    out: dict = {}

    # --- Executive Summary --------------------------------------------------
    bits = [f"{name} is a {sector.lower()} company on the NGX."]
    if rev_last is not None:
        bits.append(f"In FY{rev_yr} it reported revenue of {fmt.naira(rev_last)}"
                    + (f" and profit after tax of {fmt.naira(pat_last)}." if pat_last is not None else "."))
    if rev_cagr is not None:
        d = "grew" if rev_cagr > 0 else "declined"
        bits.append(f"Revenue {d} at a {fmt.pct(abs(rev_cagr))} compound annual rate over {span}.")
    if neg_equity:
        bits.append("Return on equity is not meaningful here — shareholders' equity is negative.")
    elif roe_last is not None and (distorted or roe_last > 0.60):
        bits.append(f"Reported return on equity is an unusually high {fmt.pct(roe_last)}, "
                    "distorted by a very thin equity base.")
    elif roe_last is not None:
        q = _pct_word(roe_last, 0.20, 0.10)
        bits.append(f"Return on equity of {fmt.pct(roe_last)} is {q}"
                    + (f", versus a sector median of {fmt.pct(roe_med)}." if roe_med is not None else "."))
    out["Executive Summary"] = " ".join(bits)

    # --- Business Overview --------------------------------------------------
    ov = f"{name} operates in the {sector} sector."
    if profile == "bank":
        dep, _ = _fv(company, "customer_deposits")
        loans, _ = _fv(company, "net_loans_advances")
        if dep is not None:
            ov += f" As a bank, it is funded largely by customer deposits ({fmt.naira(dep)})"
            ov += f" and lends through a net loan book of {fmt.naira(loans)}." if loans is not None else "."
    elif profile == "insurance":
        prem, _ = _fv(company, "net_premium_income")
        if prem is not None:
            ov += f" Its underwriting income (net premiums) was {fmt.naira(prem)} in the latest year."
    ta, _ = _fv(company, "total_assets")
    if ta is not None:
        ov += f" Total assets stand at {fmt.naira(ta)}."
    out["Business Overview"] = ov

    # --- Growth -------------------------------------------------------------
    g = []
    if rev_cagr is not None:
        g.append(f"Revenue compounded at {fmt.pct(rev_cagr)} a year over {span} "
                 f"({metrics.trend_direction(rev)}).")
    elif metrics.total_growth(rev) is not None:
        g.append(f"Revenue moved {fmt.pct(metrics.total_growth(rev), sign=True)} across the period.")
    if pat_cagr is not None:
        g.append(f"Profit after tax compounded at {fmt.pct(pat_cagr)} a year "
                 f"({metrics.trend_direction(pat)}).")
    if rev_cagr is not None and pat_cagr is not None:
        if pat_cagr > rev_cagr:
            g.append("Profit grew faster than revenue, indicating improving efficiency or margins.")
        elif pat_cagr < 0 < rev_cagr:
            g.append("Revenue rose but profit fell — a sign of margin pressure or one-off costs.")
    out["Growth"] = " ".join(g) if g else "Insufficient history to assess growth reliably."

    # --- Profitability ------------------------------------------------------
    p = []
    if nm_last is not None:
        p.append(f"Net margin is {fmt.pct(nm_last)}.")
        if margin_note:
            p.append(margin_note[0].upper() + margin_note[1:] + ".")
        elif len(nm_series) >= 2:
            first = nm_series[min(nm_series)]
            chg = nm_last - first
            direction = "expanded" if chg > 0.005 else ("compressed" if chg < -0.005 else "held broadly steady")
            p.append(f"Margins {direction} over {span}.")
    if roe_last is not None:
        p.append(f"ROE is {fmt.pct(roe_last)} and ROA {fmt.pct(roa_last)}.")
        if distorted:
            p.append("ROE is distorted by a very thin equity base, so ROA is the more reliable "
                     "read on returns here.")
        elif roe_med is not None:
            rel = "above" if roe_last > roe_med else ("below" if roe_last < roe_med else "in line with")
            p.append(f"That places returns {rel} the {sector.lower()} median.")
    out["Profitability"] = " ".join(p) if p else "Profitability metrics are not available."

    # --- Balance Sheet ------------------------------------------------------
    b = []
    tl, _ = _fv(company, "total_liabilities")
    if eq_last is not None:
        b.append(f"Shareholders' equity is {fmt.naira(eq_last)}"
                 + (f" against total liabilities of {fmt.naira(tl)}." if tl is not None else "."))
    if neg_equity:
        b.append("Equity is negative — liabilities exceed assets, a sign of accumulated losses "
                 "(often FX-driven) and balance-sheet stress.")
    elif thin_equity:
        b.append(f"Equity is only {fmt.pct(equity_ratio)} of total assets, so leverage and return "
                 "ratios read as extreme and should be interpreted with caution.")
    elif de_last is not None:
        lev = "conservatively financed" if de_last < 0.5 else ("moderately leveraged" if de_last < 1.5 else "highly leveraged")
        b.append(f"With debt-to-equity of {fmt.multiple(de_last)}, the company is {lev}.")
    if cr_last is not None:
        liq = "comfortable" if cr_last >= 1.5 else ("adequate" if cr_last >= 1 else "tight")
        b.append(f"A current ratio of {fmt.multiple(cr_last)} points to {liq} short-term liquidity.")
    out["Balance Sheet"] = " ".join(b) if b else "Balance-sheet detail is limited for this company."

    # --- Cash Flow ----------------------------------------------------------
    c = []
    if cfo_last is not None:
        c.append(f"Operating cash flow was {fmt.naira(cfo_last)}.")
        if pat_last is not None and pat_last > 0:
            conv = cfo_last / pat_last
            if conv >= 0.9:
                c.append("Cash generation comfortably backs reported profit.")
            elif conv >= 0.4:
                c.append("Cash conversion is partial — some profit is tied up in working capital.")
            else:
                c.append("Reported profit is only weakly backed by operating cash — worth scrutinising.")
    if fcf_last is not None:
        c.append("Free cash flow is positive." if fcf_last >= 0
                 else "Free cash flow is negative, typically reflecting heavy investment.")
    out["Cash Flow"] = " ".join(c) if c else "Cash-flow data is not available for this company."

    # --- Strengths / Weaknesses / Risks ------------------------------------
    strengths, weaknesses, risks = [], [], []
    if rev_cagr is not None and rev_cagr >= 0.15:
        strengths.append(f"Rapid revenue growth ({fmt.pct(rev_cagr)} CAGR over {span}).")
    if not distorted and roe_last is not None and 0.20 <= roe_last <= 0.60:
        strengths.append(f"High return on equity ({fmt.pct(roe_last)}).")
    if not distorted and roe_med is not None and roe_last is not None and roe_last > roe_med:
        strengths.append("Returns above the sector median.")
    if roa_last is not None and roa_last >= 0.10:
        strengths.append(f"Strong return on assets ({fmt.pct(roa_last)}).")
    if not margin_note and nm_last is not None and 0.15 <= nm_last <= 1.0:
        strengths.append(f"Healthy net margin ({fmt.pct(nm_last)}).")
    if len(dps) >= max(2, len(years) - 1) and all(v > 0 for v in dps.values()):
        strengths.append("Consistent dividend payer across the period.")
    if cfo_last is not None and pat_last is not None and pat_last > 0 and cfo_last / pat_last >= 0.9:
        strengths.append("Strong cash backing of earnings.")

    if pat_cagr is not None and pat_cagr < 0:
        weaknesses.append("Declining profit after tax over the period.")
    if nm_last is not None and 0 <= nm_last < 0.05:
        weaknesses.append(f"Thin net margin ({fmt.pct(nm_last)}).")
    if roe_last is not None and 0 <= roe_last < 0.10:
        weaknesses.append(f"Below-average return on equity ({fmt.pct(roe_last)}).")
    if neg_equity:
        weaknesses.append("Negative shareholders' equity — liabilities exceed assets.")
    elif thin_equity:
        weaknesses.append(f"Very thin equity base (equity is {fmt.pct(equity_ratio)} of assets), "
                          "which inflates ROE and leverage ratios.")
    elif de_last is not None and de_last >= 1.5:
        weaknesses.append(f"Elevated leverage (D/E {fmt.multiple(de_last)}).")
    if cr_last is not None and cr_last < 1:
        weaknesses.append(f"Current ratio below 1.0x ({fmt.multiple(cr_last)}) — short-term liquidity is tight.")
    if pat_last is not None and pat_last < 0:
        weaknesses.append("The company is currently loss-making.")

    if metrics.trend_direction(pat) == "volatile":
        risks.append("Earnings have been volatile year to year.")
    if distorted:
        risks.append("A depleted equity base (often FX-driven) makes the balance sheet fragile "
                     "and distorts return and leverage ratios.")
    elif de_last is not None and de_last >= 1.5:
        risks.append("High leverage increases sensitivity to interest rates and refinancing.")
    if profile == "bank":
        risks.append("As a bank, results are exposed to credit quality, FX and regulatory policy.")
    if config.NON_DECEMBER_FYE.get(company):
        risks.append(f"Reports on a non-December year-end ({config.NON_DECEMBER_FYE[company]}); periods aren't directly comparable to December filers.")
    if margin_note:
        risks.append("Latest profit is boosted by one-off/non-operating gains — underlying operating "
                     "profitability is materially lower.")
    risks.append("Figures are historical (2021–2025) and do not reflect events after the last reporting date.")

    out["Strengths"] = strengths or ["No standout strengths flagged by the rules."]
    out["Weaknesses"] = weaknesses or ["No material weaknesses flagged by the rules."]
    out["Risks"] = risks

    # --- Key Trends ---------------------------------------------------------
    kt = []
    if rev:
        kt.append(f"Revenue {metrics.trend_direction(rev)} over {span}.")
    if nm_series and len(nm_series) >= 2:
        kt.append(f"Net margin moved from {fmt.pct(nm_series[min(nm_series)])} to {fmt.pct(nm_series[max(nm_series)])}.")
    if data.series(company, "total_assets"):
        kt.append(f"Balance sheet {metrics.trend_direction(data.series(company, 'total_assets'))}.")
    out["Key Trends"] = " ".join(kt)

    # --- Educational Notes --------------------------------------------------
    if profile == "bank":
        edu = ("For banks, judge scale by total assets and deposits, and profitability by ROE and net "
               "margin rather than ROA (which looks low by design). Cost of sales, gross margin and the "
               "current ratio don't apply to banks.")
    elif profile == "insurance":
        edu = ("For insurers, net premium income and net claims drive results. ROE and net margin are the "
               "clearest cross-company gauges; some manufacturing-style ratios don't apply.")
    elif profile == "fund":
        edu = ("For a fund, AUM and NAV per unit matter most; income-statement ratios are less meaningful "
               "than for operating companies.")
    else:
        edu = ("Read profitability through gross, operating and net margins, efficiency through ROE/ROA, and "
               "safety through debt-to-equity and the current ratio. Compare only with same-sector peers.")
    out["Educational Notes"] = edu

    # --- Overall Assessment -------------------------------------------------
    score = 0
    if rev_cagr is not None and rev_cagr > 0.10: score += 1
    if not distorted and roe_last is not None and roe_last >= 0.15: score += 1
    if nm_last is not None and nm_last >= 0.10: score += 1
    if pat_last is not None and pat_last > 0: score += 1
    if not distorted and de_last is not None and de_last < 1.0: score += 1
    if neg_equity: score -= 1
    verdict = ("presents a broadly strong financial profile" if score >= 4 else
               "shows a mixed financial profile" if score >= 2 else
               "shows a financially challenged profile")
    out["Overall Assessment"] = (
        f"Over {span}, {name} {verdict} on the available data. "
        "This is an educational summary generated from historical figures only — not investment advice."
    )
    return out
