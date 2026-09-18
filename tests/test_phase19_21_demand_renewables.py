"""
Tests for Phase 19 (solar/hydro profiles), Phase 21 (demand calendar
model), and the generic renewable physical functions.
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.generation import ESTONIA_SOLAR_PROFILE, ESTONIA_HYDRO_PROFILE
from A_engine.models.demand import add_calendar_features, demand_profile_summary, ESTONIA_PUBLIC_HOLIDAYS_2019
from A_engine.models.renewable_physical import generic_wind_power_curve, generic_pv_model


# --- Phase 19/20 profiles ---

def test_solar_profile_has_real_capacity_and_standard_cost_assumptions():
    assert ESTONIA_SOLAR_PROFILE.capacity_mw == 1210
    assert ESTONIA_SOLAR_PROFILE.marginal_cost_eur_per_mwh == 0
    assert ESTONIA_SOLAR_PROFILE.variable is True
    assert ESTONIA_SOLAR_PROFILE.dispatchable is False


def test_hydro_profile_reflects_real_tiny_estonian_capacity():
    assert ESTONIA_HYDRO_PROFILE.capacity_mw == 7  # real, confirmed, not a data gap
    assert ESTONIA_HYDRO_PROFILE.renewable is True


# --- Phase 21: demand calendar features ---

def test_add_calendar_features_basic_columns():
    df = pd.DataFrame({"ts": pd.date_range("2019-06-03", periods=3, freq="h", tz="UTC")})  # a Monday
    result = add_calendar_features(df, "ts")
    assert result.loc[0, "day_of_week"] == 0  # Monday
    assert result.loc[0, "is_weekend"] == False  # noqa: E712
    assert result.loc[0, "season"] == "summer"


def test_add_calendar_features_weekend_detection():
    df = pd.DataFrame({"ts": pd.date_range("2019-06-08", periods=1, freq="h", tz="UTC")})  # a Saturday
    result = add_calendar_features(df, "ts")
    assert bool(result.loc[0, "is_weekend"]) is True


def test_holiday_detection_matches_local_tallinn_date_not_utc_date():
    """
    Regression test for the real bug caught during development: New
    Year's Day 2019-01-01 00:00 in Tallinn local time is
    2018-12-31 22:00 in UTC. A naive UTC-date comparison would miss it.
    """
    df = pd.DataFrame({"ts": [pd.Timestamp("2018-12-31 22:00:00", tz="UTC")]})  # = 2019-01-01 00:00 Tallinn
    result = add_calendar_features(df, "ts", holidays=ESTONIA_PUBLIC_HOLIDAYS_2019)
    assert bool(result.loc[0, "is_holiday"]) is True


def test_demand_profile_summary_structure():
    df = pd.DataFrame({
        "ts": pd.date_range("2019-01-01", periods=48, freq="h", tz="UTC"),
        "demand_mw": [1000 + i for i in range(48)],
    })
    df = add_calendar_features(df, "ts")
    summary = demand_profile_summary(df, "demand_mw")
    assert "by_hour" in summary
    assert "by_season" in summary
    assert len(summary["by_hour"]) == 24


# --- Generic renewable physical functions (explicitly uncalibrated) ---

def test_wind_power_curve_below_cut_in_is_zero():
    assert generic_wind_power_curve(2.0, rated_capacity_mw=100) == 0.0


def test_wind_power_curve_above_cut_out_is_zero():
    assert generic_wind_power_curve(30.0, rated_capacity_mw=100) == 0.0


def test_wind_power_curve_at_rated_speed_is_full_capacity():
    assert generic_wind_power_curve(12.0, rated_capacity_mw=100) == 100.0


def test_wind_power_curve_between_cutin_and_rated_is_partial():
    output = generic_wind_power_curve(7.5, rated_capacity_mw=100)
    assert 0 < output < 100


def test_pv_model_zero_irradiance_is_zero_output():
    assert generic_pv_model(0, capacity_mw=100) == 0.0


def test_pv_model_full_irradiance_scales_by_performance_ratio():
    output = generic_pv_model(1000, capacity_mw=100, performance_ratio=0.8)
    assert output == pytest.approx(80.0)


def test_pv_model_caps_at_full_capacity_above_reference_irradiance():
    output = generic_pv_model(1500, capacity_mw=100, performance_ratio=0.8)
    assert output == pytest.approx(80.0)  # clipped, not overshooting
