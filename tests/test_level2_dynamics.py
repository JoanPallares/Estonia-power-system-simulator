"""
Tests for Phase 16 (TechnologyProfile), 23 (SystemState), 25
(interconnection), 26 (storage), 27-28 (5-state classification).
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.generation import TechnologyProfile, ESTONIA_OIL_SHALE_PROFILE
from A_engine.models.state import SystemState, states_to_dataframe
from A_engine.models.storage import Battery, BatteryConfig
from A_engine.models.interconnection import (
    InterconnectionConfig, InterconnectionFlow, check_capacity_violation,
)
from A_engine.models.system_status import (
    SystemState5, FiveStateThresholds, classify_system_state_5,
)


# --- Phase 16 ---

def test_oil_shale_profile_leaves_unsourced_fields_none():
    assert ESTONIA_OIL_SHALE_PROFILE.marginal_cost_eur_per_mwh is None
    assert ESTONIA_OIL_SHALE_PROFILE.emissions_factor_tco2_per_mwh is None
    assert ESTONIA_OIL_SHALE_PROFILE.capacity_mw == 1568


def test_technology_profile_is_a_plain_dataclass():
    p = TechnologyProfile(
        technology="test", capacity_mw=10, availability=0.9, min_output_mw=0,
        max_output_mw=10, ramp_rate_mw_per_min=1, marginal_cost_eur_per_mwh=50,
        emissions_factor_tco2_per_mwh=0.5, renewable=False, variable=False, dispatchable=True,
    )
    assert p.capacity_mw == 10


# --- Phase 23 ---

def test_system_state_to_dict_flattens_component_status():
    s = SystemState(
        timestamp=pd.Timestamp("2019-01-01", tz="UTC"), demand_mw=100, domestic_generation_mw=80,
        renewable_generation_mw=10, available_capacity_mw=200, imports_mw=20, exports_mw=0,
        reserve_mw=100, reserve_margin_pct=100.0, storage_soc_mwh=None,
        component_status={"battery": "offline"},
    )
    d = s.to_dict()
    assert d["status__battery"] == "offline"


def test_states_to_dataframe():
    states = [
        SystemState(pd.Timestamp("2019-01-01", tz="UTC"), 100, 80, 10, 200, 20, 0, 100, 100.0, None),
        SystemState(pd.Timestamp("2019-01-01 01:00", tz="UTC"), 110, 85, 12, 200, 25, 0, 90, 81.8, None),
    ]
    df = states_to_dataframe(states)
    assert len(df) == 2
    assert "demand_mw" in df.columns


# --- Phase 26: Battery ---

def test_battery_charge_respects_power_limit():
    b = Battery(BatteryConfig(energy_capacity_mwh=100, power_capacity_mw=10), initial_soc_fraction=0.5)
    actual = b.step(requested_power_mw=50, duration_hours=1.0)  # way over the 10 MW limit
    assert actual <= 10.0


def test_battery_charge_respects_max_soc():
    config = BatteryConfig(energy_capacity_mwh=100, power_capacity_mw=1000, max_soc_fraction=0.9, charge_efficiency=1.0)
    b = Battery(config, initial_soc_fraction=0.89)
    b.step(requested_power_mw=1000, duration_hours=1.0)
    assert b.state.soc_mwh <= 90.0 + 1e-6


def test_battery_discharge_respects_min_soc():
    config = BatteryConfig(energy_capacity_mwh=100, power_capacity_mw=1000, min_soc_fraction=0.1, discharge_efficiency=1.0)
    b = Battery(config, initial_soc_fraction=0.11)
    b.step(requested_power_mw=-1000, duration_hours=1.0)
    assert b.state.soc_mwh >= 10.0 - 1e-6


def test_battery_round_trip_efficiency_loses_energy():
    config = BatteryConfig(energy_capacity_mwh=100, power_capacity_mw=50, charge_efficiency=0.9, discharge_efficiency=0.9)
    b = Battery(config, initial_soc_fraction=0.5)
    soc_before = b.state.soc_mwh
    b.step(requested_power_mw=10, duration_hours=1.0)   # charge
    b.step(requested_power_mw=-10, duration_hours=1.0)  # discharge same requested power
    # Round trip efficiency < 1 means we get back less energy than we could
    # have delivered before charging (SOC should have drifted down slightly
    # relative to a lossless round trip of equal charge/discharge requests)
    assert b.state.soc_mwh < soc_before + 1e-6


# --- Phase 25: Interconnection ---

def test_interconnection_flow_sign_convention():
    flow = InterconnectionFlow("Finland", flow_mw=-300)  # importing
    assert flow.import_mw() == 300
    assert flow.export_mw() == 0


def test_check_capacity_violation_detects_overload():
    config = InterconnectionConfig("Finland", import_capacity_mw=1000, export_capacity_mw=1000)
    flow = InterconnectionFlow("Finland", flow_mw=-1200)
    violation = check_capacity_violation(flow, config)
    assert violation is not None
    assert "Finland" in violation


def test_check_capacity_violation_none_within_limits():
    config = InterconnectionConfig("Finland", import_capacity_mw=1000, export_capacity_mw=1000)
    flow = InterconnectionFlow("Finland", flow_mw=-500)
    assert check_capacity_violation(flow, config) is None


def test_check_capacity_violation_unavailable_interconnection():
    config = InterconnectionConfig("Finland", import_capacity_mw=1000, export_capacity_mw=1000, available=False)
    flow = InterconnectionFlow("Finland", flow_mw=-50)
    violation = check_capacity_violation(flow, config)
    assert violation is not None


# --- Phase 27-28: 5-state classification ---

def test_five_state_normal():
    assert classify_system_state_5(reserve_margin_pct=50, unserved_energy_mw=0, demand_mw=1000) == SystemState5.NORMAL


def test_five_state_stressed():
    assert classify_system_state_5(reserve_margin_pct=15, unserved_energy_mw=0, demand_mw=1000) == SystemState5.STRESSED


def test_five_state_critical():
    assert classify_system_state_5(reserve_margin_pct=5, unserved_energy_mw=0, demand_mw=1000) == SystemState5.CRITICAL


def test_five_state_deficit():
    result = classify_system_state_5(reserve_margin_pct=-2, unserved_energy_mw=3, demand_mw=1000)
    assert result == SystemState5.DEFICIT


def test_five_state_blackout():
    result = classify_system_state_5(reserve_margin_pct=-20, unserved_energy_mw=50, demand_mw=1000)
    assert result == SystemState5.BLACKOUT


def test_five_state_custom_thresholds():
    strict = FiveStateThresholds(stressed_below_pct=80, critical_below_pct=50)
    assert classify_system_state_5(60, 0, 1000, strict) == SystemState5.STRESSED
    assert classify_system_state_5(40, 0, 1000, strict) == SystemState5.CRITICAL
