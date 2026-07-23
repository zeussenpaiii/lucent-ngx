"""Rankings — rank companies by any metric, all-sectors or within a sector."""
from __future__ import annotations
import streamlit as st

from .. import data, charts, metrics, state, ui
from .. import format as fmt
from ..config import THEME, METRICS, display_name

RANKABLE = [k for k, m in METRICS.items() if m["group"] in ("income", "balance", "cashflow", "ratio", "market")]


def render() -> None:
    st.markdown("## Rankings")
    df = data.load()
    max_year = int(df["year"].max())

    c = st.columns([2, 2, 1])
    with c[0]:
        default_metric = st.session_state.get("rank_metric", "roe")
        metric = st.selectbox("Rank by", RANKABLE,
                              index=RANKABLE.index(default_metric) if default_metric in RANKABLE else 0,
                              format_func=lambda k: METRICS[k]["label"], key="rank_metric")
    with c[1]:
        sector_opts = ["All sectors"] + data.sectors()
        default_sector = st.session_state.get("rank_sector", "All sectors")
        sector = st.selectbox("Scope", sector_opts,
                              index=sector_opts.index(default_sector) if default_sector in sector_opts else 0,
                              key="rank_sector")
    with c[2]:
        year = st.selectbox("Year", list(range(max_year, int(df["year"].min()) - 1, -1)), key="rank_year")

    good = METRICS[metric]["good"]
    ascending = (good == "down")

    scope = df if sector == "All sectors" else df[df["sector"] == sector]
    rows = scope[scope["year"] == year][["company", metric]].dropna()
    if not len(rows):
        ui.empty_state(f"No data for {METRICS[metric]['label']} in FY{year}"
                       + ("" if sector == "All sectors" else f" ({sector})"),
                       "Try another metric, sector, or year.")
        return
    rows = rows.sort_values(metric, ascending=ascending)

    if sector == "All sectors" and METRICS[metric]["group"] == "ratio":
        st.caption("Ranking a ratio across all sectors mixes very different business models "
                   "(e.g. banks vs manufacturers). Narrow the scope to a sector for a fair comparison.")

    pairs = [(display_name(r["company"]), float(r[metric])) for _, r in rows.iterrows()]
    st.plotly_chart(
        charts.horizontal_ranking(pairs[:20], METRICS[metric]["fmt"],
                                  f"{METRICS[metric]['label']} · FY{year}"),
        use_container_width=True, config={"displayModeBar": False},
    )

    # Clickable table
    st.markdown("#### Full ranking")
    any_caution = False
    for rank, (_, r) in enumerate(rows.iterrows(), start=1):
        comp = r["company"]
        caution = metrics.roe_caution(comp, year, r[metric]) if metric == "roe" else None
        any_caution = any_caution or bool(caution)
        col = st.columns([1, 6, 2])
        col[0].markdown(f"<div style='color:{THEME['muted']};padding-top:6px'>{rank}</div>",
                        unsafe_allow_html=True)
        with col[1]:
            label = display_name(comp) + ("  ⚠" if caution else "")
            if st.button(label, key=f"rank_{comp}", use_container_width=True, help=caution or None):
                state.open_company(comp)
        col[2].markdown(f"<div style='text-align:right;padding-top:6px;color:{THEME['text']};"
                        f"font-weight:600'>{fmt.metric(metric, r[metric])}</div>", unsafe_allow_html=True)
    if any_caution:
        st.caption("⚠ = ROE flattered by a small or fast-changing equity base — read alongside ROA.")
