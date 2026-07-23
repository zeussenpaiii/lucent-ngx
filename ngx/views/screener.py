"""Screener — filter the 35 companies by your own criteria (latest year)."""
from __future__ import annotations
import streamlit as st

from .. import data, state
from .. import format as fmt
from ..config import THEME, display_name


def render() -> None:
    st.markdown("<h1 style='margin-bottom:2px'>Screener</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{THEME['muted']};margin-bottom:14px'>Find companies that match what you care "
                f"about — set the filters, get a shortlist. Based on the latest reported year.</div>",
                unsafe_allow_html=True)

    df = data.latest_frame()
    yr = int(df["year"].iloc[0]) if len(df) else data.dataset_summary()["year_max"]
    max_rev_bn = int((df["gross_earnings"].max() or 0) / 1e9) + 1

    c1, c2, c3 = st.columns(3)
    with c1:
        sectors = st.multiselect("Sectors", data.sectors(), default=[], key="scr_sectors",
                                 placeholder="All sectors")
        min_rev = st.slider("Min revenue (₦bn)", 0, max_rev_bn, 0, key="scr_rev")
    with c2:
        min_roe = st.slider("Min ROE (%)", -50, 100, 0, key="scr_roe")
        max_de = st.slider("Max debt/equity (x)", 0.0, 5.0, 5.0, 0.25, key="scr_de")
    with c3:
        profitable = st.checkbox("Profitable only", value=True, key="scr_prof")
        dividend = st.checkbox("Pays a dividend", value=False, key="scr_div")
        min_margin = st.slider("Min net margin (%)", -20, 60, -20, key="scr_margin")

    # ---- filter ----
    rows = df.copy()
    if sectors:
        rows = rows[rows["sector"].isin(sectors)]
    rows = rows[rows["gross_earnings"].fillna(0) >= min_rev * 1e9]
    rows = rows[rows["roe"].fillna(-99) >= min_roe / 100]
    rows = rows[rows["net_margin"].fillna(-99) >= min_margin / 100]
    rows = rows[rows["debt_to_equity"].fillna(0) <= max_de]
    if profitable:
        rows = rows[rows["profit_after_tax"].fillna(-1) > 0]
    if dividend:
        rows = rows[rows["dividend_per_share"].fillna(0) > 0]
    rows = rows.sort_values("gross_earnings", ascending=False)

    st.markdown(f"<div style='margin:6px 0 8px;color:{THEME['text']};font-weight:600'>"
                f"{len(rows)} <span style='color:{THEME['muted']};font-weight:400'>"
                f"of {df['company'].nunique()} companies match · FY{yr}</span></div>", unsafe_allow_html=True)

    if not len(rows):
        from .. import ui
        ui.empty_state("No companies match these filters.", "Loosen a filter and try again.")
        return

    # header
    st.markdown(
        f"<div style='display:flex;padding:4px 12px;color:{THEME['faint']};font-size:11.5px;"
        f"text-transform:uppercase;letter-spacing:.3px'>"
        f"<div style='flex:5'>Company</div><div style='flex:2;text-align:right'>Revenue</div>"
        f"<div style='flex:1.4;text-align:right'>ROE</div><div style='flex:1.6;text-align:right'>Margin</div>"
        f"<div style='flex:1.2;text-align:right'>D/E</div></div>", unsafe_allow_html=True)

    for _, r in rows.iterrows():
        c = r["company"]
        cols = st.columns([5, 2, 1.4, 1.6, 1.2])
        with cols[0]:
            if st.button(f"{display_name(c)}", key=f"scr_{c}", use_container_width=True):
                state.open_company(c)
        cols[1].markdown(_num(fmt.naira(r["gross_earnings"]), THEME["text"]), unsafe_allow_html=True)
        cols[2].markdown(_num(fmt.pct(r["roe"]), THEME["muted"]), unsafe_allow_html=True)
        cols[3].markdown(_num(fmt.pct(r["net_margin"]), THEME["muted"]), unsafe_allow_html=True)
        cols[4].markdown(_num(fmt.multiple(r["debt_to_equity"]), THEME["muted"]), unsafe_allow_html=True)


def _num(text: str, color: str) -> str:
    return (f"<div class='lux-num' style='text-align:right;padding-top:7px;color:{color};"
            f"font-size:13px'>{text}</div>")
