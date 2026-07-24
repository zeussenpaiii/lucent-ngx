"""Dividends — who pays, how much, how reliably, and whether it's covered by earnings."""
from __future__ import annotations
import streamlit as st

from .. import charts, data, metrics, state, ui
from .. import format as fmt
from ..config import THEME, display_name


def render() -> None:
    st.markdown("<h1 style='margin-bottom:2px'>Dividends</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{THEME['muted']};margin-bottom:6px'>Who pays, how much, how reliably — "
                f"and whether the payout is actually covered by earnings.</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{THEME['faint']};font-size:12px;margin-bottom:14px'>"
                f"Note: dividend <b>yield</b> isn't shown — it needs a live share price, and this dataset is "
                f"fundamentals-only. Everything here comes from declared dividends per share.</div>",
                unsafe_allow_html=True)

    ms = metrics.dividend_market_summary()
    c = st.columns(4)
    with c[0]:
        ui._card("Total declared", fmt.naira(ms["total_declared"]), sub="latest year")
    with c[1]:
        ui._card("Dividend payers", f"{ms['payers']}/{ms['total_companies']}", sub="companies")
    with c[2]:
        ui._card("Paid every year", str(ms["consistent"]), sub="2021–2025")
    with c[3]:
        ui._card("Median payout", fmt.pct(ms["median_payout"]), sub="of earnings")

    rows = metrics.dividend_table()

    # ---- filters ----
    f1, f2 = st.columns([2, 2])
    with f1:
        sectors = st.multiselect("Sectors", data.sectors(), default=[], key="div_sectors",
                                 placeholder="All sectors")
    with f2:
        mode = st.radio("Show", ["All companies", "Payers only", "Paid every year", "Covered by earnings"],
                        horizontal=True, key="div_mode", label_visibility="collapsed")

    def keep(r):
        if sectors and data.company_sector(r["company"]) not in sectors:
            return False
        if mode == "Payers only":
            return bool(r["latest_dps"])
        if mode == "Paid every year":
            return r["consistent"]
        if mode == "Covered by earnings":
            return bool(r["latest_dps"]) and r["covered"]
        return True

    shown = [r for r in rows if keep(r)]

    ui.section_title("Dividend table", f"{len(shown)} companies")
    st.markdown(
        f"<div style='display:flex;padding:4px 12px;color:{THEME['faint']};font-size:11px;"
        f"text-transform:uppercase;letter-spacing:.3px'>"
        f"<div style='flex:5'>Company</div><div style='flex:2;text-align:right'>DPS</div>"
        f"<div style='flex:2;text-align:right'>Total paid</div>"
        f"<div style='flex:2;text-align:right'>Payout</div>"
        f"<div style='flex:2;text-align:right'>DPS growth</div>"
        f"<div style='flex:2;text-align:right'>Reliability</div></div>", unsafe_allow_html=True)

    for r in shown:
        comp = r["company"]
        cols = st.columns([5, 2, 2, 2, 2, 2])
        with cols[0]:
            if st.button(display_name(comp), key=f"div_{comp}", use_container_width=True):
                state.open_company(comp)
        cols[1].markdown(_n(fmt.per_share(r["latest_dps"]) if r["latest_dps"] else fmt.DASH,
                            THEME["text"]), unsafe_allow_html=True)
        cols[2].markdown(_n(fmt.naira(r["total_payout"]) if r["total_payout"] else fmt.DASH,
                            THEME["muted"]), unsafe_allow_html=True)
        # payout: green if covered, gold if paying beyond earnings. Only shown
        # when a dividend was actually declared in the latest year, so it can't
        # contradict a blank DPS.
        pc = THEME["muted"]
        show_payout = r["latest_dps"] is not None and r["payout"] is not None
        if show_payout:
            pc = THEME["pos"] if r["covered"] else THEME["accent"]
        cols[3].markdown(_n(fmt.pct(r["payout"]) if show_payout else fmt.DASH, pc),
                         unsafe_allow_html=True)
        gc = THEME["muted"]
        if r["dps_cagr"] is not None:
            gc = THEME["pos"] if r["dps_cagr"] >= 0 else THEME["neg"]
        cols[4].markdown(_n(fmt.pct(r["dps_cagr"]) if r["dps_cagr"] is not None else fmt.DASH, gc),
                         unsafe_allow_html=True)
        rel = f"{r['years_paid']}/{r['years_total']} yrs"
        rc = THEME["pos"] if r["consistent"] else THEME["muted"]
        cols[5].markdown(_n(rel, rc), unsafe_allow_html=True)

    st.caption("Payout shown green when the dividend is covered by earnings (≤100%), gold when the company "
               "paid out more than it earned. Reliability = years a dividend was declared.")

    _calculator()

    # ---- most reliable payers ----
    champs = [r for r in rows if r["consistent"] and r["dps_cagr"] is not None]
    champs.sort(key=lambda r: r["dps_cagr"], reverse=True)
    if champs:
        ui.section_title("Most reliable payers", "paid every year, ranked by dividend growth")
        for r in champs[:8]:
            ui.company_button(r["company"], "champ",
                              right=f"{fmt.pct(r['dps_cagr'])} growth", right_color=THEME["pos"])


