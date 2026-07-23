"""Company Workspace — snapshot, sector-aware statements, charts, AI analysis."""
from __future__ import annotations
import streamlit as st

from .. import config, data, charts, narrative, state, ui
from ..config import THEME, display_name, profile_for


def render() -> None:
    company = st.session_state.get("company")
    if not company or company not in data.companies():
        ui.empty_state("No company selected.", "Pick one from Home to open its workspace.")
        if st.button("← Back to Home"):
            state.goto("Home")
        return

    sector = data.company_sector(company)
    profile = profile_for(sector)
    year = data.latest_year(company)

    top = st.columns([5, 1])
    with top[0]:
        ui.company_header(company)
    with top[1]:
        if st.button("＋ Compare", use_container_width=True):
            state.add_to_compare(company)

    ui.confidence_badge(company, year)
    ui.kpi_row(company)

    tabs = st.tabs(["Snapshot & Charts", "Financial Statements", "AI Analysis"])

    with tabs[0]:
        _charts(company, sector, profile)
    with tabs[1]:
        _statements(company)
    with tabs[2]:
        _analysis(company)


def _charts(company: str, sector: str, profile: str) -> None:
    def show(fig):
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    r1 = st.columns(2)
    with r1[0]:
        if data.series(company, "gross_earnings"):
            show(charts.revenue_vs_pat(company))
    with r1[1]:
        if data.series(company, "roe"):
            show(charts.ratio_vs_median(company, sector, "roe"))

    r2 = st.columns(2)
    with r2[0]:
        margins = {config.METRICS[k]["short"]: data.series(company, k)
                   for k in ["net_margin", "gross_margin", "operating_margin"] if data.series(company, k)}
        if margins:
            show(charts.line(margins, "pct", "Margins over time"))
    with r2[1]:
        if data.series(company, "net_cash_from_operations"):
            show(charts.bars(data.series(company, "net_cash_from_operations"), "naira",
                             "Operating cash flow", color=THEME["pos"]))

    r3 = st.columns(2)
    with r3[0]:
        if profile == "bank" and data.series(company, "customer_deposits"):
            show(charts.grouped_bars(
                {"Deposits": data.series(company, "customer_deposits"),
                 "Net loans": data.series(company, "net_loans_advances")},
                "naira", "Deposits vs net loans"))
        elif data.series(company, "eps_basic"):
            show(charts.bars(data.series(company, "eps_basic"), "per_share", "Earnings per share"))
    with r3[1]:
        eq = data.series(company, "total_equity")
        li = data.series(company, "total_liabilities")
        if eq and li:
            show(charts.grouped_bars({"Equity": eq, "Liabilities": li}, "naira",
                                     "Equity vs liabilities"))
        elif data.series(company, "dividend_per_share"):
            show(charts.bars(data.series(company, "dividend_per_share"), "per_share",
                             "Dividend per share"))


def _statements(company: str) -> None:
    ui.statement_table(company, "income", "Income Statement")
    ui.statement_table(company, "balance", "Balance Sheet")
    ui.statement_table(company, "cashflow", "Cash Flow")
    ui.statement_table(company, "ratio", "Key Ratios")
    st.caption("Only line items reported by this company/sector are shown. — = not reported that year.")


def _analysis(company: str) -> None:
    with st.spinner("Generating analysis from the data…"):
        sections = narrative.generate(company)

    exec_summary = sections.get("Executive Summary", "")
    st.markdown(
        f"""<div style="background:{THEME['panel2']};border:1px solid {THEME['border']};
        border-radius:8px;padding:14px 16px;margin-bottom:10px">
        <div style="font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:{THEME['accent']};
        margin-bottom:4px">Executive Summary</div>
        <div style="color:{THEME['text']};font-size:15px;line-height:1.5">{exec_summary}</div></div>""",
        unsafe_allow_html=True,
    )

    prose = ["Business Overview", "Growth", "Profitability", "Balance Sheet", "Cash Flow", "Key Trends"]
    cols = st.columns(2)
    for i, key in enumerate(prose):
        if sections.get(key):
            with cols[i % 2]:
                st.markdown(f"**{key}**")
                st.markdown(f"<span style='color:{THEME['muted']};font-size:13.5px'>{sections[key]}</span>",
                            unsafe_allow_html=True)
                st.markdown("")

    swr = st.columns(3)
    for col, key, color in zip(swr, ["Strengths", "Weaknesses", "Risks"],
                               [THEME["pos"], THEME["neg"], THEME["warn"]]):
        with col:
            st.markdown(f"<b style='color:{color}'>{key}</b>", unsafe_allow_html=True)
            for item in sections.get(key, []):
                st.markdown(f"<div style='font-size:13px;color:{THEME['text']};margin:3px 0'>"
                            f"<span style='color:{color}'>•</span> {item}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"**Educational Notes** &nbsp;<span style='color:{THEME['muted']};font-size:13px'>"
                f"{sections.get('Educational Notes','')}</span>", unsafe_allow_html=True)
    st.info(sections.get("Overall Assessment", ""))
