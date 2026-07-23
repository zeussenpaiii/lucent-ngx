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
