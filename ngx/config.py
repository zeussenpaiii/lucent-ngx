"""
config.py — Single source of truth for the NGX Intelligence Workspace.

Holds the analysis window, the metric registry (labels / units / formatting /
direction), the sector -> statement-layout profiles, and company display names.
No Streamlit or pandas imports here so it stays cheap to import anywhere.
"""
from __future__ import annotations

APP_NAME = "NGX Intelligence Workspace"
APP_TAGLINE = "Financial intelligence on 35 NGX-listed companies · 2021–2025"

# --- analysis window -------------------------------------------------------
YEAR_MIN, YEAR_MAX = 2021, 2025
YEARS = list(range(YEAR_MIN, YEAR_MAX + 1))
CURRENCY = "NGN"
DATA_FILE = "data/ngx_2021_2025.csv"

# Optional LLM layer stays OFF for the offline prototype. The Narrative Engine
# (deterministic, grounded) is always on and needs no key.
ENABLE_LLM = False

# --- theme (dark) ----------------------------------------------------------
THEME = {
    "bg": "#0d1117",
    "panel": "#161b22",
    "panel2": "#1c2333",
    "border": "#2a3038",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "accent": "#3b82f6",   # blue
    "pos": "#3fb950",      # green
    "neg": "#f85149",      # red
    "warn": "#d29922",     # amber
    "grid": "#21262d",
}
# Qualitative palette for multi-series charts (colour-blind aware, dark-safe).
SERIES_COLORS = ["#3b82f6", "#3fb950", "#d29922", "#a371f7", "#f85149", "#2dd4bf"]

