"""
run_level2_dynamic_simulation.py
==================================
Phases 23-24-26-27-28 combined: runs the real 8760-hour 2019 dataset
through the timestep simulation loop, once WITHOUT storage (baseline)
and once WITH a hypothetical battery (Phase 26 scenario), and reports
the 5-state distribution for each.
"""

from pathlib import Path
import pandas as pd

from A_engine.io.data_loader import load_estonia_hourly_2019
from A_engine.models.system_status import FiveStateThresholds
from A_engine.models.storage import BatteryConfig
from A_engine.simulation.simulator import run_hourly_replay
from A_engine.models.state import states_to_dataframe

ROOT = Path(__file__).parent

# "Available capacity" definition for this run (Phase 27, made explicit):
# Estonia's total installed net capacity, start of 2025, per Elering
# (C_configs/estonia.yaml). This OVERSTATES true real-time available
# capacity (ignores outages/maintenance/wind-solar resource limits) —
# a documented simplification, not a hidden one.
AVAILABLE_CAPACITY_MW = 3473

# Thresholds: stressed buffer is this project's own choice; critical
# threshold (10%) IS Elering's real official Grid Code minimum.
THRESHOLDS = FiveStateThresholds(stressed_below_pct=20.0, critical_below_pct=10.0)


def main():
    raw = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])
    raw = raw.rename(columns={"generation_mw": "domestic_generation_mw"})

    print("=== Baseline: no storage (real 2019 data, 8760 hours) ===")
    states_baseline = run_hourly_replay(raw, AVAILABLE_CAPACITY_MW, THRESHOLDS)
    df_baseline = states_to_dataframe(states_baseline)
    print(df_baseline["status__5_state"].value_counts())
    print(f"Min reserve margin observed: {df_baseline['reserve_margin_pct'].min():.1f}%")
    print(f"Max unserved energy observed: {df_baseline['unserved_energy_mw'].max():.2f} MW")
    print()

    print("=== Scenario: + hypothetical 500 MWh / 200 MW battery (Phase 26) ===")
    print("(SCENARIO ONLY — Estonia has no real utility-scale storage of this kind today)")
    battery_config = BatteryConfig(energy_capacity_mwh=500, power_capacity_mw=200)

    def simple_rule(reserve_margin_pct: float) -> float:
        # Naive, transparent rule: charge when reserve is ample, discharge when tight.
        # Not an optimization — just enough to demonstrate the mechanism (Section 3:
        # avoid complexity/optimization "because it sounds impressive").
        if reserve_margin_pct > 40:
            return 200.0   # charge at full power
        elif reserve_margin_pct < 15:
            return -200.0  # discharge at full power
        return 0.0

    states_with_storage = run_hourly_replay(
        raw, AVAILABLE_CAPACITY_MW, THRESHOLDS,
        battery_config=battery_config, battery_dispatch_rule=simple_rule,
    )
    df_storage = states_to_dataframe(states_with_storage)
    print(df_storage["status__5_state"].value_counts())
    print(f"Min reserve margin observed: {df_storage['reserve_margin_pct'].min():.1f}%")
    print(f"Max unserved energy observed: {df_storage['unserved_energy_mw'].max():.2f} MW")
    print(f"Final battery SOC: {df_storage['storage_soc_mwh'].iloc[-1]:.1f} MWh (of {battery_config.energy_capacity_mwh} MWh capacity)")

    print()
    print(
        "Interpretation: with Estonia's installed capacity ~2x its all-time peak "
        "demand, the system stays NORMAL essentially the whole year in this "
        "simplified replay (constant available capacity, no outages modelled) — "
        "the battery scenario changes very little here BECAUSE the system was "
        "never actually stressed in this dataset to begin with. A more revealing "
        "test needs either (a) real outage/maintenance data reducing available "
        "capacity, or (b) the renewable-penetration stress scenarios (Phase 29)."
    )


if __name__ == "__main__":
    main()
