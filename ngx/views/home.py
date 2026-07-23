"""Home — global search, dataset overview, featured rankings, suggested questions."""
from __future__ import annotations
import streamlit as st

from .. import config, data, metrics, state, ui
from .. import format as fmt
from ..config import THEME, display_name


SUGGESTED = [
    ("Who are the most profitable banks?", "Rankings", {"metric": "roe", "sector": "Banking"}),
    ("Which company grew revenue fastest?", "Rankings", {"metric": "gross_earnings", "sector": "All sectors"}),
    ("Compare the big brewers", "Compare", {"set": ["NIGERIAN BREWERIES", "INTERNATIONAL BREWERIES", "GUINNESS NIG"]}),
    ("Highest dividend payers", "Rankings", {"metric": "dividend_per_share", "sector": "All sectors"}),
]


def render() -> None:
    s = data.dataset_summary()
    st.markdown(f"<h1 style='margin-bottom:0'>{config.APP_NAME}</h1>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{THEME['muted']};margin-bottom:14px'>{config.APP_TAGLINE}</div>",
                unsafe_allow_html=True)

    c = st.columns(4)
    for col, (val, lab) in zip(c, [(s["companies"], "Companies"), (s["sectors"], "Sectors"),
                                   (f"{s['year_min']}–{s['year_max']}", "Years"),
                                   (s["rows"], "Company-year filings")]):
        with col:
            ui._card(lab, str(val), "")

    st.markdown("###  ")
    left, right = st.columns([3, 2])

    with left:
        ui.section_title("Find a company")
        companies = data.companies()
        labels = {display_name(c): c for c in companies}
        choice = st.selectbox("Search 35 NGX companies", ["Type or select a company…"] + sorted(labels),
                              label_visibility="collapsed")
        if choice in labels:
            state.open_company(labels[choice])

        ui.section_title("Browse by sector")
        for sector in data.sectors():
            members = data.sector_members(sector)
            with st.expander(f"{sector}  ·  {len(members)}"):
                for m in members:
                    if st.button(display_name(m), key=f"br_{m}", use_container_width=True):
                        state.open_company(m)

    with right:
        ui.section_title("Featured · Top ROE (latest year)")
        _featured_roe()

        ui.section_title("Suggested questions")
        for i, (label, page, payload) in enumerate(SUGGESTED):
            if st.button(label, key=f"sug_{i}", use_container_width=True):
                if page == "Rankings":
                    st.session_state["rank_metric"] = payload["metric"]
                    st.session_state["rank_sector"] = payload["sector"]
                elif page == "Compare":
                    st.session_state.compare_set = list(payload["set"])
                state.goto(page)


def _featured_roe() -> None:
    df = data.load()
    yr = int(df["year"].max())
    rows = df[df["year"] == yr][["company", "roe"]].dropna().sort_values("roe", ascending=False)
    # Exclude companies whose ROE isn't meaningful (near-zero equity base) from a
    # "top performer" highlight — showing a 190% ROE as #1 would mislead.
    rows = [r for _, r in rows.iterrows() if not metrics.roe_not_meaningful(r["company"], yr)][:6]
    if not rows:
        ui.empty_state("No ranking available.")
        return
    flagged = False
    for r in rows:
        comp = r["company"]
        caution = metrics.roe_caution(comp, yr, r["roe"])
        flagged = flagged or bool(caution)
        cta, val = st.columns([4, 1])
        with cta:
            label = display_name(comp) + ("  ⚠" if caution else "")
            if st.button(label, key=f"feat_{comp}", use_container_width=True, help=caution or None):
                state.open_company(comp)
        with val:
            st.markdown(f"<div style='text-align:right;padding-top:6px;color:{THEME['pos']};"
                        f"font-weight:600'>{fmt.pct(r['roe'])}</div>", unsafe_allow_html=True)
    cap = f"Return on equity, FY{yr}, across all sectors."
    if flagged:
        cap += " ⚠ = unusually high; read alongside ROA. Near-zero-equity cases are excluded."
    st.caption(cap)
