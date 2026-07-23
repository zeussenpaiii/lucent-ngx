"""
report.py — Generate a self-contained, print-ready company report (HTML).

Produces a single branded HTML file a user can download, open in any browser,
and print/save as PDF — the "share one company's summary" path. Light-themed
so it prints cleanly. All content comes from the dataset + Narrative Engine.
"""
from __future__ import annotations
import datetime as _dt

from . import config, data, narrative
from . import format as fmt
from .config import METRICS, display_name, ticker, profile_for


def _kpi_cells(company: str) -> str:
    out = []
    for key in config.KPI_CARDS:
        s = data.series(company, key)
        if not s:
            continue
        ys = sorted(s)
        val = fmt.metric(key, s[ys[-1]])
        delta = ""
        if len(ys) >= 2:
            d = fmt.delta_pct(s[ys[-1]], s[ys[-2]])
            if d is not None:
                good = METRICS[key].get("good")
                up = d >= 0
                col = "#1a7f37" if (up == (good != "down")) else "#b42318"
                delta = f"<span style='color:{col};font-size:12px'>{'▲' if up else '▼'} {fmt.pct(abs(d))}</span>"
        out.append(
            f"<div class='kpi'><div class='kpi-l'>{METRICS[key]['short']}</div>"
            f"<div class='kpi-v'>{val}</div><div>{delta} <span class='muted'>FY{ys[-1]}</span></div></div>")
    return "".join(out)


def _ratio_rows(company: str) -> str:
    profile = profile_for(data.company_sector(company))
    keys = config.PROFILES[profile]["ratio"]
    years = data.years_for(company)
    rows = ""
    for key in keys:
        s = data.series(company, key)
        if not s:
            continue
        cells = "".join(f"<td class='num'>{fmt.metric(key, s.get(y))}</td>" for y in years)
        rows += f"<tr><td>{METRICS[key]['label']}</td>{cells}</tr>"
    head = "".join(f"<th class='num'>FY{y}</th>" for y in years)
    return (f"<table class='rt'><thead><tr><th></th>{head}</tr></thead><tbody>{rows}</tbody></table>"
            if rows else "")


def _prose(sections: dict, key: str) -> str:
    v = sections.get(key)
    if not v:
        return ""
    return f"<h3>{key}</h3><p>{v}</p>"


def _list(sections: dict, key: str, color: str) -> str:
    items = sections.get(key, [])
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f"<div class='col'><h4 style='color:{color}'>{key}</h4><ul>{lis}</ul></div>"


def company_report_html(company: str) -> str:
    name = display_name(company)
    sector = data.company_sector(company)
    tk = ticker(company)
    years = data.years_for(company)
    span = f"FY{min(years)}–FY{max(years)}" if years else ""
    today = _dt.date.today().strftime("%d %b %Y")
    s = narrative.generate(company)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} — {config.BRAND} report</title>
<style>
  * {{ box-sizing:border-box; }}
  body {{ font-family:'Inter',system-ui,Arial,sans-serif; color:#1a1d21; background:#f4f4f2;
         margin:0; padding:28px; line-height:1.5; }}
  .page {{ max-width:820px; margin:0 auto; background:#fff; border:1px solid #e6e6e3;
          border-radius:14px; padding:34px 40px; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
  .brand {{ display:flex;align-items:center;justify-content:space-between;
           border-bottom:2px solid #E3B341; padding-bottom:12px; margin-bottom:18px; }}
  .brand .name {{ font-weight:700; font-size:19px; letter-spacing:.3px; }}
  .brand .name b {{ color:#B8860B; }}
  .brand .meta {{ text-align:right; font-size:12px; color:#6b7075; }}
  h1 {{ font-size:26px; margin:2px 0 2px; }}
  .sub {{ color:#6b7075; font-size:13.5px; margin-bottom:16px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:14px 0 20px; }}
  .kpi {{ border:1px solid #ececea; border-radius:10px; padding:10px 12px; }}
  .kpi-l {{ font-size:11px; text-transform:uppercase; letter-spacing:.4px; color:#8a8f95; }}
  .kpi-v {{ font-size:20px; font-weight:700; margin:2px 0; }}
  .muted {{ color:#9aa0a6; font-size:11px; }}
  .summary {{ background:#fbf7ec; border:1px solid #f0e4c3; border-radius:10px; padding:14px 16px; margin-bottom:6px; }}
  .summary .lbl {{ font-size:11px; text-transform:uppercase; letter-spacing:.5px; color:#B8860B; font-weight:600; }}
  h3 {{ font-size:15px; margin:16px 0 3px; }}
  h4 {{ font-size:13.5px; margin:0 0 6px; }}
  p {{ margin:0 0 8px; font-size:13.5px; }}
  .cols {{ display:flex; gap:20px; margin:10px 0; }}
  .col {{ flex:1; }}
  .col ul {{ margin:0; padding-left:16px; }}
  .col li {{ font-size:12.5px; margin:3px 0; }}
  table.rt {{ width:100%; border-collapse:collapse; font-size:12.5px; margin:6px 0 4px; }}
  table.rt th, table.rt td {{ padding:5px 8px; border-bottom:1px solid #eee; text-align:left; }}
  table.rt .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  table.rt thead th {{ color:#8a8f95; font-weight:600; border-bottom:1px solid #ddd; }}
  .foot {{ margin-top:20px; padding-top:12px; border-top:1px solid #eee; font-size:11px; color:#9aa0a6; }}
  @media print {{ body {{ background:#fff; padding:0; }} .page {{ border:none; box-shadow:none; }} }}
</style></head><body><div class="page">
  <div class="brand">
    <div class="name">✦ <b>{config.BRAND}</b></div>
    <div class="meta">{config.APP_DESCRIPTOR}<br>Generated {today}</div>
  </div>
  <h1>{name}</h1>
  <div class="sub">{sector}{' · ' + tk if tk else ''} · {span}</div>

  <div class="kpis">{_kpi_cells(company)}</div>

  <div class="summary"><div class="lbl">Executive Summary</div>
    <div style="font-size:14px;margin-top:4px">{s.get('Executive Summary','')}</div></div>

  {_prose(s, 'Growth')}
  {_prose(s, 'Profitability')}
  {_prose(s, 'Balance Sheet')}
  {_prose(s, 'Cash Flow')}

  <h3>Key ratios</h3>
  {_ratio_rows(company)}

  <div class="cols">
    {_list(s, 'Strengths', '#1a7f37')}
    {_list(s, 'Weaknesses', '#b42318')}
    {_list(s, 'Risks', '#B8860B')}
  </div>

  {_prose(s, 'Overall Assessment')}

  <div class="foot">{config.BRAND} · Educational summary from 2021–2025 company filings — <b>not investment
  advice</b>. Ratios use average-balance methodology as stored in the source dataset.
  © {config.BRAND_YEAR} {config.BRAND}.</div>
</div></body></html>"""