# ---------------------------------------------------------------------------
# METRIC REGISTRY
#   label : full name
#   short : compact label for cards / tables
#   group : income | balance | cashflow | ratio | market
#   fmt   : naira | pct | x | per_share | count
#   good  : "up" (higher better) | "down" (lower better) | None (neutral)
# ---------------------------------------------------------------------------
METRICS: dict[str, dict] = {
    # Income statement
    "gross_earnings":            {"label": "Revenue / Gross Earnings", "short": "Revenue",      "group": "income",   "fmt": "naira", "good": "up"},
    "net_interest_income":       {"label": "Net Interest Income",      "short": "Net Int. Inc.", "group": "income",   "fmt": "naira", "good": "up"},
    "net_premium_income":        {"label": "Net Premium Income",       "short": "Net Premium",  "group": "income",   "fmt": "naira", "good": "up"},
    "net_claims_incurred":       {"label": "Net Claims Incurred",      "short": "Net Claims",   "group": "income",   "fmt": "naira", "good": "down"},
    "cost_of_sales":             {"label": "Cost of Sales",            "short": "COGS",         "group": "income",   "fmt": "naira", "good": "down"},
    "gross_profit":              {"label": "Gross Profit",             "short": "Gross Profit", "group": "income",   "fmt": "naira", "good": "up"},
    "operating_expenses":        {"label": "Operating Expenses",       "short": "OpEx",         "group": "income",   "fmt": "naira", "good": "down"},
    "operating_profit":          {"label": "Operating Profit",         "short": "Op. Profit",   "group": "income",   "fmt": "naira", "good": "up"},
    "depreciation_amortization": {"label": "Depreciation & Amort.",    "short": "D&A",          "group": "income",   "fmt": "naira", "good": None},
    "ebitda":                    {"label": "EBITDA",                   "short": "EBITDA",       "group": "income",   "fmt": "naira", "good": "up"},
    "finance_cost":              {"label": "Finance Cost",             "short": "Fin. Cost",    "group": "income",   "fmt": "naira", "good": "down"},
    "impairment_loan_loss":      {"label": "Impairment / Loan Loss",   "short": "Impairment",   "group": "income",   "fmt": "naira", "good": "down"},
    "profit_before_tax":         {"label": "Profit Before Tax",        "short": "PBT",          "group": "income",   "fmt": "naira", "good": "up"},
    "income_tax_expense":        {"label": "Income Tax Expense",       "short": "Tax",          "group": "income",   "fmt": "naira", "good": "down"},
    "profit_after_tax":          {"label": "Profit After Tax",         "short": "PAT",          "group": "income",   "fmt": "naira", "good": "up"},
    "nci_profit_after_tax":      {"label": "Non-controlling PAT",      "short": "NCI PAT",      "group": "income",   "fmt": "naira", "good": None},
    # Balance sheet
    "total_assets":              {"label": "Total Assets",             "short": "Assets",       "group": "balance",  "fmt": "naira", "good": "up"},
    "current_assets":            {"label": "Current Assets",           "short": "Cur. Assets",  "group": "balance",  "fmt": "naira", "good": "up"},
    "net_loans_advances":        {"label": "Net Loans & Advances",     "short": "Net Loans",    "group": "balance",  "fmt": "naira", "good": "up"},
    "total_liabilities":         {"label": "Total Liabilities",        "short": "Liabilities",  "group": "balance",  "fmt": "naira", "good": None},
    "current_liabilities":       {"label": "Current Liabilities",      "short": "Cur. Liab.",   "group": "balance",  "fmt": "naira", "good": None},
    "customer_deposits":         {"label": "Customer Deposits",        "short": "Deposits",     "group": "balance",  "fmt": "naira", "good": "up"},
    "interest_bearing_debt":     {"label": "Interest-bearing Debt",    "short": "Debt",         "group": "balance",  "fmt": "naira", "good": "down"},
    "total_equity":              {"label": "Total Equity",             "short": "Equity",       "group": "balance",  "fmt": "naira", "good": "up"},
    "nci_total_equity":          {"label": "Non-controlling Equity",   "short": "NCI Equity",   "group": "balance",  "fmt": "naira", "good": None},
    "retained_earnings":         {"label": "Retained Earnings",        "short": "Ret. Earn.",   "group": "balance",  "fmt": "naira", "good": "up"},
    "cash_and_equivalents":      {"label": "Cash & Equivalents",       "short": "Cash",         "group": "balance",  "fmt": "naira", "good": "up"},
    "working_capital":           {"label": "Working Capital",          "short": "Work. Cap.",   "group": "balance",  "fmt": "naira", "good": "up"},
    # Cash flow
    "net_cash_from_operations":  {"label": "Cash from Operations",     "short": "CFO",          "group": "cashflow", "fmt": "naira", "good": "up"},
    "net_cash_from_investing":   {"label": "Cash from Investing",      "short": "CFI",          "group": "cashflow", "fmt": "naira", "good": None},
    "net_cash_from_financing":   {"label": "Cash from Financing",      "short": "CFF",          "group": "cashflow", "fmt": "naira", "good": None},
    "capex":                     {"label": "Capital Expenditure",      "short": "CapEx",        "group": "cashflow", "fmt": "naira", "good": None},
    "free_cash_flow":            {"label": "Free Cash Flow",           "short": "FCF",          "group": "cashflow", "fmt": "naira", "good": "up"},
    # Fund / AM specific
    "aum":                       {"label": "Assets Under Management",  "short": "AUM",          "group": "balance",  "fmt": "naira", "good": "up"},
    "nav_total":                 {"label": "Net Asset Value (total)",  "short": "NAV",          "group": "balance",  "fmt": "naira", "good": "up"},
    # Market / per-share
    "eps_basic":                 {"label": "Earnings per Share",       "short": "EPS",          "group": "market",   "fmt": "per_share", "good": "up"},
    "dividend_per_share":        {"label": "Dividend per Share",       "short": "DPS",          "group": "market",   "fmt": "per_share", "good": "up"},
    "nav_per_unit":              {"label": "NAV per Unit",             "short": "NAV/unit",     "group": "market",   "fmt": "per_share", "good": "up"},
    "shares_outstanding":        {"label": "Shares Outstanding",       "short": "Shares",       "group": "market",   "fmt": "count", "good": None},
    "units_in_issue":            {"label": "Units in Issue",           "short": "Units",        "group": "market",   "fmt": "count", "good": None},
    # Ratios (stored as decimals)
    "net_margin":                {"label": "Net Margin",               "short": "Net Margin",   "group": "ratio", "fmt": "pct", "good": "up"},
    "gross_margin":              {"label": "Gross Margin",             "short": "Gross Margin", "group": "ratio", "fmt": "pct", "good": "up"},
    "operating_margin":          {"label": "Operating Margin",         "short": "Op. Margin",   "group": "ratio", "fmt": "pct", "good": "up"},
    "ebitda_margin":             {"label": "EBITDA Margin",            "short": "EBITDA Margin","group": "ratio", "fmt": "pct", "good": "up"},
    "roe":                       {"label": "Return on Equity",         "short": "ROE",          "group": "ratio", "fmt": "pct", "good": "up"},
    "roa":                       {"label": "Return on Assets",         "short": "ROA",          "group": "ratio", "fmt": "pct", "good": "up"},
    "payout_ratio":              {"label": "Dividend Payout Ratio",    "short": "Payout",       "group": "ratio", "fmt": "pct", "good": None},
    "debt_to_equity":            {"label": "Debt to Equity",           "short": "D/E",          "group": "ratio", "fmt": "x",   "good": "down"},
    "current_ratio":             {"label": "Current Ratio",            "short": "Current Ratio","group": "ratio", "fmt": "x",   "good": "up"},
}

