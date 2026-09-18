"""
capacity_expansion.py
=======================
Phase 44: evaluates a CAPACITY PLAN (wind/solar/storage/thermal/import
capacities) against the real 2019 hourly shape, using a fast heuristic
(not a full per-hour LP — running economic_dispatch.py's LP for
thousands of plans x 8760 hours each would be computationally
impractical; Section 3 also cautions against complexity for its own
sake). This is a CAPACITY ADEQUACY screening tool, not an operational
dispatch optimizer — it answers "does this capacity mix keep the
lights on and how much does it cost/curtail", not "what does the
system operator do each hour".

Renewable output shapes:
  - Wind: REAL 2019 hourly shape, normalized to per-MW-of-capacity
    (i.e. real capacity factor time series), then scaled to any
    candidate wind_capacity_mw.
  - Solar: generic_pv_model() applied to REAL 2019 national-average
    irradiance (ERA5) — REAL weather input, GENERIC/uncalibrated PV
    coefficient (see renewable_physical.py). Not the same confidence
    level as wind's real generation-based shape.

Storage: simulated hour-by-hour (SOC-consistent, reuses the Battery
class from storage.py) with a simple greedy rule: charge from any
curtailed renewable surplus first, discharge to cover unserved demand
first — not a cost-optimal dispatch, a physically-consistent heuristic.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

from ..models.storage import Battery, BatteryConfig
from ..models.renewable_physical import generic_pv_model

ASSUMED_OIL_SHALE_COST_EUR_MWH = 40.0
ASSUMED_IMPORT_PRICE_EUR_MWH = 60.0

# *** ANNUALIZED CAPITAL COST ASSUMPTIONS — GENERIC INDUSTRY BENCHMARKS ***
# NOT Estonia-specific procurement costs. Without these, a cost-minimizing
# sweep would always prefer building infinite free-fuel renewable capacity
# (a real bug caught in this project's own first sweep run — see
# run_capacity_optimization_sweep.py's documented finding). Overnight
# capital cost annualized via a simple capital recovery factor:
#   CRF = r(1+r)^n / ((1+r)^n - 1), r=discount rate, n=lifetime years
_DISCOUNT_RATE = 0.05
_WIND_OVERNIGHT_EUR_PER_MW = 1_300_000
_WIND_LIFETIME_YEARS = 25
_SOLAR_OVERNIGHT_EUR_PER_MW = 700_000
_SOLAR_LIFETIME_YEARS = 25
_STORAGE_OVERNIGHT_EUR_PER_MWH = 300_000
_STORAGE_LIFETIME_YEARS = 15


def _capital_recovery_factor(lifetime_years: int, rate: float = _DISCOUNT_RATE) -> float:
    return rate * (1 + rate) ** lifetime_years / ((1 + rate) ** lifetime_years - 1)


ANNUALIZED_WIND_EUR_PER_MW_YEAR = _WIND_OVERNIGHT_EUR_PER_MW * _capital_recovery_factor(_WIND_LIFETIME_YEARS)
ANNUALIZED_SOLAR_EUR_PER_MW_YEAR = _SOLAR_OVERNIGHT_EUR_PER_MW * _capital_recovery_factor(_SOLAR_LIFETIME_YEARS)
ANNUALIZED_STORAGE_EUR_PER_MWH_YEAR = _STORAGE_OVERNIGHT_EUR_PER_MWH * _capital_recovery_factor(_STORAGE_LIFETIME_YEARS)


@dataclass
class CapacityPlan:
    wind_capacity_mw: float
    solar_capacity_mw: float
    storage_capacity_mwh: float
    thermal_capacity_mw: float
    import_capacity_mw: float
    demand_multiplier: float = 1.0


@dataclass
class CapacityPlanResult:
    plan: CapacityPlan
    unserved_energy_mwh: float
    curtailment_mwh: float
    renewable_share_pct: float
    operational_cost_eur: float
    annualized_capex_eur: float
    total_cost_eur: float
    hours_with_unserved_energy: int


def precompute_shapes(baseline_df: pd.DataFrame, national_weather_df: pd.DataFrame) -> dict:
    """Computes the two per-MW-of-capacity output shapes ONCE, reused
    across every plan in a sweep (avoids recomputing 8760-hour series
    thousands of times)."""
    real_wind_capacity_mw = 695.0  # Elering, start 2025 — see C_configs/estonia.yaml
    wind_shape = (baseline_df["wind_generation_mw"] / real_wind_capacity_mw).clip(lower=0, upper=1).values

    irradiance = national_weather_df.set_index("time").reindex(
        pd.to_datetime(baseline_df["timestamp_utc"]).dt.tz_localize(None)
    )["shortwave_radiation_wm2"].fillna(0).values
    solar_shape = np.array([generic_pv_model(irr, capacity_mw=1.0) for irr in irradiance])

    return {
        "wind_shape": wind_shape,       # fraction of wind_capacity_mw, per hour
        "solar_shape": solar_shape,     # MW per MW of solar_capacity_mw, per hour
        "demand_mw": baseline_df["demand_mw"].values,
    }


def evaluate_plan(plan: CapacityPlan, shapes: dict, storage_power_mw: float | None = None) -> CapacityPlanResult:
    n_hours = len(shapes["demand_mw"])
    demand = shapes["demand_mw"] * plan.demand_multiplier
    wind_out = shapes["wind_shape"] * plan.wind_capacity_mw
    solar_out = shapes["solar_shape"] * plan.solar_capacity_mw
    renewable_out = wind_out + solar_out

    if storage_power_mw is None:
        storage_power_mw = plan.storage_capacity_mwh / 4.0  # ASSUMPTION: 4-hour-duration battery, a common real-world default ratio

    battery = Battery(BatteryConfig(energy_capacity_mwh=max(plan.storage_capacity_mwh, 1e-6),
                                     power_capacity_mw=max(storage_power_mw, 1e-6)),
                       initial_soc_fraction=0.5) if plan.storage_capacity_mwh > 0 else None

    unserved = np.zeros(n_hours)
    curtailed = np.zeros(n_hours)
    thermal_used = np.zeros(n_hours)
    import_used = np.zeros(n_hours)

    for t in range(n_hours):
        net_needed = demand[t] - renewable_out[t]

        if net_needed <= 0:
            surplus = -net_needed
            if battery is not None:
                absorbed = battery.step(min(surplus, storage_power_mw), duration_hours=1.0)
                surplus -= max(absorbed, 0)
            curtailed[t] = max(surplus, 0)
            continue

        thermal = min(net_needed, plan.thermal_capacity_mw)
        net_needed -= thermal
        thermal_used[t] = thermal

        if net_needed > 0 and battery is not None:
            discharged = -battery.step(-min(net_needed, storage_power_mw), duration_hours=1.0)
            net_needed -= max(discharged, 0)

        imports = min(max(net_needed, 0), plan.import_capacity_mw)
        net_needed -= imports
        import_used[t] = imports

        unserved[t] = max(net_needed, 0)

    total_demand_mwh = demand.sum()
    renewable_share = 100 * (renewable_out.sum() - curtailed.sum()) / total_demand_mwh if total_demand_mwh else 0
    operational_cost = thermal_used.sum() * ASSUMED_OIL_SHALE_COST_EUR_MWH + import_used.sum() * ASSUMED_IMPORT_PRICE_EUR_MWH

    # Only capacity ADDED beyond what already exists today is capitalized —
    # today's real 695 MW wind / 1210 MW solar / 0 MWh storage are treated
    # as sunk (already built), so this optimizes INCREMENTAL investment,
    # not a from-scratch system cost.
    incremental_wind_mw = max(plan.wind_capacity_mw - 695.0, 0)
    incremental_solar_mw = max(plan.solar_capacity_mw - 1210.0, 0)
    annualized_capex = (
        incremental_wind_mw * ANNUALIZED_WIND_EUR_PER_MW_YEAR
        + incremental_solar_mw * ANNUALIZED_SOLAR_EUR_PER_MW_YEAR
        + plan.storage_capacity_mwh * ANNUALIZED_STORAGE_EUR_PER_MWH_YEAR
    )
    total_cost = operational_cost + annualized_capex

    return CapacityPlanResult(
        plan=plan,
        unserved_energy_mwh=round(float(unserved.sum()), 1),
        curtailment_mwh=round(float(curtailed.sum()), 1),
        renewable_share_pct=round(float(renewable_share), 2),
        operational_cost_eur=round(float(operational_cost), 0),
        annualized_capex_eur=round(float(annualized_capex), 0),
        total_cost_eur=round(float(total_cost), 0),
        hours_with_unserved_energy=int((unserved > 0).sum()),
    )
