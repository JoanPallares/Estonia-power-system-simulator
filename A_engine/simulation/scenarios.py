"""
scenarios.py
============
Phase 31: the scenario engine. Applies a ScenarioConfig (matching the
exact YAML schema requested) to a baseline hourly DataFrame, producing
a modified DataFrame — never mutating the original, always reproducible
from the config alone (MASTER PROMPT Section 22).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import pandas as pd


@dataclass
class ScenarioConfig:
    name: str
    description: str = ""
    demand_multiplier: float = 1.0
    wind_multiplier: float = 1.0
    solar_multiplier: float = 1.0
    hydro_availability: float = 1.0        # 0-1, fraction of normal hydro available
    oil_shale_availability: float = 1.0     # 0-1, fraction of normal oil-shale/other-dispatchable capacity available
    import_capacity_multiplier: float = 1.0  # applied to each interconnection's rated capacity
    storage_capacity_mwh: float = 0.0        # 0 = no storage (Estonia's real current situation)


def load_scenarios(path: str | Path) -> list[ScenarioConfig]:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    scenarios = []
    for entry in raw["scenarios"]:
        s = entry.get("scenario", {})
        scenarios.append(ScenarioConfig(
            name=entry["name"],
            description=entry.get("description", ""),
            demand_multiplier=s.get("demand_multiplier", 1.0),
            wind_multiplier=s.get("wind_multiplier", 1.0),
            solar_multiplier=s.get("solar_multiplier", 1.0),
            hydro_availability=s.get("hydro_availability", 1.0),
            oil_shale_availability=s.get("oil_shale_availability", 1.0),
            import_capacity_multiplier=s.get("import_capacity_multiplier", 1.0),
            storage_capacity_mwh=s.get("storage_capacity_mwh", 0.0),
        ))
    return scenarios


def apply_scenario(baseline_df: pd.DataFrame, scenario: ScenarioConfig) -> pd.DataFrame:
    """
    baseline_df expects columns: demand_mw, wind_generation_mw,
    generation_mw (total domestic — used to derive a non-wind residual
    that oil_shale_availability scales), imports_mw, exports_mw.

    Returns a NEW DataFrame (baseline is never mutated) with the
    scenario's multipliers applied. Solar is scaled even though 2019
    had ~0 real solar (Phase 19) — the multiplier is applied to
    whatever is in the 'solar_generation_mw' column if present, else
    treated as 0 throughout (never fabricated).
    """
    df = baseline_df.copy()

    df["demand_mw"] = df["demand_mw"] * scenario.demand_multiplier
    df["wind_generation_mw"] = df["wind_generation_mw"] * scenario.wind_multiplier

    if "solar_generation_mw" in df.columns:
        df["solar_generation_mw"] = df["solar_generation_mw"] * scenario.solar_multiplier

    non_wind_mw = df["generation_mw"] - baseline_df["wind_generation_mw"]
    non_wind_mw = non_wind_mw * scenario.oil_shale_availability  # bundles oil shale + other dispatchable, see generation.py taxonomy notes
    df["generation_mw"] = non_wind_mw + df["wind_generation_mw"]

    df["import_capacity_multiplier"] = scenario.import_capacity_multiplier  # consumed by failure/reserve logic downstream, not applied to flows directly here

    return df
