"""
Tests for Phase 8 (units), Phase 9 (time_handling), Phase 7/10 (pipeline).
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.units import ValueWithUnit, UnitError, mwh_to_gwh, gwh_to_mwh
from A_engine.models.time_handling import (
    localize_naive_index, to_utc, detect_dst_transition_days, validate_hourly_continuity,
    CANONICAL_TIMEZONE,
)
from A_engine.pipeline.read import read_raw_csv
from A_engine.pipeline.parse import parse_types
from A_engine.pipeline.clean import strip_whitespace, drop_exact_duplicate_rows, rename_columns
from A_engine.pipeline.normalize import normalize_units
from A_engine.pipeline.quality import (
    check_missing, check_duplicates, check_negative, check_impossible, check_outliers,
)
from A_engine.pipeline.pipeline import run_pipeline, PipelineConfig
from D_analysis.validation import peak_demand_error, generation_error, multi_resolution_comparison


# --- units.py ---

def test_mwh_gwh_roundtrip():
    assert gwh_to_mwh(mwh_to_gwh(1000)) == pytest.approx(1000)


def test_value_with_unit_already_canonical():
    v = ValueWithUnit(value=42.0, unit="MWh", quantity="energy")
    assert v.to_canonical() == 42.0


def test_value_with_unit_converts_gwh():
    v = ValueWithUnit(value=1.0, unit="GWh", quantity="energy")
    assert v.to_canonical() == 1000.0


def test_value_with_unit_unknown_conversion_raises():
    v = ValueWithUnit(value=1.0, unit="furlongs", quantity="energy")
    with pytest.raises(UnitError):
        v.to_canonical()


# --- time_handling.py ---

def test_localize_naive_index():
    idx = pd.date_range("2025-06-01", periods=3, freq="h")
    localized = localize_naive_index(idx)
    assert str(localized.tz) == CANONICAL_TIMEZONE


def test_localize_already_aware_raises():
    idx = pd.date_range("2025-06-01", periods=3, freq="h", tz="UTC")
    with pytest.raises(ValueError):
        localize_naive_index(idx)


def test_to_utc_requires_aware_index():
    idx = pd.date_range("2025-06-01", periods=3, freq="h")
    with pytest.raises(ValueError):
        to_utc(idx)


def test_detect_dst_no_transition_in_stable_period():
    # A week fully within EEST (summer), no transition expected
    idx = pd.date_range("2025-07-01", periods=24 * 7, freq="h", tz=CANONICAL_TIMEZONE)
    result = detect_dst_transition_days(idx)
    assert result["short_days"] == []
    assert result["long_days"] == []


def test_validate_hourly_continuity_detects_gap():
    idx = pd.date_range("2025-06-01", periods=5, freq="h", tz=CANONICAL_TIMEZONE)
    idx_with_gap = idx.delete(2)  # remove the 3rd hour
    result = validate_hourly_continuity(idx_with_gap)
    assert len(result["gaps"]) == 1


def test_validate_hourly_continuity_no_false_positive_on_clean_series():
    idx = pd.date_range("2025-06-01", periods=48, freq="h", tz=CANONICAL_TIMEZONE)
    result = validate_hourly_continuity(idx)
    assert result["gaps"] == []
    assert result["duplicates"] == []


# --- pipeline stages ---

def test_read_raw_csv_reads_as_strings(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("a,b\n1,2\n")
    df = read_raw_csv(p)
    assert df["a"].iloc[0] == "1"  # still a string, not parsed yet


def test_parse_types_converts_numeric():
    df = pd.DataFrame({"x": ["1", "2", "3"]})
    parsed = parse_types(df, numeric_columns=["x"])
    assert parsed["x"].dtype.kind in "if"


def test_parse_types_raises_on_bad_numeric():
    df = pd.DataFrame({"x": ["1", "not_a_number"]})
    with pytest.raises(ValueError):
        parse_types(df, numeric_columns=["x"])


def test_parse_types_bool_column():
    df = pd.DataFrame({"flag": ["true", "false", "True"]})
    parsed = parse_types(df, bool_columns=["flag"])
    assert list(parsed["flag"]) == [True, False, True]


def test_drop_exact_duplicate_rows():
    df = pd.DataFrame({"a": [1, 1, 2], "b": [1, 1, 2]})
    deduped, dropped = drop_exact_duplicate_rows(df)
    assert dropped == 1
    assert len(deduped) == 2


def test_rename_columns_raises_on_missing_source():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(KeyError):
        rename_columns(df, {"nonexistent": "b"})


def test_normalize_units_converts_and_logs():
    df = pd.DataFrame({"energy": [1.0, 2.0]})
    converted, log = normalize_units(df, {"energy": ("energy", "GWh")})
    assert converted["energy"].tolist() == [1000.0, 2000.0]
    assert "converted GWh -> MWh" in log[0]


def test_normalize_units_preserves_nan():
    df = pd.DataFrame({"energy": [1.0, None]})
    converted, _ = normalize_units(df, {"energy": ("energy", "MWh")})
    assert pd.isna(converted["energy"].iloc[1])


# --- quality.py ---

def test_check_missing():
    df = pd.DataFrame({"a": [1, None, 3]})
    result = check_missing(df, ["a"])
    assert result == {"a": 1}


def test_check_negative_flags_bad_rows():
    df = pd.DataFrame({"generation_mwh": [10, -5, 3]})
    result = check_negative(df, ["generation_mwh"])
    assert result["generation_mwh"] == [1]


def test_check_impossible_range():
    df = pd.DataFrame({"capacity_factor": [0.5, 1.5, 0.9]})
    result = check_impossible(df, "capacity_factor", 0.0, 1.05)
    assert result == [1]


def test_check_outliers_flags_extreme_value():
    df = pd.DataFrame({"x": [10, 11, 9, 10, 10, 11, 9, 10, 11, 9, 500]})
    result = check_outliers(df, "x", z_threshold=2.0)
    assert 10 in result


# --- full pipeline, real data ---

def test_full_pipeline_on_real_estonia_generation_data():
    config = PipelineConfig(
        numeric_columns=["generation_mwh", "installed_capacity_mw"],
        bool_columns=["renewable"],
        missing_check_columns=["generation_mwh", "installed_capacity_mw"],
        nonnegative_columns=["generation_mwh", "installed_capacity_mw"],
    )
    root = Path(__file__).parent.parent
    result = run_pipeline(
        raw_path=root / "B_data" / "raw" / "elering" / "generation_by_technology_quarterly.csv",
        config=config,
        dataset_name="test",
    )
    assert len(result.processed_df) == 3
    # The real, known data gap: biomass capacity is genuinely missing
    assert result.quality_report.missing_values.get("installed_capacity_mw") == 1
    assert not result.quality_report.is_clean()  # correctly NOT clean, because of that gap


# --- Phase 14 validation metrics ---

def test_peak_demand_error_zero_when_identical():
    s = pd.Series([10, 20, 30])
    assert peak_demand_error(s, s) == pytest.approx(0.0)


def test_peak_demand_error_detects_overestimate():
    real = pd.Series([10, 20, 30])
    simulated = pd.Series([10, 20, 33])  # peak overestimated by 10%
    assert peak_demand_error(real, simulated) == pytest.approx(10.0)


def test_generation_error_same_formula_as_annual_energy_error():
    real = pd.Series([100, 100])
    simulated = pd.Series([110, 110])
    assert generation_error(real, simulated) == pytest.approx(10.0)


def test_multi_resolution_comparison_structure():
    dates = pd.date_range("2024-01-01", periods=48, freq="h", tz="UTC")
    df = pd.DataFrame({"date": dates, "real": range(48), "sim": range(48)})
    result = multi_resolution_comparison(df, "date", "real", "sim")
    assert "native" in result
    assert "daily" in result
    assert result["native"]["mae"] == pytest.approx(0.0)
