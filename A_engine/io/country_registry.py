"""
country_registry.py
====================
Maps a country slug to its config file and data loader.

DECISION (per project owner, after Andorra's data proved too limited to
be worth maintaining in parallel): this project is now Estonia-focused.
The registry pattern is kept - the engine in A_engine/models/ still
never mentions a country by name - but only Estonia is registered.
To point this project at a different country, replace B_data/
and C_configs/estonia.yaml with the new country's data/config (or add
a new registry entry here, which is all Section 2's genericity
requirement was ever demonstrating). Andorra's old data lived in
B_data/andorra/ and C_configs/andorra.yaml as a real example of this
before it was removed.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Callable

from .config_loader import load_country_config, CountryConfig
from .data_loader import load_estonia_annual_balance
from ..models.schema import CountryTimeSeries

ROOT = Path(__file__).parent.parent.parent  # project root


@dataclass
class CountryEntry:
    config_path: Path
    balance_loader: Callable[[Path], CountryTimeSeries]
    balance_data_path: Path


REGISTRY: dict[str, CountryEntry] = {
    "estonia": CountryEntry(
        config_path=ROOT / "C_configs" / "estonia.yaml",
        balance_loader=load_estonia_annual_balance,
        balance_data_path=ROOT / "B_data" / "raw" / "elering" / "electricity_balance_annual.csv",
    ),
}


def load_country(slug: str = "estonia") -> tuple[CountryConfig, CountryTimeSeries]:
    """Loads config + balance data for a country by its registry slug.
    Defaults to 'estonia', the only registered country right now."""
    slug = slug.lower()
    if slug not in REGISTRY:
        raise KeyError(f"Unknown country '{slug}'. Available: {list(REGISTRY.keys())}")
    entry = REGISTRY[slug]
    config = load_country_config(entry.config_path)
    ts = entry.balance_loader(entry.balance_data_path)
    return config, ts
