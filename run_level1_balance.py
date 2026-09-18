"""
run_level1_balance.py
======================
Level 1: national electricity balance. Uses the country_registry
(A_engine/io/country_registry.py) — currently Estonia only (Andorra
was removed; see country_registry.py's docstring for how to point this
at a different country in the future).

Usage:
    python run_level1_balance.py
"""

import pandas as pd

from A_engine.io.country_registry import load_country
from A_engine.models.balance import compute_balance, balance_summary
from D_analysis.validation import check_balance_consistency


def main():
    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", 20)

    config, ts = load_country()

    print(f"=== Country: {config.name} | Resolution: {config.resolution} ===\n")
    print(f"Loaded {len(ts)} period(s) from: {ts.source}")
    print(f"Notes: {ts.notes}\n")

    balance_df = compute_balance(ts)
    print("--- Balance ---")
    print(balance_df[[
        "date", "demand_mwh", "domestic_generation_mwh", "imports_mwh",
        "exports_mwh", "system_balance_mwh", "self_sufficiency_ratio",
        "import_dependency_ratio",
    ]].to_string(index=False))
    print()

    checked = check_balance_consistency(balance_df, tolerance_pct=1.0)
    n_flagged = checked["consistency_flag"].sum()
    print(f"--- Consistency check (tolerance = 1.0% of demand) ---")
    print(f"Periods flagged as inconsistent: {n_flagged} / {len(checked)}")
    if n_flagged:
        print(checked.loc[checked["consistency_flag"], ["date", "residual_pct_of_demand"]].to_string(index=False))
    print()

    summary = balance_summary(balance_df)
    print("--- Summary KPIs ---")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
