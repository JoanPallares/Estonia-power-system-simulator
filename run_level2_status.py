"""
run_level2_status.py
=====================
Level 2 demo: system status classification (Stable / Stressed / Blackout).

Available capacity here is REAL (installed capacity + interconnection
limits, both published by Elering), and the reserve threshold is
Elering's own official Grid Code requirement (10%), not an assumption.
See run_failure_scenario.py for a real historical stress test using
this same data.

(This script previously also supported Andorra with a SYNTHETIC
capacity placeholder, since Andorra publishes no installed-capacity
data. Andorra has been removed from this project - see
A_engine/io/country_registry.py's docstring.)
"""

from pathlib import Path
import pandas as pd

from A_engine.io.config_loader import load_country_config
from A_engine.models.system_status import classify_system_status, ReserveThresholds

ROOT = Path(__file__).parent


def main():
    config = load_country_config(ROOT / "C_configs" / "estonia.yaml")

    print("=" * 78)
    print("Available capacity below is REAL (Elering-published installed capacity")
    print("+ interconnection limits). Threshold (10%) is Elering's official rule,")
    print("not an assumption. See run_failure_scenario.py for a real stress test.")
    print("=" * 78 + "\n")

    demand = pd.Series([config.peak_demand_mw], name="demand_mw")
    available_capacity = pd.Series([config.installed_capacity_total_mw], name="available_capacity_mw")
    thresholds = ReserveThresholds(
        stressed_below_pct=config.reserve_thresholds.stressed_below_pct,
        blackout_below_pct=config.reserve_thresholds.blackout_below_pct,
    )
    status_df = classify_system_status(demand, available_capacity, thresholds)
    result = pd.concat([demand, available_capacity, status_df], axis=1)
    print(result.to_string(index=False))
    print(f"\n(This is Estonia's all-time peak demand, {config.peak_demand_mw} MW on 5 Feb 2026, "
          f"vs total domestic installed capacity alone, not counting imports.)")


if __name__ == "__main__":
    main()