# Metrics that exist in ~every company/year (the "universal spine").
UNIVERSAL_SPINE = [
    "gross_earnings", "profit_before_tax", "profit_after_tax",
    "total_assets", "total_liabilities", "total_equity", "cash_and_equivalents",
    "eps_basic", "dividend_per_share", "net_margin", "roe", "roa",
]

# KPI hero cards on the company workspace (in order).
KPI_CARDS = ["gross_earnings", "profit_after_tax", "roe", "net_margin", "eps_basic", "total_assets"]

# ---------------------------------------------------------------------------
# SECTOR PROFILES — statement layouts keyed by profile, mapped from NGX sector.
# The renderer shows only rows that actually have data for the company, so an
# imperfect profile still degrades gracefully.
# ---------------------------------------------------------------------------
SECTOR_TO_PROFILE = {
    "Banking": "bank",
    "Insurance": "insurance",
    "Closed-End Fund": "fund",
    "Asset Management": "financial",
    # everything else uses the trading-company layout
    "Consumer Goods": "corporate",
    "Industrial Goods": "corporate",
    "Oil & Gas": "corporate",
    "Agriculture": "corporate",
    "Telecommunications": "corporate",
    "Conglomerates": "corporate",
    "Hospitality": "corporate",
    "Utilities": "corporate",
}
DEFAULT_PROFILE = "corporate"

PROFILES: dict[str, dict[str, list[str]]] = {
    "corporate": {
        "income":   ["gross_earnings", "cost_of_sales", "gross_profit", "operating_expenses",
                     "operating_profit", "depreciation_amortization", "ebitda", "finance_cost",
                     "profit_before_tax", "income_tax_expense", "profit_after_tax"],
        "balance":  ["total_assets", "current_assets", "cash_and_equivalents", "total_liabilities",
                     "current_liabilities", "interest_bearing_debt", "total_equity", "retained_earnings"],
        "cashflow": ["net_cash_from_operations", "net_cash_from_investing", "net_cash_from_financing",
                     "capex", "free_cash_flow"],
        "ratio":    ["net_margin", "gross_margin", "operating_margin", "ebitda_margin", "roe", "roa",
                     "current_ratio", "debt_to_equity", "payout_ratio"],
    },
    "bank": {
        "income":   ["gross_earnings", "net_interest_income", "impairment_loan_loss",
                     "operating_expenses", "profit_before_tax", "income_tax_expense", "profit_after_tax"],
        "balance":  ["total_assets", "net_loans_advances", "customer_deposits", "cash_and_equivalents",
                     "total_liabilities", "total_equity", "retained_earnings"],
        "cashflow": ["net_cash_from_operations", "net_cash_from_investing", "net_cash_from_financing"],
        "ratio":    ["net_margin", "roe", "roa", "debt_to_equity", "payout_ratio"],
    },
    "insurance": {
        "income":   ["gross_earnings", "net_premium_income", "net_claims_incurred",
                     "operating_expenses", "profit_before_tax", "income_tax_expense", "profit_after_tax"],
        "balance":  ["total_assets", "cash_and_equivalents", "total_liabilities", "total_equity", "retained_earnings"],
        "cashflow": ["net_cash_from_operations", "net_cash_from_investing", "net_cash_from_financing"],
        "ratio":    ["net_margin", "roe", "roa", "debt_to_equity", "payout_ratio"],
    },
    "financial": {
        "income":   ["gross_earnings", "operating_expenses", "profit_before_tax",
                     "income_tax_expense", "profit_after_tax"],
        "balance":  ["total_assets", "cash_and_equivalents", "total_liabilities", "total_equity", "retained_earnings"],
        "cashflow": ["net_cash_from_operations", "net_cash_from_investing", "net_cash_from_financing"],
        "ratio":    ["net_margin", "roe", "roa", "debt_to_equity", "payout_ratio"],
    },
    "fund": {
        "income":   ["gross_earnings", "operating_expenses", "profit_before_tax", "profit_after_tax"],
        "balance":  ["total_assets", "aum", "nav_total", "total_equity"],
        "cashflow": ["net_cash_from_operations", "net_cash_from_investing", "net_cash_from_financing"],
        "ratio":    ["roe", "roa", "payout_ratio"],
    },
}

# Charts to render on the company workspace (built only if data present).
COMPANY_CHARTS = [
    ("gross_earnings", "PAT vs Revenue"),   # special combined handled in charts.py
]