def _calculator() -> None:
    """Work out what a holding would actually have paid you."""
    ui.section_title("Dividend calculator", "what a holding would have paid you")
    st.markdown(f"<div style='color:{THEME['faint']};font-size:12px;margin-bottom:8px'>"
                f"Enter how many shares you hold (or are considering). Optionally add the price you paid "
                f"per share to get a yield on cost — the dataset has no share prices, so that number has to "
                f"come from you.</div>", unsafe_allow_html=True)

    payers = [r for r in metrics.dividend_table() if r["latest_dps"]]
    labels = {display_name(r["company"]): r["company"] for r in payers}

    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        picked = st.selectbox("Company", sorted(labels), key="calc_company")
    with c2:
        shares = st.number_input("Shares held", min_value=0, value=10_000, step=1_000, key="calc_shares")
    with c3:
        cost = st.number_input("Price paid per share (₦, optional)", min_value=0.0, value=0.0,
                               step=1.0, key="calc_cost")

    company = labels[picked]
    prof = metrics.dividend_profile(company)
    dps_series = prof["dps"]
    latest_dps = prof["latest_dps"] or 0.0

    annual = shares * latest_dps
    lifetime = sum(v * shares for v in dps_series.values() if v and v > 0)
    invested = shares * cost if cost else None
    yoc = (latest_dps / cost) if cost else None

    cards = st.columns(4)
    with cards[0]:
        ui._card("Annual income", fmt.naira(annual), sub=f"at ₦{latest_dps:,.2f}/share")
    with cards[1]:
        ui._card(f"Total {min(dps_series) if dps_series else ''}–{max(dps_series) if dps_series else ''}",
                 fmt.naira(lifetime), sub="if held throughout")
    with cards[2]:
        ui._card("Yield on cost", fmt.pct(yoc) if yoc else "—",
                 sub="you supplied the price" if yoc else "enter a price")
    with cards[3]:
        ui._card("Cost of holding", fmt.naira(invested) if invested else "—",
                 sub="shares × price" if invested else "optional")

    # year-by-year payout
    if dps_series:
        rows = "".join(
            f"<tr style='border-top:1px solid {THEME['grid']}'>"
            f"<td style='padding:5px 12px;color:{THEME['muted']}'>FY{y}</td>"
            f"<td class='lux-num' style='text-align:right;padding:5px 12px;color:{THEME['muted']}'>"
            f"{fmt.per_share(dps_series[y])}</td>"
            f"<td class='lux-num' style='text-align:right;padding:5px 12px;color:{THEME['text']}'>"
            f"{fmt.naira(dps_series[y] * shares)}</td></tr>"
            for y in sorted(dps_series)
        )
        st.markdown(
            f"""<div style="overflow-x:auto;margin-top:10px"><table style="width:100%;
            border-collapse:collapse;font-size:13px"><thead><tr>
            <th style='text-align:left;padding:5px 12px;color:{THEME['faint']};font-size:11.5px'>Year</th>
            <th style='text-align:right;padding:5px 12px;color:{THEME['faint']};font-size:11.5px'>Dividend/share</th>
            <th style='text-align:right;padding:5px 12px;color:{THEME['faint']};font-size:11.5px'>Your income</th>
            </tr></thead><tbody>{rows}</tbody></table></div>""",
            unsafe_allow_html=True)

    if prof["payout"] and prof["payout"] > 1.0:
        st.warning(f"{display_name(company)} paid out {fmt.pct(prof['payout'])} of its earnings — more than "
                   f"it earned. A dividend at this level may not be repeatable.", icon="⚠️")
    st.caption("Based on dividends already declared for the years shown. Past dividends are not a promise of "
               "future ones — educational only, not investment advice.")


def _n(text: str, color: str) -> str:
    return (f"<div class='lux-num' style='text-align:right;padding-top:7px;color:{color};"
            f"font-size:13px'>{text}</div>")
