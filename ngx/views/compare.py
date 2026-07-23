"""Compare — 2–4 companies side by side, sector-aware, with a deterministic verdict."""
from __future__ import annotations
import streamlit as st

from .. import config, data, charts, metrics, ui
from .. import format as fmt
from ..config import THEME, METRICS, display_name

COMPARE_METRICS = ["gross_earnings", "profit_after_tax", "net_margin", "roe", "roa",
                   "eps_basic", "dividend_per_share", "total_assets", "debt_to_equity"]


def render() -> None:
    st.markdown("## Compare companies")
    companies = data.companies()
    labels = {display_name(c): c for c in companies}
    default = [display_name(c) for c in st.session_state.get("compare_set", []) if c in companies]

    picked = st.multiselect("Select 2–4 companies", sorted(labels), default=default[:4],
                            max_selections=4)
    chosen = [labels[p] for p in picked]
    st.session_state.compare_set = chosen

    if len(chosen) < 2:
        ui.empty_state("Pick at least two companies to compare.",
                       "You can add companies from any workspace with the ＋ Compare button.")
        return

    # Cross-sector warning
    secs = {data.company_sector(c) for c in chosen}
    if len(secs) > 1:
        st.warning("You're comparing companies from different sectors "
                   f"({', '.join(sorted(secs))}). Ratios like ROA, margins and leverage aren't directly "
                   "comparable across sectors — read them with care.", icon="⚠️")

    _table(chosen)

    st.markdown("### Trend")
    mkey = st.selectbox("Metric to chart", COMPARE_METRICS,
                        format_func=lambda k: METRICS[k]["label"])
    series_map = {display_name(c): data.series(c, mkey) for c in chosen}
    series_map = {k: v for k, v in series_map.items() if v}
    if series_map:
        st.plotly_chart(charts.line(series_map, METRICS[mkey]["fmt"], METRICS[mkey]["label"], height=340),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("### AI comparison")
    _verdict(chosen)


def _table(chosen: list[str]) -> None:
    # Use each company's latest available year.
    header = "".join(f"<th style='text-align:right;padding:6px 10px;color:{THEME['text']}'>"
                     f"{display_name(c)}<br><span style='color:{THEME['muted']};font-weight:400'>"
                     f"FY{data.latest_year(c)}</span></th>" for c in chosen)
    rows = []
    for key in COMPARE_METRICS:
        vals = [data.latest_value(c, key)[0] for c in chosen]
        good = METRICS[key]["good"]
        present = [v for v in vals if v is not None]
        best = None
        if present and good in ("up", "down"):
            best = (max if good == "up" else min)(present)
        cells = ""
        for v in vals:
            is_best = best is not None and v == best and len(chosen) > 1
            style = f"color:{THEME['pos']};font-weight:700" if is_best else f"color:{THEME['text']}"
            cells += f"<td style='text-align:right;padding:6px 10px;{style}'>{fmt.metric(key, v)}</td>"
        rows.append(f"<tr style='border-top:1px solid {THEME['grid']}'>"
                    f"<td style='padding:6px 10px;color:{THEME['muted']}'>{METRICS[key]['label']}</td>{cells}</tr>")
    st.markdown(
        f"""<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead><tr><th style='text-align:left;padding:6px 10px'></th>{header}</tr></thead>
        <tbody>{''.join(rows)}</tbody></table></div>
        <div style="color:{THEME['muted']};font-size:11px;margin-top:4px">Best value per row highlighted
        (where a metric has a clear better direction).</div>""",
        unsafe_allow_html=True,
    )


def _verdict(chosen: list[str]) -> None:
    lines = []
    # Size (latest revenue)
    rev = [(display_name(c), data.latest_value(c, "gross_earnings")[0]) for c in chosen]
    rev = [(n, v) for n, v in rev if v is not None]
    if rev:
        lead = max(rev, key=lambda x: x[1])
        lines.append(f"**Largest by revenue:** {lead[0]} ({fmt.naira(lead[1])}).")
    # Profitability (roe) — carry the caution so a flattered ROE isn't crowned cleanly
    roe = []
    for c in chosen:
        v, yr = data.latest_value(c, "roe")
        if v is not None:
            roe.append((c, v, yr))
    if roe:
        lead = max(roe, key=lambda x: x[1])
        note = metrics.roe_caution(lead[0], lead[2], lead[1])
        extra = f"  ⚠ {note}" if note else ""
        lines.append(f"**Highest return on equity:** {display_name(lead[0])} ({fmt.pct(lead[1])}).{extra}")
    # Growth (revenue CAGR)
    grow = [(display_name(c), metrics.cagr(data.series(c, "gross_earnings"))) for c in chosen]
    grow = [(n, v) for n, v in grow if v is not None]
    if grow:
        lead = max(grow, key=lambda x: x[1])
        lines.append(f"**Fastest revenue growth:** {lead[0]} ({fmt.pct(lead[1])} CAGR).")
    # Efficiency (net margin)
    nm = [(display_name(c), data.latest_value(c, "net_margin")[0]) for c in chosen]
    nm = [(n, v) for n, v in nm if v is not None]
    if nm:
        lead = max(nm, key=lambda x: x[1])
        lines.append(f"**Widest net margin:** {lead[0]} ({fmt.pct(lead[1])}).")
    for ln in lines:
        st.markdown(f"- {ln}")
    st.caption("Generated from the data. Educational only — not investment advice.")
