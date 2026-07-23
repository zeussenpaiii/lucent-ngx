"""
ui.py — Reusable Lucent UI components (dark, editorial, high-signal).

Everything user-facing (cards, sparklines, badges, tables, empty states) lives
here so pages stay declarative and the styling stays consistent with brand.py.
"""
from __future__ import annotations
import streamlit as st

from . import config, data, glossary, state
from . import format as fmt
from .config import METRICS, THEME, display_name, ticker, profile_for


# ---------------------------------------------------------------------------
def sparkline(series: dict[int, float], color: str, width: int = 130, height: int = 34) -> str:
    """Tiny inline trend line for a {year: value} series."""
    ys = sorted(series)
    pts = [series[y] for y in ys]
    if len(pts) < 2:
        return ""
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1
    n = len(pts)
    coords = [((i / (n - 1)) * (width - 6) + 3,
               (height - 3) - ((v - lo) / rng) * (height - 6)) for i, v in enumerate(pts)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = f"3,{height-3} " + poly + f" {width-3},{height-3}"
    lx, ly = coords[-1]
    uid = f"{color[1:]}{width}{int(lx)}{int(ly)}"
    return (
        f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' "
        f"style='display:block'><defs><linearGradient id='g{uid}' x1='0' y1='0' x2='0' y2='1'>"
        f"<stop offset='0' stop-color='{color}' stop-opacity='0.22'/>"
        f"<stop offset='1' stop-color='{color}' stop-opacity='0'/></linearGradient></defs>"
        f"<polygon points='{area}' fill='url(#g{uid})'/>"
        f"<polyline points='{poly}' fill='none' stroke='{color}' stroke-width='1.8' "
        f"stroke-linecap='round' stroke-linejoin='round'/>"
        f"<circle cx='{lx:.1f}' cy='{ly:.1f}' r='2.4' fill='{color}'/></svg>"
    )


def _card(label: str, value: str, delta_html: str = "", sub: str = "", spark: str = "") -> None:
    st.markdown(
        f"""<div style="background:{THEME['panel']};border:1px solid {THEME['border']};
        border-radius:12px;padding:13px 15px;height:100%">
        <div style="font-size:11.5px;color:{THEME['muted']};text-transform:uppercase;
        letter-spacing:.4px;margin-bottom:6px">{label}</div>
        <div class="lux-num" style="font-size:23px;font-weight:600;color:{THEME['text']};
        line-height:1.05">{value}</div>
        <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:6px">
        <div>{delta_html} <span style="color:{THEME['faint']};font-size:11px">{sub}</span></div>
        <div style="opacity:.9">{spark}</div></div></div>""",
        unsafe_allow_html=True,
    )


def pill(text: str, color: str, bg: str | None = None) -> str:
    bg = bg or THEME["panel2"]
    return (f"<span style='background:{bg};color:{color};padding:2px 8px;border-radius:20px;"
            f"font-size:11px;font-weight:600;white-space:nowrap'>{text}</span>")


def section_title(text: str, sub: str = "") -> None:
    extra = (f"<span style='color:{THEME['faint']};font-size:13px;font-weight:400;margin-left:8px'>"
             f"{sub}</span>") if sub else ""
    st.markdown(f"<div style='margin:20px 0 8px'><span style='font-size:15px;font-weight:600;"
                f"color:{THEME['text']}'>{text}</span>{extra}</div>", unsafe_allow_html=True)


def empty_state(msg: str, hint: str = "") -> None:
    st.markdown(
        f"""<div style="background:{THEME['panel']};border:1px dashed {THEME['border2']};
        border-radius:12px;padding:30px;text-align:center;color:{THEME['muted']};margin:8px 0">
        <div style="font-size:15px;color:{THEME['text']};margin-bottom:4px">{msg}</div>
        <div style="font-size:12.5px">{hint}</div></div>""",
        unsafe_allow_html=True,
    )


def disclaimer() -> None:
    st.markdown(
        f"<div style='color:{THEME['faint']};font-size:11.5px;margin:6px 0 2px'>"
        f"Educational summary generated from 2021–2025 filings — not investment advice.</div>",
        unsafe_allow_html=True)


# ---------------------------------------------------------------------------
def company_header(company: str) -> None:
    sector = data.company_sector(company)
    tk = ticker(company)
    fye = config.NON_DECEMBER_FYE.get(company)
    partial = len(data.years_for(company)) < len(config.YEARS)
    chips = [f"<span style='color:{THEME['muted']};font-size:13px'>{sector}</span>"]
    if tk:
        chips.append(pill(tk, THEME["text"], THEME["panel2"]))
    if fye:
        chips.append(pill(f"FY-end {fye}", THEME["accent"], THEME["accent_soft"]))
    if partial:
        yrs = data.years_for(company)
        chips.append(pill(f"Limited history {min(yrs)}–{max(yrs)}", THEME["accent"], THEME["accent_soft"]))
    st.markdown(
        f"<h1 style='margin:0 0 4px;font-size:30px'>{display_name(company)}</h1>"
        f"<div style='display:flex;gap:10px;align-items:center;margin-bottom:2px'>{' '.join(chips)}</div>",
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
    ocr_chip = "  " + pill("OCR-extracted", THEME["accent"], THEME["accent_soft"]) if ocr else ""
    st.markdown(
        f"<div style='font-size:12px;color:{THEME['faint']};margin:8px 0 4px'>"
        f"Data confidence · FY{year} &nbsp;"
        f"<span style='color:{color};font-weight:600'>● {label}</span>{ocr_chip}</div>",
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


def _delta_html(key: str, new, old) -> str:
    d = fmt.delta_pct(new, old)
    if d is None:
        return f"<span style='color:{THEME['faint']};font-size:12px'>—</span>"
    good = METRICS.get(key, {}).get("good")
    up = d >= 0
    if good == "up":
        color = THEME["pos"] if up else THEME["neg"]
    elif good == "down":
        color = THEME["neg"] if up else THEME["pos"]
    else:
        color = THEME["muted"]
    return f"<span style='color:{color};font-size:12px;font-weight:600'>{'▲' if up else '▼'} {fmt.pct(abs(d))}</span>"


def kpi_row(company: str) -> None:
    cols = st.columns(len(config.KPI_CARDS))
    for col, key in zip(cols, config.KPI_CARDS):
        s = data.series(company, key)
        with col:
            if not s:
                _card(METRICS[key]["short"], fmt.DASH)
                continue
            ys = sorted(s)
            last = s[ys[-1]]
            prev = s[ys[-2]] if len(ys) >= 2 else None
            # sparkline colour: trend direction weighted by whether up is good
            good = METRICS[key].get("good")
            rising = len(ys) >= 2 and s[ys[-1]] >= s[ys[0]]
            spark_color = THEME["muted"]
            if good == "up":
                spark_color = THEME["pos"] if rising else THEME["neg"]
            elif good == "down":
                spark_color = THEME["neg"] if rising else THEME["pos"]
            else:
                spark_color = THEME["accent"]
            _card(METRICS[key]["short"], fmt.metric(key, last),
                  _delta_html(key, last, prev), sub=f"FY{ys[-1]}",
                  spark=sparkline(s, spark_color))


# ---------------------------------------------------------------------------
def statement_table(company: str, group: str, title: str) -> None:
    profile = profile_for(data.company_sector(company))
    keys = config.PROFILES[profile][group]
    years = data.years_for(company)
    if not years:
        return
    rows_html = []
    for key in keys:
        s = data.series(company, key)
        if not s:
            continue
        defn = glossary.define(key)
        tip = (defn["definition"] if defn else "")
        cells = "".join(
            f"<td class='lux-num' style='text-align:right;padding:6px 12px;color:{THEME['text']}'>"
            f"{fmt.metric(key, s.get(y))}</td>" for y in years
        )
        rows_html.append(
            f"<tr style='border-top:1px solid {THEME['grid']}'>"
            f"<td style='padding:6px 12px;color:{THEME['muted']}' title=\"{tip}\">{METRICS[key]['label']}</td>"
            f"{cells}</tr>"
        )
    if not rows_html:
        return
    head = "".join(f"<th style='text-align:right;padding:6px 12px;color:{THEME['faint']};"
                   f"font-weight:600;font-size:12px'>FY{y}</th>" for y in years)
    st.markdown(f"<div style='font-size:13px;font-weight:600;color:{THEME['text']};margin:16px 0 2px'>{title}</div>",
                unsafe_allow_html=True)
    st.markdown(
        f"""<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead><tr><th style='text-align:left;padding:6px 12px'></th>{head}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody></table></div>""",
        unsafe_allow_html=True,
    )


def company_button(company: str, key_prefix: str, right: str = "", right_color: str | None = None) -> None:
    """A clickable company row with an optional right-aligned value."""
    if right:
        c1, c2 = st.columns([5, 2])
        with c1:
            if st.button(display_name(company), key=f"{key_prefix}_{company}", use_container_width=True):
                state.open_company(company)
        c2.markdown(f"<div class='lux-num' style='text-align:right;padding-top:7px;"
                    f"color:{right_color or THEME['text']};font-weight:600'>{right}</div>",
                    unsafe_allow_html=True)
    else:
        if st.button(display_name(company), key=f"{key_prefix}_{company}", use_container_width=True):
            state.open_company(company)
