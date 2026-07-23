# NGX Intelligence Workspace

An offline, AI-style research workspace over historical financials for **35
NGX-listed companies (2021–2025)**. It turns a static dataset into a browsable
platform: company workspaces, side-by-side comparison, rankings, a deterministic
"AI" narrative analyst, and a plain-language glossary — all running locally with
no APIs, no keys, and no live market data.

> Educational prototype. Historical figures only — **not investment advice**.

---

## Quick start

The app runs on **Python 3.12** (Streamlit does not yet publish wheels for 3.14).
A local `.venv` built with 3.12 is included in the setup below.

```bash
# from the project folder
.venv/Scripts/streamlit run app.py
```

Then open the URL Streamlit prints (default http://localhost:8501).

### Rebuilding the environment from scratch

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
```

### Rebuilding the dataset

The app reads `data/ngx_2021_2025.csv`, generated from the extractor master:

```bash
python scripts/prepare_data.py
```

This slices the master to 2021–2025 and drops five empty scaffolding columns.

---

## What's inside

| Module | Purpose |
|---|---|
| **Home** | Global search, dataset overview, browse-by-sector, featured ROE ranking, suggested questions |
| **Company Workspace** | KPI cards, data-confidence badge, sector-aware statements, charts, AI analysis |
| **Compare** | 2–4 companies side by side, same-sector aware, deterministic verdict |
| **Rankings** | Rank by any metric, all-sectors or within a sector, any year |
| **Glossary** | Plain-language definition + formula + interpretation for every metric |

## Design decisions grounded in the data

- **Sector-aware everything.** The 35 companies span 12 sectors with genuinely
  different line items (banks report deposits/NII; manufacturers report COGS/
  gross margin; insurers report premiums/claims; the fund reports AUM/NAV). Each
  company renders the statement layout for its sector and only shows line items
  it actually reports.
- **Stored ratios are shown as-is.** ROE/ROA use the dataset's average-balance
  methodology; the app never silently recomputes them with closing balances
  (which would disagree with the source).
- **Equity-quality guardrail.** Where the Naira devaluation left a company with a
  near-zero equity base (e.g. Nestlé Nigeria), a raw ROE of ~190% is flagged as
  *distorted* rather than celebrated, and ROA becomes the headline return metric.
- **Provenance surfaced as confidence.** Every filing carries its extraction/
  verification status (`web-verified`, OCR flag, correction log); the workspace
  shows this as a data-confidence badge with a "how we got these numbers" panel.
- **The "AI" is a deterministic Narrative Engine.** It writes the executive
  summary, strengths, weaknesses and risks purely from computed metrics, so it is
  grounded by construction, reproducible, and fully offline. An optional LLM
  adapter is stubbed off (`config.ENABLE_LLM = False`).

## Data notes / caveats

- **Window:** 2021–2025. All 35 companies overlap here except **Chapel Hill
  Denham** (listed 2023 → 3 years; shown with a "limited history" badge).
- **Fiscal calendars differ:** **Airtel Africa** has a 31 March year-end, flagged
  on its workspace — its "FY2025" is not the same period as a December filer's.
- **Currency:** three groups report in **US dollars**, not Naira — **Ecobank
  (ETI)**, **Seplat Energy** and **Airtel Africa**. `scripts/prepare_data.py`
  converts their monetary columns to NGN at World Bank annual-average USD/NGN
  rates, and each is tagged "Reports in USD · converted to NGN" in the app.
  Ratios are unit-independent so they are left untouched. These absolute figures
  are therefore approximate (±~3%); verified against published results:
  Seplat FY2024 → ₦1.65trn (reported ₦1.652trn), Ecobank FY2024 → ₦4.08trn
  (reported ₦4.22trn), Airtel FY2025 → ₦7.61trn ($4,955m × 1535).

## Data quality

`scripts/` includes the corrections; the dataset was audited against the hard
accounting identities that real statements must satisfy:

| Check | Result |
|---|---|
| Assets = Liabilities + Equity | 172/172 (100%) |
| Net margin = PAT ÷ Revenue | 173/173 (100%) |
| Gross profit = Revenue − COGS | 95/95 (100%) |
| EPS ≈ attributable profit ÷ shares | 93% |
| ROE plausibility | 92% |

The EPS/ROE shortfalls are accounting nuances, not bad data: weighted-average
share counts (several banks ran large rights issues in 2024) and companies whose
equity was driven near zero or negative by FX losses, which makes average-vs-
closing ROE diverge. Those cases are flagged in the UI rather than hidden.

## Project structure

```
app.py                 Controller: config, theme, sidebar nav, routing
requirements.txt
data/ngx_2021_2025.csv Shipped dataset (self-contained)
scripts/prepare_data.py
ngx/
  config.py            Metric registry, sector profiles, display names
  data.py              Cached data-access layer
  format.py            Naira / % / multiple formatting
  metrics.py           CAGR, YoY, sector median & percentile
  glossary.py          Metric definitions
  narrative.py         Deterministic Narrative Engine
  charts.py            Themed Plotly builders
  ui.py                Reusable components (cards, badges, tables)
  state.py             Session state + navigation
  views/               Home / Company / Compare / Rankings / Glossary
```
