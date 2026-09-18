"""
run_capacity_optimization_sweep.py
=====================================
Phase 44-45: evaluates thousands of capacity plans (random sampling
across the specified ranges) against the REAL 2019 hourly shape, then
reports the lowest-cost plan among those with zero unserved energy.

Ranges swept (Phase 45's own spec, interpreted concretely):
  - Renewables: wind capacity 0-3x today's 695 MW, solar 0-3x today's
    1210 MW (independently) -- "0-100%" read as a 0x-3x capacity
    multiplier sweep, since Phase 44 lists CAPACITY as the decision
    variable, not a penetration percentage directly.
  - Storage: 0-2,000 MWh (a documented, round upper bound - "X" was
    not specified further).
  - Demand: -10% to +50% of real 2019 demand.
  - Imports: 0-1,000 MW (0-100% of today's real Finland interconnection
    capacity).
  - Thermal (oil shale): held FIXED at today's real 1,568 MW for this
    sweep (Phase 45's own listed ranges don't include it) - noted, not hidden.
"""

from pathlib import Path
import time
import numpy as np
import pandas as pd

from A_engine.optimization.capacity_expansion import CapacityPlan, evaluate_plan, precompute_shapes

ROOT = Path(__file__).parent
N_COMBINATIONS = 3000
RANDOM_SEED = 42
THERMAL_CAPACITY_MW = 1568.0


def main():
    baseline = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])
    weather = pd.read_csv(ROOT / "B_data" / "processed" / "weather_national_average_2015_2025.csv", parse_dates=["time"])
    weather_2019 = weather[weather["time"].dt.year == 2019]

    shapes = precompute_shapes(baseline, weather_2019)

    rng = np.random.default_rng(RANDOM_SEED)
    plans = [
        CapacityPlan(
            wind_capacity_mw=rng.uniform(0, 3 * 695),
            solar_capacity_mw=rng.uniform(0, 3 * 1210),
            storage_capacity_mwh=rng.uniform(0, 2000),
            thermal_capacity_mw=THERMAL_CAPACITY_MW,
            import_capacity_mw=rng.uniform(0, 1000),
            demand_multiplier=rng.uniform(0.90, 1.50),
        )
        for _ in range(N_COMBINATIONS)
    ]

    print(f"Evaluating {N_COMBINATIONS} capacity plans against real 2019 hourly shape...")
    t0 = time.time()
    results = [evaluate_plan(plan, shapes) for plan in plans]
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s ({1000*elapsed/N_COMBINATIONS:.1f} ms/plan)\n")

    df = pd.DataFrame([{
        "wind_mw": r.plan.wind_capacity_mw, "solar_mw": r.plan.solar_capacity_mw,
        "storage_mwh": r.plan.storage_capacity_mwh, "import_mw": r.plan.import_capacity_mw,
        "demand_mult": r.plan.demand_multiplier,
        "unserved_mwh": r.unserved_energy_mwh, "curtailment_mwh": r.curtailment_mwh,
        "renewable_share_pct": r.renewable_share_pct,
        "operational_cost_eur": r.operational_cost_eur, "capex_eur": r.annualized_capex_eur,
        "total_cost_eur": r.total_cost_eur,
    } for r in results])

    feasible = df[df["unserved_mwh"] == 0]
    print(f"Plans with ZERO unserved energy: {len(feasible)} / {N_COMBINATIONS}")

    if len(feasible) > 0:
        best = feasible.loc[feasible["total_cost_eur"].idxmin()]
        print("\n=== Lowest TOTAL-cost (operational + annualized capex) fully-reliable plan ===")
        print(f"  Wind capacity:    {best['wind_mw']:.0f} MW (today: 695 MW)")
        print(f"  Solar capacity:   {best['solar_mw']:.0f} MW (today: 1210 MW)")
        print(f"  Storage:          {best['storage_mwh']:.0f} MWh (today: 0 MWh)")
        print(f"  Import capacity:  {best['import_mw']:.0f} MW (today: 1000 MW)")
        print(f"  Demand level:     {100*(best['demand_mult']-1):.1f}% vs real 2019")
        print(f"  -> Renewable share: {best['renewable_share_pct']:.1f}%, curtailment: {best['curtailment_mwh']:.0f} MWh")
        print(f"  -> Operational cost: {best['operational_cost_eur']:,.0f} EUR/yr")
        print(f"  -> Annualized capex: {best['capex_eur']:,.0f} EUR/yr")
        print(f"  -> TOTAL cost:       {best['total_cost_eur']:,.0f} EUR/yr")
    else:
        print("No fully-reliable plan found in this sample — widen the search or increase N_COMBINATIONS.")

    print(f"\n=== Total cost distribution across all {N_COMBINATIONS} plans (feasible + infeasible) ===")
    print(df["total_cost_eur"].describe().to_string())

    out_path = ROOT / "B_data" / "processed" / "capacity_sweep_results.csv"
    df.to_csv(out_path, index=False)
    print(f"\nFull results written to {out_path}")

    print(
        "\nCaveats: costs use the same illustrative EUR/MWh assumptions as "
        "Phase 43 (not real Estonian prices). Storage is dispatched by a "
        "simple greedy heuristic, not a cost-optimal operational schedule. "
        "Solar output uses REAL 2019 irradiance through a GENERIC (uncalibrated) "
        "PV model — see capacity_expansion.py docstring."
    )


if __name__ == "__main__":
    main()
