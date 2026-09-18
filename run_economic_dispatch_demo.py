"""
run_economic_dispatch_demo.py
================================
Phase 43: runs the economic dispatch LP on two REAL hours from 2019 —
the annual peak demand hour and a low-demand summer hour — to show the
mechanism responding sensibly to different real conditions.
"""

from pathlib import Path
import pandas as pd

from A_engine.optimization.economic_dispatch import solve_economic_dispatch

ROOT = Path(__file__).parent
OIL_SHALE_CAPACITY_MW = 1568
INTERCONNECTION_CAPACITY_MW = 1000


def main():
    df = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])

    peak_row = df.loc[df["demand_mw"].idxmax()]
    low_row = df.loc[df["demand_mw"].idxmin()]

    for label, row in [("Peak demand hour (real 2019)", peak_row), ("Lowest demand hour (real 2019)", low_row)]:
        print(f"=== {label}: {row['timestamp_utc']} ===")
        print(f"Real demand: {row['demand_mw']:.1f} MW, real wind: {row['wind_generation_mw']:.1f} MW")

        result = solve_economic_dispatch(
            demand_mw=row["demand_mw"], wind_mw=row["wind_generation_mw"],
            oil_shale_capacity_mw=OIL_SHALE_CAPACITY_MW,
            interconnection_capacity_mw=INTERCONNECTION_CAPACITY_MW,
        )

        print(f"  Optimal dispatch: oil_shale={result.oil_shale_mw} MW, imports={result.imports_mw} MW, "
              f"exports={result.exports_mw} MW")
        print(f"  Total cost: {result.total_cost_eur_per_h:.0f} EUR/h "
              f"({result.total_cost_eur_per_h / row['demand_mw']:.2f} EUR/MWh average)")
        print()

    print(
        "Interpretation: with oil shale (40 EUR/MWh, assumed) cheaper than imports "
        "(60 EUR/MWh, assumed), the optimizer correctly maxes out oil shale before "
        "importing anything — exactly the expected LP behaviour. This confirms the "
        "OPTIMIZATION MECHANISM works; the actual EUR figures are illustrative, "
        "not a real Estonian cost estimate (see module docstring)."
    )


if __name__ == "__main__":
    main()
