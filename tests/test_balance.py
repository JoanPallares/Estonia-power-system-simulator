"""
Unit tests for the Level 1 engine. Run with: pytest tests/
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.schema import CountryTimeSeries, BALANCE_COLUMNS
from A_engine.models.balance import compute_balance, balance_summary
from D_analysis.validation import (
    check_balance_consistency, mae, rmse, mape, annual_energy_error,
)


def make_ts(rows: list[dict]) -> CountryTimeSeries:
    df = pd.DataFrame(rows)
    return CountryTimeSeries(country="TestLand", resolution="monthly", data=df)


def test_schema_rejects_missing_columns():
    df = pd.DataFrame({"date": ["2025-01-01"], "demand_mwh": [100]})
    with pytest.raises(ValueError):
        CountryTimeSeries(country="X", resolution="monthly", data=df)


def test_balance_is_zero_when_perfectly_consistent():
    ts = make_ts([
        {"date": "2025-01-01", "demand_mwh": 100, "domestic_generation_mwh": 40,
         "imports_mwh": 60, "exports_mwh": 0, "losses_mwh": 0, "data_quality": "measured"},
    ])
    balance_df = compute_balance(ts)
    assert balance_df.loc[0, "system_balance_mwh"] == 0
    assert balance_df.loc[0, "self_sufficiency_ratio"] == pytest.approx(0.4)
    assert balance_df.loc[0, "import_dependency_ratio"] == pytest.approx(0.6)


def test_balance_flags_inconsistent_period():
    ts = make_ts([
        {"date": "2025-01-01", "demand_mwh": 100, "domestic_generation_mwh": 40,
         "imports_mwh": 40, "exports_mwh": 0, "losses_mwh": 0, "data_quality": "measured"},
        # generation + imports = 80, demand = 100 -> 20 unit deficit -> should be flagged
    ])
    balance_df = compute_balance(ts)
    checked = check_balance_consistency(balance_df, tolerance_pct=1.0)
    assert checked.loc[0, "consistency_flag"] == True  # noqa: E712


def test_balance_summary_matches_manual_sum():
    ts = make_ts([
        {"date": "2025-01-01", "demand_mwh": 100, "domestic_generation_mwh": 40,
         "imports_mwh": 60, "exports_mwh": 0, "losses_mwh": 0, "data_quality": "measured"},
        {"date": "2025-02-01", "demand_mwh": 200, "domestic_generation_mwh": 80,
         "imports_mwh": 120, "exports_mwh": 0, "losses_mwh": 0, "data_quality": "measured"},
    ])
    balance_df = compute_balance(ts)
    summary = balance_summary(balance_df)
    assert summary["total_demand_mwh"] == 300
    assert summary["total_domestic_generation_mwh"] == 120
    assert summary["balance_residual_mwh"] == 0


def test_validation_metrics():
    real = pd.Series([100.0, 200.0, 300.0])
    simulated = pd.Series([110.0, 190.0, 300.0])

    assert mae(real, simulated) == pytest.approx(20 / 3, rel=1e-3)
    assert rmse(real, simulated) > 0
    assert mape(real, simulated) > 0
    assert annual_energy_error(real, simulated) == pytest.approx(0.0, abs=0.5)


def test_data_quality_column_required():
    assert "data_quality" in BALANCE_COLUMNS
