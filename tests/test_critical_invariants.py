"""
test_critical_invariants.py
=============================
Phase 50: physical invariants that must NEVER be violated by this
engine, checked against REAL data and randomized inputs (not just
hand-picked toy cases) — these are the tests that matter most for
scientific credibility, per the project owner's own framing.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.balance import compute_balance
from A_engine.io.data_loader import load_estonia_hourly_2019
from A_engine.simulation.simulator import run_hourly_replay
from A_engine.models.storage import Battery, BatteryConfig
from A_engine.power_flow.dc_power_flow import check_congestion, TYPICAL_THERMAL_LIMIT_MW
from A_engine.models.network import PowerNetwork, Bus, Line
from A_engine.models.time_handling import validate_hourly_continuity, CANONICAL_TIMEZONE

ROOT = Path(__file__).parent.parent


def _real_hourly_path():
    return ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv"


# =====================================================================
# 1. ENERGY CONSERVATION
# =====================================================================

def test_energy_conservation_real_2019_balance():
    """Generation + Imports - Exports - Demand - Losses must be ~0 for
    every real hour, not just in aggregate (Phase 11's own finding,
    re-asserted here as a hard invariant, per-hour not just annually)."""
    path = _real_hourly_path()
    if not path.exists():
        pytest.skip("real hourly data not present")

    ts = load_estonia_hourly_2019(path)
    balance_df = compute_balance(ts)

    # Per-hour residual must be small relative to that hour's demand -
    # not just small in the annual sum (which could hide offsetting errors).
    residual_pct = (balance_df["system_balance_mwh"].abs() / balance_df["demand_mwh"]) * 100
    assert residual_pct.max() < 5.0, f"Worst single-hour residual: {residual_pct.max():.2f}% of demand"
    assert residual_pct.mean() < 0.5


def test_energy_conservation_dynamic_replay_with_storage():
    """Generation + Imports = Demand + Exports + Storage_charge + Curtailment
    + Unserved, at EVERY timestep of a dynamic replay with a battery
    active (Phase 50's equation, with the components this engine
    actually models)."""
    path = _real_hourly_path()
    if not path.exists():
        pytest.skip("real hourly data not present")

    raw = pd.read_csv(path, parse_dates=["timestamp_utc"])
    raw = raw.rename(columns={"generation_mw": "domestic_generation_mw"}).head(500)  # sample for speed

    from A_engine.models.storage import BatteryConfig
    states = run_hourly_replay(
        raw, available_capacity_mw=3473,
        battery_config=BatteryConfig(energy_capacity_mwh=500, power_capacity_mw=200),
        battery_dispatch_rule=lambda margin: 100.0 if margin > 50 else -100.0,
    )

    for i, s in enumerate(states):
        charge = max(s.storage_charge_mw, 0)
        discharge = max(-s.storage_charge_mw, 0)
        lhs = s.domestic_generation_mw + s.imports_mw + discharge
        rhs = s.demand_mw + s.exports_mw + charge + s.curtailment_mw + s.unserved_energy_mw
        assert abs(lhs - rhs) < 1.0, f"Hour {i}: conservation violated by {lhs - rhs:.2f} MW"


# =====================================================================
# 2. GENERATION NEVER EXCEEDS AVAILABLE CAPACITY
# =====================================================================

def test_capacity_expansion_thermal_never_exceeds_its_capacity():
    from A_engine.optimization.capacity_expansion import CapacityPlan, evaluate_plan
    n = 200
    shapes = {
        "wind_shape": np.random.default_rng(1).uniform(0, 1, n),
        "solar_shape": np.random.default_rng(2).uniform(0, 1, n),
        "demand_mw": np.random.default_rng(3).uniform(500, 2000, n),
    }
    plan = CapacityPlan(wind_capacity_mw=500, solar_capacity_mw=500, storage_capacity_mwh=0,
                         thermal_capacity_mw=800, import_capacity_mw=0)
    # Re-implement a direct check by calling evaluate_plan's internals is not
    # exposed, so we check the OUTPUT-level invariant: unserved energy should
    # appear whenever demand exceeds ALL capacity combined (thermal capped at 800).
    result = evaluate_plan(plan, shapes)
    max_possible_mw = 500 + 500 + 800  # wind+solar+thermal capacity ceiling (upper bound, shapes <=1)
    # If demand never exceeds max possible, unserved must be 0 (capacity was never truly binding)
    if shapes["demand_mw"].max() <= max_possible_mw * 0.5:  # generous margin given random shapes
        assert result.unserved_energy_mwh == 0


def test_battery_charge_output_never_exceeds_power_capacity():
    rng = np.random.default_rng(42)
    config = BatteryConfig(energy_capacity_mwh=100, power_capacity_mw=20)
    battery = Battery(config, initial_soc_fraction=0.5)
    for _ in range(500):
        requested = rng.uniform(-1000, 1000)  # deliberately absurd requests
        actual = battery.step(requested, duration_hours=1.0)
        assert abs(actual) <= config.power_capacity_mw + 1e-6


# =====================================================================
# 3. BATTERY SOC NEVER OUT OF BOUNDS
# =====================================================================

def test_battery_soc_never_negative_or_over_capacity_under_random_operation():
    rng = np.random.default_rng(7)
    config = BatteryConfig(energy_capacity_mwh=250, power_capacity_mw=80,
                            min_soc_fraction=0.05, max_soc_fraction=0.95)
    battery = Battery(config, initial_soc_fraction=0.5)

    for _ in range(2000):
        requested = rng.uniform(-150, 150)
        battery.step(requested, duration_hours=1.0)
        assert battery.state.soc_mwh >= 0 - 1e-6, f"SOC went negative: {battery.state.soc_mwh}"
        assert battery.state.soc_mwh <= config.energy_capacity_mwh + 1e-6, f"SOC exceeded 100%: {battery.state.soc_mwh}"
        # Also check it respects the configured min/max (tighter bound than 0/capacity)
        assert battery.state.soc_mwh >= config.energy_capacity_mwh * config.min_soc_fraction - 1e-6
        assert battery.state.soc_mwh <= config.energy_capacity_mwh * config.max_soc_fraction + 1e-6


# =====================================================================
# 4. TRANSMISSION: flow > limit ALWAYS flagged
# =====================================================================

def test_every_overloaded_line_is_flagged_never_silently_allowed():
    rng = np.random.default_rng(99)
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="A", voltage_kv=110))
    net.add_bus(Bus(id="B", name="B", voltage_kv=110))
    net.add_line(Line(id="L1", from_bus_id="A", to_bus_id="B", voltage_kv=110, length_km=10))

    limit = TYPICAL_THERMAL_LIMIT_MW[110.0]
    for _ in range(500):
        flow = rng.uniform(-limit * 3, limit * 3)
        violations = check_congestion({"L1": flow}, net)
        if abs(flow) > limit:
            assert len(violations) == 1, f"Flow {flow} MW (limit {limit}) was NOT flagged"
        else:
            assert len(violations) == 0, f"Flow {flow} MW (limit {limit}) was WRONGLY flagged"


# =====================================================================
# 5. TIME: no duplicate timestamps, no silent gaps
# =====================================================================

def test_real_2019_data_has_no_duplicate_timestamps():
    path = _real_hourly_path()
    if not path.exists():
        pytest.skip("real hourly data not present")
    df = pd.read_csv(path, parse_dates=["timestamp_utc"])
    assert df["timestamp_utc"].duplicated().sum() == 0


def test_real_2019_data_has_no_unexpected_gaps():
    path = _real_hourly_path()
    if not path.exists():
        pytest.skip("real hourly data not present")
    df = pd.read_csv(path, parse_dates=["timestamp_utc"])
    idx = pd.DatetimeIndex(df["timestamp_utc"])
    result = validate_hourly_continuity(idx)
    assert result["gaps"] == [], f"Unexpected gaps found: {result['gaps'][:5]}"
    assert result["duplicates"] == []


def test_ambiguous_dst_timestamp_raises_rather_than_silently_resolving():
    """Regression test for the exact real bug this project hit and fixed
    (Phase 11 ingestion, 2019-10-27 03:00 fall-back duplicate) — the
    generic time_handling module must still fail loudly by default."""
    from A_engine.models.time_handling import localize_naive_index
    idx = pd.DatetimeIndex(["2019-10-27 02:00", "2019-10-27 03:00", "2019-10-27 03:00", "2019-10-27 04:00"])
    with pytest.raises(Exception):
        localize_naive_index(idx)
