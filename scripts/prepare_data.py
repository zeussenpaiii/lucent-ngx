"""
prepare_data.py — Build the shipped dataset for the NGX Intelligence Workspace.

Reads the extractor master CSV, slices to the clean 2021-2025 window, drops the
five empty scaffolding columns, and writes a self-contained data file into
data/ngx_2021_2025.csv so the app never depends on the extractor folder at runtime.

Run once (or whenever the master is regenerated):
    python scripts/prepare_data.py
"""
from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd

# --- paths -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUT = DATA_DIR / "ngx_2021_2025.csv"

# Master source (extractor output). Overridable via CLI arg 1.
DEFAULT_SOURCE = Path(r"C:\Users\machiavelique\Desktop\NGX_EXTRACTOR\ngx_master_final.csv")
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE

YEAR_MIN, YEAR_MAX = 2021, 2025

# Columns that are 100% empty across the dataset — carry no information.
DEAD_COLS = ["page_method", "needs_review", "missing", "repair_notes", "ocr_dependent"]

# --- sourced corrections ---------------------------------------------------
# Three NGX-listed groups report in US dollars, not Naira (Ecobank/ETI, Seplat
# Energy and Airtel Africa — the international dual-listed groups). The extractor
# stored their USD figures under an NGN label, so their absolute values looked
# ~1000x too small. Convert every monetary column to NGN at World Bank official
# annual-average USD/NGN rates.
#
# Ratios (ROE/ROA/margins) are unit-independent and already correct, so they are
# left untouched; scaling all money columns by one rate per year also keeps
# A = L + E intact. Figures are therefore approximate (these are multi-country
# groups whose own consolidation rates differ slightly).
#
# Verified against published Naira figures:
#   Ecobank FY2024: $0.49bn x1478 ~= N724bn vs reported N735.9bn (-1.6%)
#   Seplat  FY2024: $1.116bn x1478 ~= N1.65trn vs reported N1.652trn (exact)
# Sources: nairametrics.com (ETI FY2024), arise.tv (Seplat FY2024),
#          technext24.com (Airtel FY2025), World Bank PA.NUS.FCRF (rates).
USD_NGN = {2021: 401.0, 2022: 426.0, 2023: 645.0, 2024: 1478.0, 2025: 1535.0}
USD_COMPANIES = ["ECO BANK", "SEPLAT ENERGY", "AIRTEL AFRICA"]

# Money columns converted by the FX rate. Per-share amounts are deliberately
# excluded: their units are inconsistent in the source (dollars for some issuers,
# US cents for others), so we recompute them from converted profit instead.
_MONEY_COLS = [
    "gross_earnings", "net_interest_income", "cost_of_sales", "operating_expenses",
    "depreciation_amortization", "finance_cost", "impairment_loan_loss", "profit_before_tax",
    "profit_after_tax", "total_assets", "current_assets", "total_liabilities", "current_liabilities",
    "interest_bearing_debt", "total_equity", "retained_earnings", "cash_and_equivalents",
    "net_cash_from_operations", "net_cash_from_investing", "net_cash_from_financing", "capex",
    "gross_profit", "operating_profit", "income_tax_expense", "customer_deposits", "net_loans_advances",
    "net_premium_income", "net_claims_incurred", "aum", "nav_total", "nci_profit_after_tax",
    "nci_total_equity", "working_capital", "free_cash_flow", "ebitda",
]


def _apply_corrections(df: pd.DataFrame) -> pd.DataFrame:
    fixed = 0
    for company in USD_COMPANIES:
        rows = df["company"] == company
        if not rows.any():
            continue

        # 1) money columns -> NGN at that year's average rate
        for yr, rate in USD_NGN.items():
            m = rows & (df["year"] == yr)
            for col in _MONEY_COLS:
                if col in df.columns:
                    df.loc[m, col] = pd.to_numeric(df.loc[m, col], errors="coerce") * rate

        # 2) per-share figures recomputed in NGN from the converted profit, which
        #    sidesteps the dollars-vs-cents ambiguity in the source data.
        #    EPS = profit attributable to owners / shares; DPS = payout x EPS
        #    (payout_ratio is a ratio, so it survives the currency change).
        pat = pd.to_numeric(df.loc[rows, "profit_after_tax"], errors="coerce")
        nci = pd.to_numeric(df.loc[rows, "nci_profit_after_tax"], errors="coerce").fillna(0)
        shares = pd.to_numeric(df.loc[rows, "shares_outstanding"], errors="coerce")
        payout = pd.to_numeric(df.loc[rows, "payout_ratio"], errors="coerce")
        eps = (pat - nci) / shares
        df.loc[rows, "eps_basic"] = eps
        df.loc[rows, "dividend_per_share"] = payout * eps

        fixed += int(rows.sum())
        print(f"[FIX] {company}: {int(rows.sum())} rows converted USD->NGN")
    if fixed:
        print(f"[FIX] total {fixed} rows corrected across {len(USD_COMPANIES)} USD reporters")
    return df


def main() -> int:
    if not SOURCE.exists():
        print(f"[ERROR] source not found: {SOURCE}")
        return 1

    df = pd.read_csv(SOURCE)
    n0 = len(df)

    # Clean year -> int and slice to the comparable window.
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df = df[(df["year"] >= YEAR_MIN) & (df["year"] <= YEAR_MAX)].copy()

    # Drop empty scaffolding columns if present.
    df = df.drop(columns=[c for c in DEAD_COLS if c in df.columns])

    # Apply sourced/web-verified corrections.
    df = _apply_corrections(df)

    # Stable ordering: company, then year.
    df = df.sort_values(["company", "year"]).reset_index(drop=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print(f"[OK] {SOURCE.name}: {n0} rows -> {len(df)} rows ({YEAR_MIN}-{YEAR_MAX})")
    print(f"[OK] companies: {df['company'].nunique()} | sectors: {df['sector'].nunique()}")
    print(f"[OK] columns kept: {df.shape[1]} (dropped {len(DEAD_COLS)} empty)")
    print(f"[OK] wrote: {OUT}")
    # Sanity: any company without the full 5 years?
    counts = df.groupby("company")["year"].nunique()
    partial = counts[counts < 5]
    if len(partial):
        print("[NOTE] partial-history companies:")
        for name, c in partial.items():
            print(f"        {name}: {c} year(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
