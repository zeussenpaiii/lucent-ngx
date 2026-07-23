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
# Ecobank (ETI) reports in US dollars; the extractor stored USD figures under an
# NGN label, so its absolute values looked ~1000x too small. Convert every
# monetary column to NGN at World Bank official annual-average USD/NGN rates.
# Ratios (ROE/ROA/margins) are unit-independent and already correct, so we leave
# them; converting all money columns by one rate/year keeps A=L+E and ratios
# consistent. Figures are therefore approximate (ETI is a pan-African group).
# Verified: 2024 PAT $0.49bn x1478 ~= N724bn vs reported N735.9bn.
# Sources: nairametrics.com (ETI FY2024), World Bank PA.NUS.FCRF (rates).
ETI_USD_NGN = {2021: 401.0, 2022: 426.0, 2023: 645.0, 2024: 1478.0, 2025: 1535.0}
_MONEY_COLS = [
    "gross_earnings", "net_interest_income", "cost_of_sales", "operating_expenses",
    "depreciation_amortization", "finance_cost", "impairment_loan_loss", "profit_before_tax",
    "profit_after_tax", "total_assets", "current_assets", "total_liabilities", "current_liabilities",
    "interest_bearing_debt", "total_equity", "retained_earnings", "cash_and_equivalents",
    "net_cash_from_operations", "net_cash_from_investing", "net_cash_from_financing", "capex",
    "gross_profit", "operating_profit", "income_tax_expense", "customer_deposits", "net_loans_advances",
    "net_premium_income", "net_claims_incurred", "aum", "nav_total", "nci_profit_after_tax",
    "nci_total_equity", "working_capital", "free_cash_flow", "ebitda",
    "eps_basic", "dividend_per_share", "nav_per_unit",  # per-share amounts are also USD
]


def _apply_corrections(df: pd.DataFrame) -> pd.DataFrame:
    eti = df["company"] == "ECO BANK"
    for yr, rate in ETI_USD_NGN.items():
        m = eti & (df["year"] == yr)
        for col in _MONEY_COLS:
            if col in df.columns:
                df.loc[m, col] = pd.to_numeric(df.loc[m, col], errors="coerce") * rate
    n = int(eti.sum())
    if n:
        print(f"[FIX] Ecobank (ETI): converted {n} rows USD->NGN at annual-average rates")
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
