"""
Unit tests for A_engine/models/system_status.py
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.system_status import classify_system_status, ReserveThresholds, SystemStatus


def test_stable_when_ample_reserve():
    demand = pd.Series([100.0])
    capacity = pd.Series([150.0])  # 50% reserve margin
    result = classify_system_status(demand, capacity)
    assert result.loc[0, "status"] == SystemStatus.STABLE.value
    assert result.loc[0, "reserve_margin_pct"] == pytest.approx(50.0)


def test_stressed_below_default_threshold():
    demand = pd.Series([100.0])
    capacity = pd.Series([110.0])  # 10% reserve margin, below default 15%
    result = classify_system_status(demand, capacity)
    assert result.loc[0, "status"] == SystemStatus.STRESSED.value


def test_blackout_when_capacity_below_demand():
    demand = pd.Series([100.0])
    capacity = pd.Series([90.0])  # negative reserve margin
    result = classify_system_status(demand, capacity)
    assert result.loc[0, "status"] == SystemStatus.BLACKOUT.value
    assert result.loc[0, "reserve_margin_pct"] < 0


def test_custom_thresholds_are_respected():
    demand = pd.Series([100.0])
    capacity = pd.Series([120.0])  # 20% reserve margin
    strict = ReserveThresholds(stressed_below_pct=25.0, blackout_below_pct=5.0)
    result = classify_system_status(demand, capacity, thresholds=strict)
    # 20% < 25% stressed threshold, but >= 5% blackout threshold -> stressed
    assert result.loc[0, "status"] == SystemStatus.STRESSED.value


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError):
        classify_system_status(pd.Series([100.0, 200.0]), pd.Series([150.0]))


def test_boundary_exactly_at_stressed_threshold():
    # Exactly at the threshold: current implementation treats "< threshold"
    # as stressed, so exactly-equal counts as stable (documents the edge case).
    demand = pd.Series([100.0])
    capacity = pd.Series([115.0])  # exactly 15% reserve margin
    result = classify_system_status(demand, capacity)
    assert result.loc[0, "status"] == SystemStatus.STABLE.value