# ---------------------------------------------------------------------------
# COMPANY DISPLAY — pretty name + NGX ticker (labels only, not analytical data)
# ---------------------------------------------------------------------------
COMPANY_DISPLAY: dict[str, dict[str, str]] = {
    "ACCESS HOLDINGS":                  {"name": "Access Holdings",           "ticker": "ACCESSCORP"},
    "AIRTEL AFRICA":                    {"name": "Airtel Africa",             "ticker": "AIRTELAFRI"},
    "ARADEL HOLDINGS":                  {"name": "Aradel Holdings",           "ticker": "ARADEL"},
    "AXA MANSARD INSURANCE":            {"name": "AXA Mansard Insurance",     "ticker": "AXAMANSARD"},
    "BUA CEMENT":                       {"name": "BUA Cement",                "ticker": "BUACEMENT"},
    "BUA FOODS":                        {"name": "BUA Foods",                 "ticker": "BUAFOODS"},
    "CHAPEL HILL DENHAM":               {"name": "Chapel Hill Denham (NIDF)", "ticker": "NIDF"},
    "CUSTODIAN INVESTMENT":             {"name": "Custodian Investment",      "ticker": "CUSTODIAN"},
    "DANGOTE CEMENT":                   {"name": "Dangote Cement",            "ticker": "DANGCEM"},
    "DANGOTE SUGAR":                    {"name": "Dangote Sugar Refinery",    "ticker": "DANGSUGAR"},
    "ECO BANK":                         {"name": "Ecobank (ETI)",             "ticker": "ETI"},
    "FCMB GROUP":                       {"name": "FCMB Group",                "ticker": "FCMB"},
    "FIDELITY BANK":                    {"name": "Fidelity Bank",             "ticker": "FIDELITYBK"},
    "FIRSTBANK":                        {"name": "First HoldCo",              "ticker": "FIRSTHOLDCO"},
    "GEREGU":                           {"name": "Geregu Power",              "ticker": "GEREGU"},
    "GUARANTY TRUST HOLDING COMPANY":   {"name": "GTCO",                      "ticker": "GTCO"},
    "GUINNESS NIG":                     {"name": "Guinness Nigeria",          "ticker": "GUINNESS"},
    "INTERNATIONAL BREWERIES":          {"name": "International Breweries",   "ticker": "INTBREW"},
    "JAIZBANK":                         {"name": "Jaiz Bank",                 "ticker": "JAIZBANK"},
    "LAFARGE AFRICA":                   {"name": "Lafarge Africa",            "ticker": "WAPCO"},
    "MTN NIGERIA COMMUNICATIONS":       {"name": "MTN Nigeria",              "ticker": "MTNN"},
    "NESTLE NIGERIA":                   {"name": "Nestlé Nigeria",            "ticker": "NESTLE"},
    "NIGERIAN BREWERIES":               {"name": "Nigerian Breweries",       "ticker": "NB"},
    "OKOMU OIL PALM":                   {"name": "Okomu Oil Palm",           "ticker": "OKOMUOIL"},
    "PRESCO":                           {"name": "Presco",                    "ticker": "PRESCO"},
    "SEPLAT ENERGY":                    {"name": "Seplat Energy",             "ticker": "SEPLAT"},
    "STANBIC IBTC HOLDINGS":            {"name": "Stanbic IBTC Holdings",     "ticker": "STANBIC"},
    "STERLING BANK":                    {"name": "Sterling Financial Holdings","ticker": "STERLINGNG"},
    "TOTAL ENERGIES MARKETING NIGERIA": {"name": "TotalEnergies Marketing",  "ticker": "TOTAL"},
    "TRANSCORP HOTELS":                 {"name": "Transcorp Hotels",          "ticker": "TRANSCOHOT"},
    "TRANSNATIONAL CORPORATION":        {"name": "Transcorp",                 "ticker": "TRANSCORP"},
    "UNILEVER NIGERIA":                 {"name": "Unilever Nigeria",          "ticker": "UNILEVER"},
    "UNITED BANK FOR AFRICA":           {"name": "United Bank for Africa",    "ticker": "UBA"},
    "UNITED CAPITAL":                   {"name": "United Capital",            "ticker": "UCAP"},
    "ZENITH BANK":                      {"name": "Zenith Bank",               "ticker": "ZENITHBANK"},
}

# Companies whose fiscal year does not end in December (period-comparability note).
NON_DECEMBER_FYE = {
    "AIRTEL AFRICA": "31 March",
}


def profile_for(sector: str) -> str:
    return SECTOR_TO_PROFILE.get(sector, DEFAULT_PROFILE)


def display_name(company: str) -> str:
    return COMPANY_DISPLAY.get(company, {}).get("name", company.title())


def ticker(company: str) -> str:
    return COMPANY_DISPLAY.get(company, {}).get("ticker", "")
