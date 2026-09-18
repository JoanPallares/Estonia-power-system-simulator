"""
run_level1_balance_report.py
==============================
Phase 15: the formatted balance report, using the REAL hourly 2019
dataset (the only year we have hourly data for — see docs/period_analysis.md).

HONESTY NOTE, read before trusting the "generation mix" section:
The requested report template has "Renewable generation" / "Non-renewable
generation" as line items. This hourly file (2019_arhiiv_0.xls) only
disaggregates WIND from total generation — solar, hydro, biomass, oil
shale, gas etc. are NOT separately reported here. Reporting a
"renewable vs non-renewable" split from this file would mean inventing
numbers we don't have. So this report shows "Wind generation" vs
"Other generation (technology mix not disaggregated in this dataset)"
instead — a deliberate, labelled deviation from the literal template,
not an oversight. True renewable/non-renewable requires merging with
Statistics Estonia KE21 or a fuller Elering technology export, which
has not been ingested yet (see docs/data_discovery_estonia.md).

2024 note: Elering's own published figure (8.26 TWh demand, 2024,
annual-only) is used here ONLY as an external sanity check in the
header — this report's actual balance and validation numbers are for
2019, the year we have real hourly data for.
"""

from pathlib import Path
import pandas as pd

from A_engine.io.data_loader import load_estonia_hourly_2019
from A_engine.models.balance import compute_balance, balance_summary
from D_analysis.validation import multi_resolution_comparison

ROOT = Path(__file__).parent
ELERING_2024_ANNUAL_DEMAND_TWH = 8.26  # external sanity check figure, not this report's data


def main():
    ts = load_estonia_hourly_2019(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv")
    balance_df = compute_balance(ts)
    summary = balance_summary(balance_df)

    total_demand_twh = summary["total_demand_mwh"] / 1_000_000
    total_generation_twh = summary["total_domestic_generation_mwh"] / 1_000_000
    total_imports_twh = summary["total_imports_mwh"] / 1_000_000
    total_exports_twh = summary["total_exports_mwh"] / 1_000_000
    residual_gwh = summary["balance_residual_mwh"] / 1_000

    processed = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv")
    wind_twh = processed["wind_generation_mw"].sum() / 1_000_000
    other_generation_twh = total_generation_twh - wind_twh

    # Level 1 "model": reconstruct demand from generation + imports - exports (losses=0, Phase 11)
    model_df = balance_df.copy()
    model_df["model_demand_mwh"] = (
        model_df["domestic_generation_mwh"] + model_df["imports_mwh"] - model_df["exports_mwh"]
    )
    val = multi_resolution_comparison(
        model_df, date_col="date", real_col="demand_mwh", simulated_col="model_demand_mwh"
    )

    print("=" * 55)
    print("ESTONIA ELECTRICITY BALANCE")
    print("YEAR: 2019 (real hourly data, 8760/8760 hours)")
    print("=" * 55)
    print()
    print(f"External sanity check — Elering's published 2024 annual demand: {ELERING_2024_ANNUAL_DEMAND_TWH} TWh")
    print(f"This report's year (2019) demand: {total_demand_twh:.2f} TWh — same order of magnitude, as expected")
    print()
    print("Demand")
    print(f"{total_demand_twh:.2f} TWh")
    print()
    print("Domestic generation")
    print(f"{total_generation_twh:.2f} TWh")
    print()
    print("Imports")
    print(f"{total_imports_twh:.2f} TWh")
    print()
    print("Exports")
    print(f"{total_exports_twh:.2f} TWh")
    print()
    print("Wind generation (only technology disaggregated in this file)")
    print(f"{wind_twh:.2f} TWh")
    print()
    print("Other generation (oil shale/gas/solar/hydro/biomass/waste — NOT disaggregated here)")
    print(f"{other_generation_twh:.2f} TWh")
    print()
    print("Residual (Generation + Imports - Exports - Demand, losses assumed 0 — Phase 11)")
    print(f"{residual_gwh:.2f} GWh  ({summary['balance_residual_pct_of_demand']}% of demand)")
    print()
    print("Validation  (model = Generation + Imports - Exports, vs real measured Demand)")
    print("-" * 55)
    for resolution in ["native", "daily", "monthly", "annual"]:
        m = val[resolution]
        label = "hourly" if resolution == "native" else resolution
        print(f"  [{label}] (n={m['n_periods']})")
        print(f"    MAE:  {m['mae']:.2f} MWh")
        print(f"    RMSE: {m['rmse']:.2f} MWh")
        print(f"    MAPE: {m['mape_pct']:.3f}%")
        print(f"    Peak error:   {m['peak_error_pct']:.3f}%")
        print(f"    Annual/period energy error: {m['annual_energy_error_pct']:.4f}%")
    print("=" * 55)
    print()
    print(
        "Interpretation: errors are tiny by construction — the 'model' here is "
        "reconstructed FROM the same real measured components (generation, "
        "imports, exports), so this is a CONSISTENCY check, not a predictive "
        "validation. Real predictive validation (e.g. forecasting demand "
        "without using same-period generation/import data) is a Level 2+ task."
    )


if __name__ == "__main__":
    main()
