"""
run_scenario_sweep.py
=======================
Phase 32: runs all 15 scenarios (C_configs/scenarios/estonia.yaml)
against the REAL 2019 hourly baseline.

Available capacity formula, made explicit (Phase 27's own requirement):
    available_capacity_mw = wind_capacity_nameplate      (695 MW, unaffected by wind_multiplier —
                                                            capacity != output; a de-rated capacity
                                                            credit for wind would be more realistic
                                                            but isn't modelled here)
                           + solar_capacity_nameplate     (1210 MW, same caveat)
                           + other_dispatchable_capacity  (1568 MW) x oil_shale_availability
                           + interconnection_capacity     (1000 MW, Finland only — Latvia's total
                                                            capacity isn't confirmed, see data_catalogue.csv)
                             x import_capacity_multiplier

This is a documented SIMPLIFICATION, not a claim that wind/solar
contribute their full nameplate to firm reserve — a proper capacity
credit model is future work.
"""

from pathlib import Path
import pandas as pd

from A_engine.simulation.scenarios import load_scenarios, apply_scenario
from A_engine.models.curtailment import curtailment_summary
from A_engine.models.system_status import classify_system_state_5, FiveStateThresholds

ROOT = Path(__file__).parent

WIND_CAPACITY_MW = 695
SOLAR_CAPACITY_MW = 1210
OTHER_DISPATCHABLE_CAPACITY_MW = 1568
FINLAND_IMPORT_CAPACITY_MW = 1000

THRESHOLDS = FiveStateThresholds(stressed_below_pct=20.0, critical_below_pct=10.0)


def main():
    baseline = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])
    scenarios = load_scenarios(ROOT / "C_configs" / "scenarios" / "estonia.yaml")

    results = []
    for scenario in scenarios:
        scenario_df = apply_scenario(baseline, scenario)

        available_capacity_mw = (
            WIND_CAPACITY_MW + SOLAR_CAPACITY_MW
            + OTHER_DISPATCHABLE_CAPACITY_MW * scenario.oil_shale_availability
            + FINLAND_IMPORT_CAPACITY_MW * scenario.import_capacity_multiplier
        )

        reserve_margin_pct = 100 * (available_capacity_mw - scenario_df["demand_mw"]) / scenario_df["demand_mw"]
        min_reserve = reserve_margin_pct.min()

        states = reserve_margin_pct.apply(lambda m: classify_system_state_5(m, 0.0, 1.0, THRESHOLDS).value)
        state_counts = states.value_counts().to_dict()

        curt = curtailment_summary(scenario_df["wind_generation_mw"], scenario_df["wind_generation_mw"].clip(upper=scenario_df["demand_mw"]))

        results.append({
            "scenario": scenario.name,
            "avg_demand_mw": round(scenario_df["demand_mw"].mean(), 1),
            "available_capacity_mw": round(available_capacity_mw, 1) if not hasattr(available_capacity_mw, "mean") else round(available_capacity_mw.mean(), 1),
            "min_reserve_margin_pct": round(min_reserve, 1),
            "curtailment_pct_of_wind": curt["curtailment_pct_of_available"],
            "hours_normal": state_counts.get("normal", 0),
            "hours_stressed": state_counts.get("stressed", 0),
            "hours_critical": state_counts.get("critical", 0),
        })

    df = pd.DataFrame(results)
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)
    print(df.to_string(index=False))
    print()
    print(
        "S9 (Latvia outage) shows no effect — documented limitation: this "
        "project's imports_mw is NETTED across all 3 real flow columns "
        "(Finland/Russia/Latvia combined), so isolating Latvia alone isn't "
        "possible with the generic scenario engine. See "
        "run_failure_deterministic.py for a version that DOES isolate "
        "individual interconnections using the raw per-country flow columns."
    )


if __name__ == "__main__":
    main()
