"""Sectors — market structure at a glance, with a heatmap-style overview and drill-down."""
from __future__ import annotations
import streamlit as st

from .. import data, metrics, state, ui
from .. import format as fmt
from ..config import THEME, display_name


def _heat(value: float | None, lo: float, hi: float) -> str:
    """Background colour scaled from red (low) through neutral to green (high)."""
    if value is None:
        return "transparent"
    t = 0.5 if hi == lo else max(0.0, min(1.0, (value - lo) / (hi - lo)))
    if t >= 0.5:
        a = (t - 0.5) * 2
        return f"rgba(63,185,80,{0.06 + a * 0.28:.2f})"
    a = (0.5 - t) * 2
    return f"rgba(248,81,73,{0.06 + a * 0.28:.2f})"


def render() -> None:
    st.markdown("<h1 style='margin-bottom:2px'>Sectors</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{THEME['muted']};margin-bottom:14px'>How the 12 NGX sectors compare on scale "
                f"and returns. Colour shows relative strength within each column.</div>", unsafe_allow_html=True)

    stats = data.sector_stats()
    yr = data.dataset_summary()["year_max"]

    roes = [s["median_roe"] for s in stats if s["median_roe"] is not None]
    margins = [s["median_margin"] for s in stats if s["median_margin"] is not None]
    r_lo, r_hi = (min(roes), max(roes)) if roes else (0, 1)
    m_lo, m_hi = (min(margins), max(margins)) if margins else (0, 1)

    header = ("<tr>"
              f"<th style='text-align:left;padding:8px 12px;color:{THEME['faint']};font-size:12px'>Sector</th>"
              f"<th style='text-align:right;padding:8px 12px;color:{THEME['faint']};font-size:12px'>Companies</th>"
              f"<th style='text-align:right;padding:8px 12px;color:{THEME['faint']};font-size:12px'>Combined revenue</th>"
              f"<th style='text-align:right;padding:8px 12px;color:{THEME['faint']};font-size:12px'>Median ROE</th>"
              f"<th style='text-align:right;padding:8px 12px;color:{THEME['faint']};font-size:12px'>Median margin</th>"
              f"<th style='text-align:left;padding:8px 12px;color:{THEME['faint']};font-size:12px'>Leader (revenue)</th></tr>")
    body = ""
    for s in stats:
        roe_bg = _heat(s["median_roe"], r_lo, r_hi)
        m_bg = _heat(s["median_margin"], m_lo, m_hi)
        body += (
            f"<tr style='border-top:1px solid {THEME['grid']}'>"
            f"<td style='padding:8px 12px;color:{THEME['text']};font-weight:500'>{s['sector']}</td>"
            f"<td class='lux-num' style='text-align:right;padding:8px 12px;color:{THEME['muted']}'>{s['n']}</td>"
            f"<td class='lux-num' style='text-align:right;padding:8px 12px;color:{THEME['text']}'>{fmt.naira(s['revenue'])}</td>"
            f"<td class='lux-num' style='text-align:right;padding:8px 12px;color:{THEME['text']};background:{roe_bg}'>{fmt.pct(s['median_roe'])}</td>"
            f"<td class='lux-num' style='text-align:right;padding:8px 12px;color:{THEME['text']};background:{m_bg}'>{fmt.pct(s['median_margin'])}</td>"
            f"<td style='padding:8px 12px;color:{THEME['muted']}'>{display_name(s['top_company']) if s['top_company'] else '—'}</td>"
            f"</tr>")
    st.markdown(
        f"<div style='overflow-x:auto'><table style='width:100%;border-collapse:collapse;font-size:13px'>"
        f"<thead>{header}</thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    st.caption(f"FY{yr}. ROE/margin are sector medians. Banks show low ROA and no margin-of-goods by design — "
               "compare within a sector, not across.")

    # ---- drill-down ----
    ui.section_title("Explore a sector")
    sector_names = [s["sector"] for s in stats]
    default = st.session_state.get("sector_pick", sector_names[0])
    pick = st.selectbox("Sector", sector_names,
                        index=sector_names.index(default) if default in sector_names else 0,
                        key="sector_pick")

    members = data.sector_members(pick)
    ranked = sorted(members, key=lambda c: (data.latest_value(c, "gross_earnings")[0] or 0), reverse=True)
    st.markdown(f"<div style='color:{THEME['muted']};font-size:13px;margin:2px 0 6px'>"
                f"{len(members)} companies · ranked by revenue</div>", unsafe_allow_html=True)
    for c in ranked:
        rev, _ = data.latest_value(c, "gross_earnings")
        roe, _ = data.latest_value(c, "roe")
        cols = st.columns([5, 2, 2])
        with cols[0]:
            if st.button(display_name(c), key=f"secdrill_{c}", use_container_width=True):
                state.open_company(c)
        cols[1].markdown(f"<div class='lux-num' style='text-align:right;padding-top:7px;color:{THEME['text']}'>"
                         f"{fmt.naira(rev)}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='lux-num' style='text-align:right;padding-top:7px;color:{THEME['muted']}'>"
                         f"ROE {fmt.pct(roe)}</div>", unsafe_allow_html=True)
