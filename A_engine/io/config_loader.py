"""
config_loader.py
=================
Loads a country's configuration file (C_configs/<country>.yaml).

This is the piece that makes "changing country = changing config" real
(MASTER PROMPT, Section 2). The engine never hard-codes country names,
capacities or interconnections — it reads them from here.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class InterconnectionConfig:
    name: str
    import_capacity_mw: float | None = None
    export_capacity_mw: float | None = None


@dataclass
class GenerationTechConfig:
    technology: str
    capacity_mw: float | None = None
    renewable: bool = True


@dataclass
class ReserveThresholdsConfig:
    stressed_below_pct: float = 15.0
    blackout_below_pct: float = 0.0


@dataclass
class CountryConfig:
    name: str
    resolution: str
    generation: list[GenerationTechConfig] = field(default_factory=list)
    interconnections: list[InterconnectionConfig] = field(default_factory=list)
    reserve_thresholds: ReserveThresholdsConfig = field(default_factory=ReserveThresholdsConfig)
    peak_demand_mw: float | None = None
    installed_capacity_total_mw: float | None = None
    data_source_notes: str = ""
    raw: dict = field(default_factory=dict)  # full original YAML, for anything not modelled yet


def load_country_config(path: str | Path) -> CountryConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Country config not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    country_name = raw.get("country", {}).get("name", "UNKNOWN")
    resolution = raw.get("simulation", {}).get("timestep", "unknown")

    generation = [
        GenerationTechConfig(
            technology=tech_name,
            capacity_mw=tech_data.get("capacity_mw"),
            renewable=tech_data.get("renewable", True),
        )
        for tech_name, tech_data in (raw.get("generation") or {}).items()
    ]

    interconnections = [
        InterconnectionConfig(
            name=ic.get("name", "unknown"),
            import_capacity_mw=ic.get("import_capacity_mw"),
            export_capacity_mw=ic.get("export_capacity_mw"),
        )
        for ic in (raw.get("interconnections") or [])
    ]

    reliability_section = raw.get("reliability", {})
    reliability_raw = reliability_section.get("reserve_thresholds", {})
    reserve_thresholds = ReserveThresholdsConfig(
        stressed_below_pct=reliability_raw.get("stressed_below_pct", 15.0),
        blackout_below_pct=reliability_raw.get("blackout_below_pct", 0.0),
    )

    return CountryConfig(
        name=country_name,
        resolution=resolution,
        generation=generation,
        interconnections=interconnections,
        reserve_thresholds=reserve_thresholds,
        peak_demand_mw=reliability_section.get("peak_demand_mw"),
        installed_capacity_total_mw=reliability_section.get("installed_capacity_total_mw"),
        data_source_notes=raw.get("data_source_notes", ""),
        raw=raw,
    )
