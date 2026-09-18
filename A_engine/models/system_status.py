"""
system_status.py
=================
Level 2 building block: system status classification
(MASTER PROMPT, Sections 11 and 14).

Classifies each period into a status based on the RESERVE MARGIN:

    Reserve Margin = (Available Capacity - Demand) / Demand

This module is completely country-agnostic and does NOT hard-code any
capacities or thresholds — those are injected as parameters, typically
sourced from a country's config file.

IMPORTANT — what "Available Capacity" must be:
This is capacity (MW, converted to comparable energy for the period),
i.e. what COULD have been supplied, not what WAS supplied (that's
domestic_generation + imports from balance.py). Without real capacity
data, this function cannot produce a scientifically meaningful result.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class SystemStatus(str, Enum):
    STABLE = "stable"       # reserve margin >= stressed_threshold
    STRESSED = "stressed"   # reserve margin >= blackout_threshold but < stressed_threshold
    BLACKOUT = "blackout"   # reserve margin < blackout_threshold (demand cannot be met)


@dataclass
class ReserveThresholds:
    """
    Configurable thresholds (MASTER PROMPT Section 15: 'never invent
    probability values and present them as real'). These are ASSUMPTIONS
    unless a country's regulator publishes official reserve requirements
    — always check C_configs/<country>.yaml for where a given value came
    from before trusting it.
    """
    stressed_below_pct: float = 15.0   # reserve margin below this %  -> STRESSED
    blackout_below_pct: float = 0.0    # reserve margin below this %  -> BLACKOUT (deficit)


class SystemState5(str, Enum):
    """
    Phase 28: the 5-state classification from MASTER PROMPT Section 11,
    made quantitative. Extends (does not replace) SystemStatus above —
    existing 3-state code (run_level2_status.py) keeps working.
    """
    NORMAL = "normal"       # enough generation AND reserve
    STRESSED = "stressed"   # generation sufficient, reserve margin low
    CRITICAL = "critical"   # reserve below the official/regulatory minimum
    DEFICIT = "deficit"     # some demand not served, but not (yet) at blackout scale
    BLACKOUT = "blackout"   # unserved energy exceeds the blackout threshold


@dataclass
class FiveStateThresholds:
    """
    Phase 27: 'what counts as available capacity' is answered by WHERE
    this struct's numbers come from, not by this struct itself — see
    each field's default/usage site for provenance. stressed_below_pct
    is this project's own choice (a buffer above the regulatory floor);
    critical_below_pct should be set to a real regulatory figure where
    one exists (e.g. Estonia: Elering's official 10% Grid Code rule —
    see C_configs/estonia.yaml).
    """
    stressed_below_pct: float = 20.0
    critical_below_pct: float = 10.0
    blackout_unserved_energy_threshold_pct_of_demand: float = 1.0  # ASSUMPTION: >1% of demand unserved = blackout-scale, not just deficit


def classify_system_state_5(
    reserve_margin_pct: float,
    unserved_energy_mw: float,
    demand_mw: float,
    thresholds: FiveStateThresholds = FiveStateThresholds(),
) -> SystemState5:
    if demand_mw <= 0:
        raise ValueError("demand_mw must be positive")

    unserved_pct = 100 * unserved_energy_mw / demand_mw

    if unserved_pct > thresholds.blackout_unserved_energy_threshold_pct_of_demand:
        return SystemState5.BLACKOUT
    if unserved_energy_mw > 0:
        return SystemState5.DEFICIT
    if reserve_margin_pct < thresholds.critical_below_pct:
        return SystemState5.CRITICAL
    if reserve_margin_pct < thresholds.stressed_below_pct:
        return SystemState5.STRESSED
    return SystemState5.NORMAL


def classify_system_status(
    demand_mwh: pd.Series,
    available_capacity_mwh: pd.Series,
    thresholds: ReserveThresholds = ReserveThresholds(),
) -> pd.DataFrame:
    """
    Computes reserve margin and classifies each period.

    Returns a DataFrame with columns: reserve_margin_pct, status.
    """
    if len(demand_mwh) != len(available_capacity_mwh):
        raise ValueError("demand_mwh and available_capacity_mwh must be the same length")

    reserve_margin_pct = 100 * (available_capacity_mwh - demand_mwh) / demand_mwh

    def _classify(margin: float) -> str:
        if margin < thresholds.blackout_below_pct:
            return SystemStatus.BLACKOUT.value
        elif margin < thresholds.stressed_below_pct:
            return SystemStatus.STRESSED.value
        else:
            return SystemStatus.STABLE.value

    status = reserve_margin_pct.apply(_classify)

    return pd.DataFrame({
        "reserve_margin_pct": reserve_margin_pct,
        "status": status,
    })
