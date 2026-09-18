"""
run_scenario.py
=================
Phase 54: canonical entry point — "python run_scenario.py --scenario
extreme_winter" -> runs ONE named scenario (not all 15 at once, unlike
run_scenario_sweep.py, which stays as the detailed multi-scenario tool).

Friendly aliases map to the real scenario IDs in
C_configs/scenarios/estonia.yaml (S0-S15) — "extreme_winter" isn't one
of the original 15 names verbatim, so it's mapped here explicitly
rather than guessed.
"""

import argparse
from pathlib import Path
import pandas as pd

from A_engine.simulation.scenarios import load_scenarios, apply_scenario

ROOT = Path(__file__).parent

FRIENDLY_ALIASES = {
    "current": "S0_current_system",
    "high_demand": "S1_high_demand",
    "low_demand": "S2_low_demand",
    "high_wind": "S3_high_wind",
    "low_wind": "S4_low_wind",
    "low_solar": "S5_low_solar",
    "low_hydro": "S6_low_hydro",
    "oil_shale_outage": "S7_oil_shale_outage",
    "finland_outage": "S8_finland_interconnection_outage",
    "latvia_outage": "S9_latvia_interconnection_outage",
    "imports_minus_50": "S10_import_capacity_minus_50pct",
    "imports_zero": "S11_import_capacity_zero",
    "high_renewables": "S12_high_renewable_penetration",
    "high_renewables_storage": "S13_high_renewables_plus_storage",
    "extreme_winter": "S14_cold_winter_low_wind",
    "extreme_winter_interconnection_failure": "S15_cold_winter_low_wind_interconnection_failure",
}


def resolve_scenario_name(name: str) -> str:
    if name in FRIENDLY_ALIASES:
        return FRIENDLY_ALIASES[name]
    if name.upper().startswith("S") and any(name == s for s in FRIENDLY_ALIASES.values()):
        return name
    raise ValueError(
        f"Unknown scenario '{name}'. Available friendly names: {list(FRIENDLY_ALIASES.keys())} "
        f"or exact IDs: {list(FRIENDLY_ALIASES.values())}"
    )


def main():
    parser = argparse.ArgumentParser(description="Run one named scenario against real 2019 Estonia data")
    parser.add_argument("--scenario", required=True, help="e.g. extreme_winter, high_wind, finland_outage")
    args = parser.parse_args()

    scenario_id = resolve_scenario_name(args.scenario)
    scenarios = {s.name: s for s in load_scenarios(ROOT / "C_configs" / "scenarios" / "estonia.yaml")}
    if scenario_id not in scenarios:
        raise KeyError(f"'{scenario_id}' not found in scenarios/estonia.yaml — available: {list(scenarios.keys())}")
    scenario = scenarios[scenario_id]

    baseline = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])
    result_df = apply_scenario(baseline, scenario)

    print(f"=== Scenario: {scenario.name} ===")
    print(f"Description: {scenario.description}\n")
    print(f"Demand: {result_df['demand_mw'].sum()/1000:,.0f} GWh/yr "
          f"(baseline: {baseline['demand_mw'].sum()/1000:,.0f} GWh/yr)")
    print(f"Wind generation: {result_df['wind_generation_mw'].sum()/1000:,.0f} GWh/yr "
          f"(baseline: {baseline['wind_generation_mw'].sum()/1000:,.0f} GWh/yr)")
    print(f"Total domestic generation: {result_df['generation_mw'].sum()/1000:,.0f} GWh/yr")
    print(f"Import capacity multiplier applied: {scenario.import_capacity_multiplier}")

    print(
        "\nFor a full reliability read (LOLP/LOLE/EENS) under this scenario, "
        "combine this scenario's demand/wind multipliers with "
        "run_monte_carlo.py's MonteCarloConfig manually, or see "
        "run_scenario_sweep.py for all 15 scenarios evaluated together "
        "with reserve-margin and 5-state classification."
    )


if __name__ == "__main__":
    main()
