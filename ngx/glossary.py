"""
glossary.py — Plain-language definitions for the educational layer.

Each entry: what it is, how it's calculated, and how to read it. Surfaced as
tooltips/expanders across the app and as a standalone Glossary page. Static,
offline, human-written — no model involved.
"""
from __future__ import annotations

GLOSSARY: dict[str, dict[str, str]] = {
    "gross_earnings": {
        "definition": "Total income a company generates from its core activities in a year. For banks and insurers this is 'gross earnings' (interest, fees, premiums); for other firms it is revenue/turnover.",
        "formula": "Reported top-line (sales, or interest + fee + other income for financials).",
        "reading": "The starting point of the income statement. Growth over time shows whether the business is expanding.",
    },
    "profit_after_tax": {
        "definition": "What remains for shareholders after all costs, interest and taxes — the 'bottom line'.",
        "formula": "Profit Before Tax − Income Tax Expense.",
        "reading": "The single clearest measure of profitability. Compare its trend against revenue to see if growth is profitable.",
    },
    "profit_before_tax": {
        "definition": "Profit earned before company income tax is deducted.",
        "formula": "Operating profit + other income − finance costs (structure varies by sector).",
        "reading": "Useful for comparing operating performance without tax-rate differences getting in the way.",
    },
    "net_margin": {
        "definition": "How many kobo of profit the company keeps from each naira of revenue.",
        "formula": "Profit After Tax ÷ Revenue.",
        "reading": "Higher is better. A rising margin means the company is getting more efficient or has pricing power.",
    },
    "gross_margin": {
        "definition": "Profit left after the direct cost of producing goods, as a share of revenue.",
        "formula": "Gross Profit ÷ Revenue.",
        "reading": "Reflects production efficiency and pricing power. Not reported by banks (no cost of sales).",
    },
    "operating_margin": {
        "definition": "Profit from core operations as a share of revenue, before financing and tax.",
        "formula": "Operating Profit ÷ Revenue.",
        "reading": "Strips out financing and tax effects to show how well the core business runs.",
    },
    "ebitda_margin": {
        "definition": "Earnings before interest, tax, depreciation and amortisation, as a share of revenue.",
        "formula": "EBITDA ÷ Revenue.",
        "reading": "A rough proxy for cash profitability that ignores capital structure and non-cash charges.",
    },
    "roe": {
        "definition": "Return on Equity — how much profit the company generates on shareholders' money.",
        "formula": "Profit After Tax ÷ Average Shareholders' Equity.",
        "reading": "Higher is better. Banks often run 15–35%; a persistently high ROE signals strong value creation, but very high ROE can also reflect high leverage.",
    },
    "roa": {
        "definition": "Return on Assets — profit generated per naira of assets the company controls.",
        "formula": "Profit After Tax ÷ Average Total Assets.",
        "reading": "Higher is better. Banks look low here (1–4%) because they carry huge balance sheets; compare only within a sector.",
    },
    "eps_basic": {
        "definition": "Earnings per Share — profit attributable to each ordinary share.",
        "formula": "Profit After Tax ÷ Weighted-average shares outstanding.",
        "reading": "Lets you compare profitability per share over time. Affected by share issues and bonuses.",
    },
    "dividend_per_share": {
        "definition": "Cash dividend declared for each ordinary share.",
        "formula": "Total dividend ÷ shares outstanding.",
        "reading": "Shows the income a shareholder receives. Compare with EPS via the payout ratio.",
    },
    "payout_ratio": {
        "definition": "The share of earnings paid out to shareholders as dividends.",
        "formula": "Dividend per Share ÷ Earnings per Share.",
        "reading": "Low means profits are retained to grow; high means most profit is distributed. Above 100% means paying more than it earned.",
    },
    "debt_to_equity": {
        "definition": "How much interest-bearing debt the company uses relative to shareholders' equity.",
        "formula": "Interest-bearing Debt ÷ Total Equity.",
        "reading": "Lower is generally safer. Rising leverage raises both potential returns and risk.",
    },
    "current_ratio": {
        "definition": "Whether short-term assets can cover short-term obligations.",
        "formula": "Current Assets ÷ Current Liabilities.",
        "reading": "Above 1.0x means short-term assets exceed short-term liabilities. Banks don't report this split.",
    },
    "total_assets": {
        "definition": "Everything the company owns or controls that has economic value.",
        "formula": "Sum of current and non-current assets (balance-sheet total).",
        "reading": "A measure of size. For banks this is dominated by loans and cash.",
    },
    "total_equity": {
        "definition": "The shareholders' residual stake after subtracting all liabilities from assets.",
        "formula": "Total Assets − Total Liabilities.",
        "reading": "Also called net worth or book value. Growing equity usually means retained profits.",
    },
    "total_liabilities": {
        "definition": "Everything the company owes to others (deposits, loans, payables, etc.).",
        "formula": "Total Assets − Total Equity.",
        "reading": "For banks, most liabilities are customer deposits — a normal part of the business.",
    },
    "cash_and_equivalents": {
        "definition": "Cash and highly liquid holdings that can be used almost immediately.",
        "formula": "Cash + bank balances + near-cash instruments.",
        "reading": "A cushion for obligations and opportunities. Very low cash can signal liquidity stress.",
    },
    "net_cash_from_operations": {
        "definition": "Cash actually generated by the day-to-day business.",
        "formula": "Cash inflows − outflows from operating activities.",
        "reading": "Healthy companies fund themselves from operations. Compare with PAT — profit without cash is a red flag.",
    },
    "free_cash_flow": {
        "definition": "Cash left after paying to maintain and grow the asset base.",
        "formula": "Cash from Operations − Capital Expenditure.",
        "reading": "What's available for dividends, debt repayment or reinvestment. Negative FCF isn't always bad if the firm is investing to grow.",
    },
    "net_interest_income": {
        "definition": "A bank's core earnings from lending, net of what it pays depositors.",
        "formula": "Interest earned on loans − interest paid on deposits/borrowings.",
        "reading": "The engine of a bank's income statement. Rising NII usually means a bigger or better-priced loan book.",
    },
    "customer_deposits": {
        "definition": "Money customers have placed with the bank.",
        "formula": "Total deposit liabilities.",
        "reading": "A bank's cheapest funding. Growing low-cost deposits is a competitive advantage.",
    },
    "net_loans_advances": {
        "definition": "Loans a bank has extended, net of expected losses.",
        "formula": "Gross loans − impairment allowance.",
        "reading": "The primary earning asset of a bank. Growth drives interest income but adds credit risk.",
    },
    "impairment_loan_loss": {
        "definition": "The charge a bank takes for loans it may not fully recover.",
        "formula": "Provision recognised for expected credit losses.",
        "reading": "Rising impairments signal deteriorating loan quality. Lower is better.",
    },
    "ebitda": {
        "definition": "Earnings before interest, tax, depreciation and amortisation.",
        "formula": "Operating Profit + Depreciation & Amortisation.",
        "reading": "A proxy for operating cash generation that ignores capital structure and non-cash charges.",
    },
    "aum": {
        "definition": "Assets Under Management — the total value of investments a fund manages.",
        "formula": "Market value of all managed holdings.",
        "reading": "The main scale metric for asset managers and funds.",
    },
    "nav_per_unit": {
        "definition": "Net Asset Value per unit — the per-unit book value of a fund.",
        "formula": "Net Asset Value ÷ Units in Issue.",
        "reading": "Tracks the value of a single unit of the fund over time.",
    },
}


def define(key: str) -> dict[str, str] | None:
    return GLOSSARY.get(key)
