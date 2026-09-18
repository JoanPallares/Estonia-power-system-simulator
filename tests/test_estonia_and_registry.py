"""
Tests for: country_registry.py, generation.py, Estonia loaders.
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.io.country_registry import load_country, REGISTRY
from A_engine.models.balance import compute_balance
from A_engine.models.generation import TechnologyGeneration, summarize_fleet, TECHNOLOGY_TAXONOMY


def test_registry_has_estonia():
    assert "estonia" in REGISTRY


def test_registry_rejects_unknown_country():
    with pytest.raises(KeyError):
        load_country("narnia")


def test_load_country_estonia_runs_through_same_balance_engine():
    """
    The core claim (Research Question 8) is still demonstrated by
    country_registry.py's design (see its docstring), even with only
    Estonia currently registered: compute_balance() itself never
    mentions a country name.
    """
    config, ts = load_country("estonia")
    balance_df = compute_balance(ts)
    assert balance_df.loc[0, "system_balance_mwh"] == pytest.approx(0, abs=1)
    assert config.name == "Estonia"


def test_load_country_defaults_to_estonia():
    config, ts = load_country()
    assert config.name == "Estonia"


def test_technology_generation_capacity_factor():
    tech = TechnologyGeneration(
        technology="wind", capacity_mw=100, generation_mwh=50_000, period_hours=1000,
    )
    # max possible = 100 MW * 1000 h = 100,000 MWh; actual 50,000 -> 50%
    assert tech.capacity_factor == pytest.approx(0.5)


def test_technology_generation_capacity_factor_none_when_capacity_unknown():
    tech = TechnologyGeneration(
        technology="biomass", capacity_mw=None, generation_mwh=1000, period_hours=100,
    )
    assert tech.capacity_factor is None


def test_summarize_fleet_renewable_share():
    fleet = [
        TechnologyGeneration("wind", 100, 30_000, 1000, renewable=True),
        TechnologyGeneration("oil_shale", 500, 70_000, 1000, renewable=False),
    ]
    summary = summarize_fleet(fleet)
    assert summary["total_generation_mwh"] == 100_000
    assert summary["renewable_share_pct"] == 30.0


def test_technology_taxonomy_matches_real_elering_classification():
    """Phase 12: never invent the classification — this is the real one."""
    assert set(TECHNOLOGY_TAXONOMY) == {
        "oil_shale", "natural_gas", "wind", "solar", "hydro", "biomass", "waste", "other",
    }


def test_estonia_hourly_2019_loads_and_covers_full_year():
    from A_engine.io.data_loader import load_estonia_hourly_2019
    from pathlib import Path
    root = Path(__file__).parent.parent
    csv_path = root / "B_data" / "processed" / "estonia_hourly_2019.csv"
    if not csv_path.exists():
        import pytest
        pytest.skip("estonia_hourly_2019.csv not present - run ingest_elering_2019_archive.py first")

    ts = load_estonia_hourly_2019(csv_path)
    assert len(ts) == 8760
    assert ts.resolution == "hourly"


def test_estonia_hourly_2019_balance_closes_tightly():
    from A_engine.io.data_loader import load_estonia_hourly_2019
    from pathlib import Path
    root = Path(__file__).parent.parent
    csv_path = root / "B_data" / "processed" / "estonia_hourly_2019.csv"
    if not csv_path.exists():
        import pytest
        pytest.skip("estonia_hourly_2019.csv not present - run ingest_elering_2019_archive.py first")

    ts = load_estonia_hourly_2019(csv_path)
    balance_df = compute_balance(ts)
    summary_residual_pct = abs(balance_df["system_balance_mwh"].sum()) / balance_df["demand_mwh"].sum() * 100
    assert summary_residual_pct < 0.01  # real data closes to ~0.003%
