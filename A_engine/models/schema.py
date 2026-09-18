"""
schema.py
=========
Defines the standard, country-agnostic data schema for the national
electricity balance (Level 1 of the project).

Every country dataset, regardless of source or original format, must be
transformed into a DataFrame that follows this schema before it can be
used by the engine. This is what keeps the simulation engine reusable
across countries (see MASTER PROMPT, Section 2 and 23).

Units: all energy quantities are in MWh unless otherwise stated.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd


class DataQuality(str, Enum):
    """Distinguishes real from non-real data, per Section 30 of the
    master prompt. Never silently mix these."""
    MEASURED = "measured"          # Directly reported by an official source
    DERIVED = "derived"            # Computed from measured data (e.g. balance residual)
    ESTIMATED = "estimated"        # Inferred using assumptions, labelled as such
    SYNTHETIC = "synthetic"        # Artificially generated (e.g. for testing only)


# Canonical column names for the Level 1 national balance table.
# A country data loader must produce a DataFrame with (at least) these
# columns before calling the engine.
BALANCE_COLUMNS = [
    "date",                # period start (monthly, daily or hourly timestamp)
    "demand_mwh",          # total electricity demand for the period
    "domestic_generation_mwh",   # total domestic generation, all technologies
    "imports_mwh",         # electricity imported
    "exports_mwh",         # electricity exported
    "losses_mwh",          # transmission/distribution losses (0 if unknown, and flagged)
    "data_quality",        # DataQuality enum value, per row
]


@dataclass
class CountryTimeSeries:
    """
    Thin, validated wrapper around a pandas DataFrame holding a country's
    electricity balance time series. Keeps the engine decoupled from how
    each country's raw files are structured.
    """
    country: str
    resolution: str          # e.g. "monthly", "hourly", "15min"
    data: pd.DataFrame
    source: str = ""
    notes: str = ""

    def __post_init__(self):
        missing = set(BALANCE_COLUMNS) - set(self.data.columns)
        if missing:
            raise ValueError(
                f"CountryTimeSeries for '{self.country}' is missing required "
                f"columns: {missing}. Every country loader must map its raw "
                f"data onto the schema defined in BALANCE_COLUMNS."
            )
        self.data = self.data.sort_values("date").reset_index(drop=True)

    def __len__(self) -> int:
        return len(self.data)
