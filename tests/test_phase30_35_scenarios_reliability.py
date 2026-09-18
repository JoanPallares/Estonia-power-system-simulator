"""
Tests for Phase 30 (curtailment), 31-32 (scenario engine), 33
(deterministic failures - interconnection module reuse), 34-35 (Monte
Carlo + reliability metrics).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.curtailment import compute_curtailment, curtailment_summary
from A_engine.simulation.scenarios import ScenarioConfig, apply_scenario, load_scenarios
from A_engine.simulation.monte_carlo import run_monte_carlo, MonteCarloConfig
from A_engine.reliability.reliability import compute_reliability_metrics


# --- Phase 30 ---

def test_curtailment_zero_when_all_used():
    available = pd.Series([100.0, 100.0])
    used = pd.Series([100.0, 100.0])
    assert compute_curtailment(available, used).tolist() == [0.0, 0.0]


def test_curtailment_positive_when_available_exceeds_used():
    available = pd.Series([100.0])
    used = pd.Series([60.0])
    assert compute_curtailment(available, used).iloc[0] == 40.0


def test_curtailment_never_negative():
    available = pd.Series([50.0])
    used = pd.Series([80.0])  # shouldn't happen physically, but data can be messy
    assert compute_curtailment(available, used).iloc[0] == 0.0


def test_curtailment_summary_structure():
    available = pd.Series([100.0, 100.0, 50.0])
    used = pd.Series([100.0, 50.0, 50.0])
    summary = curtailment_summary(available, used)
    assert summary["hours_with_curtailment"] == 1
    assert summary["total_curtailment_mwh"] == 50.0


# --- Phase 31: scenario engine ---

def test_apply_scenario_demand_multiplier():
    df = pd.DataFrame({
        "demand_mw": [100.0, 200.0],
        "wind_generation_mw": [10.0, 20.0],
        "generation_mw": [50.0, 60.0],
        "imports_mw": [40.0, 30.0],
        "exports_mw": [0.0, 0.0],
    })
    scenario = ScenarioConfig(name="test", demand_multiplier=1.5)
    result = apply_scenario(df, scenario)
    assert result["demand_mw"].tolist() == [150.0, 300.0]


def test_apply_scenario_does_not_mutate_baseline():
    df = pd.DataFrame({
        "demand_mw": [100.0], "wind_generation_mw": [10.0],
        "generation_mw": [50.0], "imports_mw": [40.0], "exports_mw": [0.0],
    })
    original = df.copy()
    apply_scenario(df, ScenarioConfig(name="test", demand_multiplier=2.0))
    pd.testing.assert_frame_equal(df, original)


def test_apply_scenario_wind_multiplier_and_generation_consistency():
    df = pd.DataFrame({
        "demand_mw": [100.0], "wind_generation_mw": [10.0],
        "generation_mw": [50.0], "imports_mw": [40.0], "exports_mw": [0.0],
    })
    scenario = ScenarioConfig(name="test", wind_multiplier=2.0)
    result = apply_scenario(df, scenario)
    assert result["wind_generation_mw"].iloc[0] == 20.0
    # non-wind portion (40) + new wind (20) = 60
    assert result["generation_mw"].iloc[0] == 60.0


def test_load_scenarios_reads_real_config():
    root = Path(__file__).parent.parent
    path = root / "C_configs" / "scenarios" / "estonia.yaml"
    if not path.exists():
        pytest.skip("scenarios/estonia.yaml not present")
    scenarios = load_scenarios(path)
    assert len(scenarios) == 16  # S0 through S15
    names = [s.name for s in scenarios]
    assert "S0_current_system" in names
    assert "S15_cold_winter_low_wind_interconnection_failure" in names


# --- Phase 34-35: Monte Carlo + reliability ---

def test_monte_carlo_reproducible_with_same_seed():
    demand = np.array([1000.0] * 100)
    wind = np.array([50.0] * 100)
    cfg = MonteCarloConfig(n_iterations=10, random_seed=123)
    r1 = run_monte_carlo(demand, wind, 800, 100, 100, 200, cfg)
    r2 = run_monte_carlo(demand, wind, 800, 100, 100, 200, cfg)
    np.testing.assert_array_equal(r1["demand_mw"], r2["demand_mw"])


def test_monte_carlo_detects_deficit_when_capacity_starved():
    demand = np.array([1000.0] * 200)
    wind = np.array([0.0] * 200)
    cfg = MonteCarloConfig(n_iterations=200, dispatchable_forced_outage_prob=0.9, dispatchable_outage_severity_fraction=1.0)
    result = run_monte_carlo(demand, wind, domestic_dispatchable_capacity_mw=900,
                              wind_capacity_mw=0, solar_capacity_mw=0,
                              interconnection_capacity_mw=0, config=cfg)
    assert result["deficit_hour"].sum() > 0  # with capacity often knocked out entirely, deficits must occur


def test_monte_carlo_no_deficit_when_capacity_vastly_exceeds_demand():
    demand = np.array([100.0] * 50)
    wind = np.array([0.0] * 50)
    cfg = MonteCarloConfig(n_iterations=100, dispatchable_forced_outage_prob=0.01, dispatchable_outage_severity_fraction=0.1)
    result = run_monte_carlo(demand, wind, domestic_dispatchable_capacity_mw=10000,
                              wind_capacity_mw=0, solar_capacity_mw=0,
                              interconnection_capacity_mw=0, config=cfg)
    assert result["deficit_hour"].sum() == 0


def test_reliability_metrics_zero_lolp_matches_zero_deficits():
    demand = np.array([100.0] * 50)
    wind = np.array([0.0] * 50)
    cfg = MonteCarloConfig(n_iterations=50, dispatchable_forced_outage_prob=0.0)
    result = run_monte_carlo(demand, wind, domestic_dispatchable_capacity_mw=10000,
                              wind_capacity_mw=0, solar_capacity_mw=0,
                              interconnection_capacity_mw=0, config=cfg)
    metrics = compute_reliability_metrics(result)
    assert metrics["LOLP"] == 0.0
    assert metrics["EENS_mwh_per_year"] == 0.0


def test_reliability_metrics_structure():
    demand = np.array([1000.0] * 50)
    wind = np.array([0.0] * 50)
    cfg = MonteCarloConfig(n_iterations=50, dispatchable_forced_outage_prob=0.5, dispatchable_outage_severity_fraction=1.0)
    result = run_monte_carlo(demand, wind, domestic_dispatchable_capacity_mw=1000,
                              wind_capacity_mw=0, solar_capacity_mw=0,
                              interconnection_capacity_mw=0, config=cfg)
    metrics = compute_reliability_metrics(result)
    for key in ["LOLP", "LOLE_hours_per_year", "EENS_mwh_per_year", "total_reserve_violations"]:
        assert key in metrics
