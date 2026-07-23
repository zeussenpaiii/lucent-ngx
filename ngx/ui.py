"""
ui.py — Reusable Streamlit UI components with the dark, high-density look.

Everything user-facing (cards, badges, tables, empty/loading states) lives here
so pages stay declarative and the styling is consistent.
"""
from __future__ import annotations
import streamlit as st

from . import config, data, glossary
from . import format as fmt
from .config import METRICS, THEME, display_name, ticker, profile_for


# --------------------------------------------------------------------------
def disclaimer() -> None:
    st.markdown(
        f"""<div style="background:{THEME['panel']};border:1px solid {THEME['border']};
        border-left:3px solid {THEME['warn']};border-radius:6px;padding:8px 12px;margin:4px 0 14px;
        font-size:12px;color:{THEME['muted']}">
        <b style="color:{THEME['text']}">Educational prototype.</b> Historical figures (2021–2025) from
        company filings — <b>not investment advice</b>. Ratios use the dataset's stored
        (average-balance) values.</div>""",
        unsafe_allow_html=True,
    )


def company_header(company: str) -> None:
    sector = data.company_sector(company)
    tk = ticker(company)
    fye = config.NON_DECEMBER_FYE.get(company)
    partial = len(data.years_for(company)) < len(config.YEARS)
    chips = [f"<span style='color:{THEME['muted']}'>{sector}</span>"]
    if tk:
        chips.append(f"<span style='background:{THEME['panel2']};padding:1px 7px;border-radius:4px;"
                     f"font-size:12px;color:{THEME['text']}'>{tk}</span>")
    if fye:
        chips.append(f"<span style='color:{THEME['warn']};font-size:12px'>FY-end {fye}</span>")
    if partial:
        yrs = data.years_for(company)
        chips.append(f"<span style='color:{THEME['warn']};font-size:12px'>Limited history "
                     f"({min(yrs)}–{max(yrs)})</span>")
    st.markdown(
        f"<h2 style='margin:0 0 2px'>{display_name(company)}</h2>"
        f"<div style='display:flex;gap:12px;align-items:center;margin-bottom:6px'>{' · '.join(chips)}</div>",
        unsafe_allow_html=True,
    )


def confidence_badge(company: str, year: int) -> None:
    p = data.provenance(company, year)
    status = (p.get("status") or "").strip()
    color, label = {
        "web-verified": (THEME["pos"], "Verified vs published reports"),
        "balance-validated": (THEME["accent"], "Balance-sheet validated"),
        "unavailable": (THEME["muted"], "Not available"),
    }.get(status, (THEME["muted"], status or "—"))
    ocr = (p.get("type") or "").strip().upper() == "OCR"
    ocr_chip = (f"<span style='background:{THEME['panel2']};color:{THEME['warn']};padding:1px 6px;"
                f"border-radius:4px;font-size:11px;margin-left:6px'>OCR-extracted</span>") if ocr else ""
    st.markdown(
        f"""<div style="font-size:12px;color:{THEME['muted']};margin:2px 0 6px">
        Data confidence (FY{year}):
        <span style="color:{color};font-weight:600">● {label}</span>{ocr_chip}</div>""",
        unsafe_allow_html=True,
    )
    log = (p.get("correction_log") or "").strip()
    reason = (p.get("status_reason") or "").strip()
    if log or reason:
        with st.expander("How we got these numbers (provenance)"):
            if reason:
                st.caption(f"**Validation:** {reason}")
            if p.get("balance_check"):
                st.caption(f"**Balance check:** {p['balance_check']}")
            if log:
                st.caption("**Corrections applied to this filing:**")
                for part in [x.strip() for x in log.split("||") if x.strip()]:
                    st.markdown(f"- {part}")


# --------------------------------------------------------------------------
def _delta_html(key: str, new, old) -> str:
    d = fmt.delta_pct(new, old)
    if d is None:
        return f"<span style='color:{THEME['muted']};font-size:12px'>—</span>"
    good = METRICS.get(key, {}).get("good")
    up = d >= 0
    if good == "up":
        color = THEME["pos"] if up else THEME["neg"]
    elif good == "down":
        color = THEME["neg"] if up else THEME["pos"]
    else:
        color = THEME["muted"]
    arrow = "▲" if up else "▼"
    return f"<span style='color:{color};font-size:12px'>{arrow} {fmt.pct(abs(d))}</span>"


def kpi_row(company: str) -> None:
    cols = st.columns(len(config.KPI_CARDS))
    for col, key in zip(cols, config.KPI_CARDS):
        s = data.series(company, key)
        if not s:
            with col:
                _card(METRICS[key]["short"], fmt.DASH, "")
            continue
        ys = sorted(s)
        last = s[ys[-1]]
        prev = s[ys[-2]] if len(ys) >= 2 else None
        with col:
            _card(METRICS[key]["short"], fmt.metric(key, last),
                  _delta_html(key, last, prev), sub=f"FY{ys[-1]}")


def _card(label: str, value: str, delta_html: str, sub: str = "") -> None:
    st.markdown(
        f"""<div style="background:{THEME['panel']};border:1px solid {THEME['border']};
        border-radius:8px;padding:12px 14px;height:100%">
        <div style="font-size:12px;color:{THEME['muted']};margin-bottom:4px">{label}</div>
        <div style="font-size:20px;font-weight:700;color:{THEME['text']};line-height:1.1">{value}</div>
        <div style="margin-top:4px">{delta_html} <span style="color:{THEME['muted']};font-size:11px">{sub}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
def statement_table(company: str, group: str, title: str) -> None:
    """Render one statement group (income/balance/cashflow/ratio) as a
    year-over-year table, showing only rows that have data for this company."""
    profile = profile_for(data.company_sector(company))
    keys = config.PROFILES[profile][group]
    years = data.years_for(company)
    if not years:
        return
    rows_html = []
    for key in keys:
        s = data.series(company, key)
        if not s:
            continue  # skip metrics this company doesn't report
        defn = glossary.define(key)
        tip = (defn["definition"] if defn else "")
        cells = "".join(
            f"<td style='text-align:right;padding:5px 10px;color:{THEME['text']}'>"
            f"{fmt.metric(key, s.get(y))}</td>" for y in years
        )
        rows_html.append(
            f"<tr style='border-top:1px solid {THEME['grid']}'>"
            f"<td style='padding:5px 10px;color:{THEME['muted']}' title=\"{tip}\">{METRICS[key]['label']}</td>"
            f"{cells}</tr>"
        )
    if not rows_html:
        return
    head = "".join(f"<th style='text-align:right;padding:5px 10px;color:{THEME['muted']};"
                   f"font-weight:600'>FY{y}</th>" for y in years)
    st.markdown(f"<div style='font-size:13px;font-weight:700;color:{THEME['text']};margin:10px 0 2px'>{title}</div>",
                unsafe_allow_html=True)
    st.markdown(
        f"""<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead><tr><th style='text-align:left;padding:5px 10px;color:{THEME['muted']}'></th>{head}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody></table></div>""",
        unsafe_allow_html=True,
    )


def empty_state(msg: str, hint: str = "") -> None:
    st.markdown(
        f"""<div style="background:{THEME['panel']};border:1px dashed {THEME['border']};
        border-radius:8px;padding:28px;text-align:center;color:{THEME['muted']};margin:8px 0">
        <div style="font-size:15px;color:{THEME['text']};margin-bottom:4px">{msg}</div>
        <div style="font-size:12px">{hint}</div></div>""",
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(f"<h4 style='margin:14px 0 4px;color:{THEME['text']}'>{text}</h4>", unsafe_allow_html=True)
