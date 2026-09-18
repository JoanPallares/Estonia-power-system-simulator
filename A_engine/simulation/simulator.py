"""
simulator.py
============
Phase 24: the dynamic simulation loop.

HONESTY NOTE — what this actually does right now:
This does NOT yet do real dispatch (choosing which plant runs) or real
storage optimization — we don't have per-plant data or a real dispatch
rule to calibrate against. What it DOES do, for real: replays REAL 2019
hourly data (demand, generation, imports/exports via Finland/Latvia)
through the SystemState/reserve-margin/5-state-classification machinery,
timestep by timestep, exactly as Section 11's numbered list describes —
with storage OPTIONALLY added as a scenario (Phase 26), since Estonia
has none for real. This is the honest current scope: a REAL historical
replay engine with an OPTIONAL hypothetical storage layer, not yet a
predictive dispatch simulator.
"""

from __future__ import annotations
import pandas as pd

from ..models.state import SystemState
from ..models.storage import Battery, BatteryConfig
from ..models.system_status import classify_system_state_5, FiveStateThresholds


def run_hourly_replay(
    hourly_df: pd.DataFrame,
    available_capacity_mw: float,
    thresholds: FiveStateThresholds = FiveStateThresholds(),
    battery_config: BatteryConfig | None = None,
    battery_dispatch_rule=None,
) -> list[SystemState]:
    """
    Section 11's numbered steps, applied per row of REAL hourly data:
      1. demand              <- hourly_df['demand_mw']
      2. renewable avail.    <- hourly_df['wind_generation_mw'] if present, else None (honest)
      3. available generation <- `available_capacity_mw` (constant — see note below)
      4. controllable gen.   <- domestic_generation - renewable (if renewable known)
      5. storage operation   <- OPTIONAL, only if battery_config given (Phase 26, scenario)
      6. imports / exports   <- hourly_df['imports_mw'] / ['exports_mw']
      7. reserve             <- available_capacity - demand
      8. curtailment         <- NOT modelled yet (needs a real dispatch rule to know what was curtailable)
      9. unserved demand     <- max(0, demand - available_capacity - battery_discharge); a CAPABILITY check, not derived from the historical generation/import accounting (see bugfix note in the loop below)
      10. system state       <- classify_system_state_5()

    `available_capacity_mw` is passed as a CONSTANT for now — real
    time-varying available capacity (accounting for maintenance,
    outages, wind/solar resource) is a further step, not yet built;
    using the constant total installed capacity is itself a documented
    simplification (see C_configs/estonia.yaml).

    battery_dispatch_rule(state_so_far: SystemState) -> requested_power_mw
    lets the caller define a simple rule (e.g. "charge when reserve is
    high, discharge when low") without hard-coding one here — Section 3
    of the master prompt: don't build features nobody asked for.
    """
    battery = Battery(battery_config) if battery_config else None
    states: list[SystemState] = []

    for _, row in hourly_df.iterrows():
        demand_mw = float(row["demand_mw"])
        generation_mw = float(row["domestic_generation_mw"])
        imports_mw = float(row["imports_mw"])
        exports_mw = float(row["exports_mw"])
        renewable_mw = float(row["wind_generation_mw"]) if "wind_generation_mw" in row and pd.notna(row.get("wind_generation_mw")) else None

        reserve_mw = available_capacity_mw - demand_mw
        reserve_margin_pct = 100 * reserve_mw / demand_mw

        storage_charge_mw = 0.0
        storage_soc_mwh = None
        battery_discharge_mw = 0.0
        if battery is not None:
            requested = battery_dispatch_rule(reserve_margin_pct) if battery_dispatch_rule else 0.0
            storage_charge_mw = battery.step(requested, duration_hours=1.0)
            storage_soc_mwh = battery.state.soc_mwh
            battery_discharge_mw = max(0.0, -storage_charge_mw)

            # BUGFIX (caught by tests/test_critical_invariants.py): storage
            # charge/discharge must be absorbed somewhere for energy to
            # balance — it cannot be a free side-channel disconnected from
            # imports/exports. Modelled here as adjusting the NET cross-
            # border flow: charging is treated as extra import need (or
            # reduced export), discharging as reduced import need (or
            # extra export). This is a modelling CHOICE (imports/exports
            # are the marginal, flexible term in Estonia's real system),
            # not a measured fact — documented here, not hidden.
            net_import_mw = imports_mw - exports_mw + storage_charge_mw
            imports_mw = max(net_import_mw, 0.0)
            exports_mw = max(-net_import_mw, 0.0)

        # unserved_energy is a CAPABILITY check (can available_capacity + any
        # battery discharge cover demand?), NOT a check against the historical
        # generation+imports-exports accounting — that accounting already
        # closes to ~0.003% of demand (see docs), and using it here would
        # misclassify essentially random rounding noise as "deficit" on
        # ~40% of all hours. That was a real bug caught by inspecting this
        # very output — left documented here rather than silently fixed.
        unserved_mw = max(0.0, demand_mw - available_capacity_mw - battery_discharge_mw)

        state5 = classify_system_state_5(reserve_margin_pct, unserved_mw, demand_mw, thresholds)

        states.append(SystemState(
            timestamp=row["timestamp_utc"] if "timestamp_utc" in row else row.get("date"),
            demand_mw=demand_mw,
            domestic_generation_mw=generation_mw,
            renewable_generation_mw=renewable_mw,
            available_capacity_mw=available_capacity_mw,
            imports_mw=imports_mw,
            exports_mw=exports_mw,
            reserve_mw=reserve_mw,
            reserve_margin_pct=reserve_margin_pct,
            storage_soc_mwh=storage_soc_mwh,
            storage_charge_mw=storage_charge_mw,
            curtailment_mw=0.0,  # not modelled yet — see docstring
            unserved_energy_mw=unserved_mw,
            component_status={"5_state": state5.value},
        ))

    return states
