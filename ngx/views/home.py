"""Home — insight-first: market story, headline numbers, biggest movers, search."""
from __future__ import annotations
import streamlit as st

from .. import config, data, metrics, state, ui, brand
from .. import format as fmt
from ..config import THEME, display_name


SUGGESTED = [
    ("Most profitable banks", "Rankings", {"metric": "roe", "sector": "Banking"}),
    ("Fastest revenue growth", "Rankings", {"metric": "gross_earnings", "sector": "All sectors"}),
    ("Compare the big brewers", "Compare", {"set": ["NIGERIAN BREWERIES", "INTERNATIONAL BREWERIES", "GUINNESS NIG"]}),
    ("Find low-debt compounders", "Screener", {}),
]


def render() -> None:
    ms = metrics.market_summary()

    # ---- hero ----
    st.markdown(brand.wordmark(30), unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-family:Fraunces,serif;font-size:26px;line-height:1.35;color:{THEME['text']};"
        f"margin:14px 0 4px;max-width:760px'>The 35 companies of the NGX earned a combined "
        f"<span style='color:{THEME['accent']}'>{fmt.naira(ms['combined_revenue'])}</span> in FY{ms['year']}, "
        f"growing at a typical <span style='color:{THEME['accent']}'>{fmt.pct(ms['median_growth'])}</span> a year "
        f"since 2021.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div style='color:{THEME['muted']};font-size:14px;margin-bottom:18px'>"
                f"{config.APP_TAGLINE} · Search a company, screen the market, or explore by sector.</div>",
                unsafe_allow_html=True)

    cards = st.columns(4)
    with cards[0]:
        ui._card("Combined revenue", fmt.naira(ms["combined_revenue"]), sub=f"FY{ms['year']}")
    with cards[1]:
        ui._card("Typical growth", fmt.pct(ms["median_growth"]), sub="revenue CAGR 21–25")
    with cards[2]:
        ui._card("Median ROE", fmt.pct(ms["median_roe"]), sub=f"FY{ms['year']}")
    with cards[3]:
        ui._card("Profitable", f"{ms['profitable']}/{ms['total_reporting']}", sub="companies")

    # ---- search ----
    ui.section_title("Find a company")
    companies = data.companies()
    labels = {display_name(c): c for c in companies}
    choice = st.selectbox("Search 35 NGX companies", ["Search a company…"] + sorted(labels),
                          label_visibility="collapsed")
    if choice in labels:
        state.open_company(labels[choice])

    # ---- movers ----
    left, right = st.columns(2)
    with left:
        ui.section_title("Fastest growing", "revenue CAGR, 2021–2025")
        for c, g, _ in metrics.biggest_movers("gross_earnings")[:5]:
            ui.company_button(c, "grow", right=fmt.pct(g), right_color=THEME["pos"])
    with right:
        ui.section_title("Standout returns", "return on equity, latest year")
        _standout_roe()

    # ---- sectors + suggested ----
    left2, right2 = st.columns(2)
    with left2:
        ui.section_title("Explore by sector")
        _sector_chips()
    with right2:
        ui.section_title("Try asking")
        for i, (label, page, payload) in enumerate(SUGGESTED):
            if st.button(label, key=f"sug_{i}", use_container_width=True):
                if page == "Rankings":
                    st.session_state["rank_metric"] = payload["metric"]
                    st.session_state["rank_sector"] = payload["sector"]
                elif page == "Compare":
                    st.session_state.compare_set = list(payload["set"])
                state.goto(page)


def _standout_roe() -> None:
    yr = data.dataset_summary()["year_max"]
    # latest ROE across companies, drop not-meaningful cases, take top 5
    df = data.load()
    latest = df[df["year"] == yr][["company", "roe"]].dropna().sort_values("roe", ascending=False)
    picked = [r for _, r in latest.iterrows() if not metrics.roe_not_meaningful(r["company"], yr)][:5]
    for r in picked:
        caution = metrics.roe_caution(r["company"], yr, r["roe"])
        mark = "  ⚠" if caution else ""
        c1, c2 = st.columns([5, 2])
        with c1:
            if st.button(display_name(r["company"]) + mark, key=f"roe_{r['company']}",
                         use_container_width=True, help=caution or None):
                state.open_company(r["company"])
        c2.markdown(f"<div class='lux-num' style='text-align:right;padding-top:7px;"
                    f"color:{THEME['accent']};font-weight:600'>{fmt.pct(r['roe'])}</div>",
                    unsafe_allow_html=True)


def _sector_chips() -> None:
    stats = data.sector_stats()
    for i in range(0, len(stats), 2):
        cols = st.columns(2)
        for col, s in zip(cols, stats[i:i + 2]):
            with col:
                if st.button(f"{s['sector']}  ·  {s['n']}", key=f"sec_{s['sector']}",
                             use_container_width=True):
                    st.session_state["sector_pick"] = s["sector"]
                    state.goto("Sectors")
