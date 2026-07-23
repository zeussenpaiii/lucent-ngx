"""
charts.py — Plotly chart builders with one shared dark theme.

Charts scale Naira series to a sensible unit (trn/bn/m) so axes read cleanly,
render ratios as %, and expose a sector-median reference where useful. Every
figure is self-contained and safe to render even with 3-year series.
"""
from __future__ import annotations
import plotly.graph_objects as go

from . import config, data
from .config import METRICS, THEME, SERIES_COLORS

_FONT = "Inter, system-ui, -apple-system, Segoe UI, sans-serif"


def _layout(fig: go.Figure, title: str, ytitle: str = "", height: int = 300) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=THEME["text"])),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT, color=THEME["muted"], size=12),
        height=height,
        margin=dict(l=10, r=10, t=44, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=THEME["muted"],
                     tickmode="linear", dtick=1)
    fig.update_yaxes(showgrid=True, gridcolor=THEME["grid"], zeroline=False,
                     color=THEME["muted"], title=dict(text=ytitle, font=dict(size=11)))
    return fig


def _naira_scale(values) -> tuple[float, str]:
    m = max((abs(v) for v in values if v is not None), default=0)
    if m >= 1e12:
        return 1e12, "₦ trillion"
    if m >= 1e9:
        return 1e9, "₦ billion"
    if m >= 1e6:
        return 1e6, "₦ million"
    return 1.0, "₦"


def _prep(series: dict[int, float], fmt: str):
    """Return (xs, ys_scaled, axis_title, hover_suffix, hover_prefix)."""
    xs = sorted(series)
    raw = [series[x] for x in xs]
    if fmt == "naira":
        factor, title = _naira_scale(raw)
        return xs, [v / factor for v in raw], title, "", "₦"
    if fmt == "pct":
        return xs, [v * 100 for v in raw], "%", "%", ""
    if fmt == "x":
        return xs, raw, "x", "x", ""
    if fmt == "per_share":
        return xs, raw, "₦ per share", "", "₦"
    return xs, raw, "", "", ""


def line(series_map: dict[str, dict[int, float]], fmt: str, title: str,
         reference: tuple[str, dict[int, float]] | None = None, height: int = 300) -> go.Figure:
    fig = go.Figure()
    axis_title = ""
    for i, (name, s) in enumerate(series_map.items()):
        if not s:
            continue
        xs, ys, axis_title, suf, _ = _prep(s, fmt)
        fig.add_trace(go.Scatter(
            x=xs, y=ys, name=name, mode="lines+markers",
            line=dict(color=SERIES_COLORS[i % len(SERIES_COLORS)], width=2.5),
            marker=dict(size=6),
            hovertemplate="%{y:,.2f}" + suf + "<extra>" + name + "</extra>",
        ))
    if reference is not None:
        rname, rs = reference
        if rs:
            xs, ys, axis_title, suf, _ = _prep(rs, fmt)
            fig.add_trace(go.Scatter(
                x=xs, y=ys, name=rname, mode="lines",
                line=dict(color=THEME["muted"], width=1.5, dash="dash"),
                hovertemplate="%{y:,.2f}" + suf + "<extra>" + rname + "</extra>",
            ))
    return _layout(fig, title, axis_title, height)


def bars(series: dict[int, float], fmt: str, title: str, color: str | None = None,
         height: int = 300) -> go.Figure:
    xs, ys, axis_title, suf, _ = _prep(series, fmt)
    colors = [THEME["neg"] if (v is not None and v < 0) else (color or THEME["accent"]) for v in ys]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors,
                           hovertemplate="%{y:,.2f}" + suf + "<extra></extra>"))
    return _layout(fig, title, axis_title, height)


def grouped_bars(series_map: dict[str, dict[int, float]], fmt: str, title: str,
                 height: int = 300) -> go.Figure:
    fig = go.Figure()
    axis_title = ""
    for i, (name, s) in enumerate(series_map.items()):
        xs, ys, axis_title, suf, _ = _prep(s, fmt)
        fig.add_trace(go.Bar(x=xs, y=ys, name=name,
                             marker_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                             hovertemplate="%{y:,.2f}" + suf + "<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    return _layout(fig, title, axis_title, height)


def revenue_vs_pat(company: str) -> go.Figure:
    return grouped_bars(
        {"Revenue": data.series(company, "gross_earnings"),
         "PAT": data.series(company, "profit_after_tax")},
        "naira", "Revenue vs Profit After Tax",
    )


def ratio_vs_median(company: str, sector: str, metric: str) -> go.Figure:
    s = data.series(company, metric)
    years = sorted(s)
    med = {y: data.sector_median(sector, metric, y) for y in years}
    med = {y: v for y, v in med.items() if v is not None}
    label = METRICS[metric]["short"]
    return line({label: s}, METRICS[metric]["fmt"], f"{label} vs sector median",
                reference=("Sector median", med))


def horizontal_ranking(pairs: list[tuple[str, float]], fmt: str, title: str,
                       highlight: str | None = None) -> go.Figure:
    pairs = [p for p in pairs if p[1] is not None]
    names = [p[0] for p in pairs][::-1]
    vals = [p[1] for p in pairs][::-1]
    if fmt == "pct":
        vals = [v * 100 for v in vals]; suf = "%"
    elif fmt == "naira":
        factor, unit = _naira_scale(vals); vals = [v / factor for v in vals]; suf = f" ({unit})"
    elif fmt == "x":
        suf = "x"
    else:
        suf = ""
    colors = [THEME["warn"] if (highlight and n == highlight) else THEME["accent"] for n in names]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker_color=colors,
        hovertemplate="%{x:,.2f}<extra>%{y}</extra>",
    ))
    fig.update_layout(
        title=dict(text=title + (suf if fmt == "naira" else ""), font=dict(size=15, color=THEME["text"])),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=_FONT, color=THEME["muted"], size=12),
        height=max(300, 26 * len(names) + 60),
        margin=dict(l=10, r=10, t=44, b=10),
    )
    fig.update_xaxes(showgrid=True, gridcolor=THEME["grid"], color=THEME["muted"])
    fig.update_yaxes(showgrid=False, color=THEME["text"], tickfont=dict(size=11))
    return fig
