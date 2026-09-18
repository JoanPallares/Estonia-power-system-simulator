"""
run_generation_fleet.py
========================
Level 2 building block: per-technology generation analysis, using
REAL quarterly production data for Estonia (Q3 2025) — no synthetic
placeholders needed here.

Computes EMPIRICAL capacity factors (measured production / theoretical
max at nameplate capacity) — these are DERIVED from real data, not
assumed industry-typical values.
"""

import pandas as pd
from pathlib import Path

from A_engine.io.data_loader import load_estonia_generation_by_technology
from A_engine.models.generation import TechnologyGeneration, summarize_fleet

ROOT = Path(__file__).parent
Q3_2025_HOURS = 92 * 24  # Jul-Sep 2025: 31+31+30 = 92 days


def main():
    pd.set_option("display.width", 120)

    df = load_estonia_generation_by_technology(
        ROOT / "B_data" / "raw" / "elering" / "generation_by_technology_quarterly.csv"
    )
    q3 = df[df["quarter"] == "2025-Q3"]

    fleet = [
        TechnologyGeneration(
            technology=row["technology"],
            capacity_mw=row["installed_capacity_mw"] if pd.notna(row["installed_capacity_mw"]) else None,
            generation_mwh=row["generation_mwh"],
            period_hours=Q3_2025_HOURS,
            renewable=bool(row["renewable"]),
        )
        for _, row in q3.iterrows()
    ]

    print("=== Estonia — Q3 2025 generation fleet (REAL data, Elering) ===\n")
    for t in fleet:
        cf = t.capacity_factor
        cf_str = f"{cf*100:.1f}%" if cf is not None else "N/A (capacity not published)"
        print(f"  {t.technology:<25} generation: {t.generation_mwh:>10,.0f} MWh   "
              f"capacity: {t.capacity_mw or 'unknown':>6} MW   capacity factor: {cf_str}")

    summary = summarize_fleet(fleet)
    print(f"\nTotal generation (these 3 technologies): {summary['total_generation_mwh']:,.0f} MWh")
    print(f"Renewable share (within these 3 technologies): {summary['renewable_share_pct']}%")
    print(
        "\nNote: this covers wind + solar + biomass/biogas/waste only — Elering's "
        "press release did not include oil shale generation for the same quarter, "
        "so this is NOT the full national generation mix, just the renewable slice "
        "that was reported. See data_catalogue.csv."
    )


if __name__ == "__main__":
    main()
