"""Company Workspace — snapshot, sector-aware statements, charts, AI analysis."""
from __future__ import annotations
import streamlit as st

from .. import config, data, charts, insights, metrics, narrative, report, state, ui
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

    top = st.columns([5, 1.1, 1.1])
    with top[0]:
        ui.company_header(company)
    with top[1]:
        if st.button("＋ Compare", use_container_width=True):
            state.add_to_compare(company)
    with top[2]:
        st.download_button("⬇ Report", data=report.company_report_html(company),
                           file_name=f"{display_name(company).replace(' ', '_')}_Lucent.html",
                           mime="text/html", use_container_width=True)

    ui.confidence_badge(company, year)
    ui.kpi_row(company)
    _standout(company)

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

    _dividends(company, show)


def _standout(company: str) -> None:
    """Peer-relative findings — the bit that should feel like an analyst, not a table."""
    items = insights.for_company(company)
    if not items:
        return
    colours = {"pos": THEME["pos"], "neg": THEME["neg"], "warn": THEME["accent"], "info": THEME["muted"]}
    rows = "".join(
        f"<div style='display:flex;gap:9px;align-items:flex-start;padding:5px 0'>"
        f"<span style='color:{colours.get(tone, THEME['muted'])};font-size:15px;line-height:1.2'>•</span>"
        f"<span style='color:{THEME['text']};font-size:13.5px;line-height:1.45'>{text}</span></div>"
        for tone, text in items
    )
    st.markdown(
        f"""<div style="background:{THEME['panel']};border:1px solid {THEME['border']};
        border-left:3px solid {THEME['accent']};border-radius:12px;padding:14px 18px;margin:16px 0 4px">
        <div style="font-size:11.5px;text-transform:uppercase;letter-spacing:.5px;
        color:{THEME['accent']};font-weight:600;margin-bottom:6px">What stands out</div>
        {rows}</div>""",
        unsafe_allow_html=True,
    )


def _dividends(company: str, show) -> None:
    """Dividend history + reliability, shown only for companies that actually pay."""
    dps = data.series(company, "dividend_per_share")
    if not any(v and v > 0 for v in dps.values()):
        return
    p = metrics.dividend_profile(company)
    from .. import format as fmt

    row = st.columns(2)
    with row[0]:
        show(charts.bars(dps, "per_share", "Dividend per share", color=THEME["accent"]))
    with row[1]:
        payout_col = THEME["pos"] if p["covered"] else THEME["accent"]
        cover_note = ("covered by earnings" if p["covered"]
                      else "paid out more than earned" if p["payout"] else "—")
        growth = fmt.pct(p["dps_cagr"]) if p["dps_cagr"] is not None else "—"
        st.markdown(
            f"""<div style="background:{THEME['panel']};border:1px solid {THEME['border']};
            border-radius:12px;padding:14px 16px;margin-top:34px">
            <div style="font-size:11.5px;color:{THEME['muted']};text-transform:uppercase;
            letter-spacing:.4px;margin-bottom:10px">Dividend profile</div>
            {_stat('Latest dividend', fmt.per_share(p['latest_dps']) if p['latest_dps'] else '—')}
            {_stat('Payout ratio', fmt.pct(p['payout']) if p['payout'] is not None else '—', payout_col)}
            {_stat('Dividend growth', growth)}
            {_stat('Paid', f"{p['years_paid']} of {p['years_total']} years"
                   + (' · every year' if p['consistent'] else ''))}
            <div style="color:{THEME['faint']};font-size:11.5px;margin-top:8px">{cover_note}. Yield needs a
            share price, which this dataset doesn't include.</div></div>""",
            unsafe_allow_html=True)


def _stat(label: str, value: str, color: str | None = None) -> str:
    return (f"<div style='display:flex;justify-content:space-between;padding:3px 0'>"
            f"<span style='color:{THEME['muted']};font-size:13px'>{label}</span>"
            f"<span class='lux-num' style='color:{color or THEME['text']};font-size:13.5px;"
            f"font-weight:600'>{value}</span></div>")


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
