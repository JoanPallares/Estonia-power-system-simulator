"""
Tests for Phase 44-45: capacity_expansion.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.optimization.capacity_expansion import CapacityPlan, evaluate_plan, precompute_shapes


def make_fake_shapes(n_hours=48):
    return {
        "wind_shape": np.array([0.5] * n_hours),
        "solar_shape": np.array([0.2] * n_hours),
        "demand_mw": np.array([100.0] * n_hours),
    }


def test_zero_capacity_plan_all_unserved():
    shapes = make_fake_shapes()
    plan = CapacityPlan(wind_capacity_mw=0, solar_capacity_mw=0, storage_capacity_mwh=0,
                         thermal_capacity_mw=0, import_capacity_mw=0)
    result = evaluate_plan(plan, shapes)
    assert result.unserved_energy_mwh == pytest.approx(100.0 * 48)


def test_sufficient_thermal_alone_meets_demand():
    shapes = make_fake_shapes()
    plan = CapacityPlan(wind_capacity_mw=0, solar_capacity_mw=0, storage_capacity_mwh=0,
                         thermal_capacity_mw=200, import_capacity_mw=0)
    result = evaluate_plan(plan, shapes)
    assert result.unserved_energy_mwh == 0.0


def test_excess_renewable_causes_curtailment_without_storage():
    shapes = make_fake_shapes()
    # wind alone (0.5 * 300 = 150 MW) exceeds demand (100 MW) every hour
    plan = CapacityPlan(wind_capacity_mw=300, solar_capacity_mw=0, storage_capacity_mwh=0,
                         thermal_capacity_mw=0, import_capacity_mw=0)
    result = evaluate_plan(plan, shapes)
    assert result.curtailment_mwh > 0
    assert result.unserved_energy_mwh == 0.0


def test_storage_reduces_curtailment_vs_no_storage():
    shapes = make_fake_shapes()
    plan_no_storage = CapacityPlan(wind_capacity_mw=300, solar_capacity_mw=0, storage_capacity_mwh=0,
                                    thermal_capacity_mw=0, import_capacity_mw=0)
    plan_with_storage = CapacityPlan(wind_capacity_mw=300, solar_capacity_mw=0, storage_capacity_mwh=500,
                                      thermal_capacity_mw=0, import_capacity_mw=0)
    result_no_storage = evaluate_plan(plan_no_storage, shapes)
    result_with_storage = evaluate_plan(plan_with_storage, shapes, storage_power_mw=100)
    assert result_with_storage.curtailment_mwh < result_no_storage.curtailment_mwh


def test_renewable_share_capped_at_100_when_fully_covered():
    shapes = make_fake_shapes()
    plan = CapacityPlan(wind_capacity_mw=1000, solar_capacity_mw=0, storage_capacity_mwh=0,
                         thermal_capacity_mw=0, import_capacity_mw=0)
    result = evaluate_plan(plan, shapes)
    assert result.renewable_share_pct <= 100.5  # allow tiny float slack, but not wildly over


def test_precompute_shapes_produces_correct_length():
    baseline = pd.DataFrame({
        "timestamp_utc": pd.date_range("2019-01-01", periods=24, freq="h", tz="UTC"),
        "wind_generation_mw": [50.0] * 24,
        "demand_mw": [900.0] * 24,
    })
    weather = pd.DataFrame({
        "time": pd.date_range("2019-01-01", periods=24, freq="h"),
        "shortwave_radiation_wm2": [200.0] * 24,
    })
    shapes = precompute_shapes(baseline, weather)
    assert len(shapes["wind_shape"]) == 24
    assert len(shapes["solar_shape"]) == 24
