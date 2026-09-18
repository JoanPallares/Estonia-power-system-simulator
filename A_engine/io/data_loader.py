"""
data_loader.py
===============
Country-specific loaders. Each loader's only job is to transform a
country's raw data files into the standard schema (schema.py) so the
generic engine never needs to know anything about the original format.

Adding a new country means writing ONE new function here (or a new
module if it gets complex) — the engine itself never changes.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

from ..models.schema import CountryTimeSeries, BALANCE_COLUMNS


def load_estonia_annual_balance(csv_path: str | Path) -> CountryTimeSeries:
    """
    Loads Estonia's annual national electricity balance (currently one
    fully-sourced year: 2024).

    IMPORTANT — data provenance (MASTER PROMPT, Section 30):
    Compiled from Elering's (Estonia's TSO) public web pages and Enerdata's
    country profile. Unlike Andorra, Estonia is a full ENTSO-E member with
    an open-data API (dashboard.elering.ee) — this loader currently uses
    manually-compiled figures, not the live API, as a first step. See
    B_data/metadata/data_catalogue.csv for exactly which numbers
    are measured vs derived, including a flagged possible year mismatch
    between the demand figure (confirmed 2024) and the import share (most
    recently published %, exact year not stated by the source).
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path, parse_dates=["date"])

    missing = set(BALANCE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Estonia raw CSV is missing expected columns: {missing}")

    return CountryTimeSeries(
        country="Estonia",
        resolution="annual",
        data=df[BALANCE_COLUMNS],
        source="Elering (Estonia TSO) + Enerdata country profile (manually compiled)",
        notes=(
            "Only one fully-sourced annual data point (2024) currently compiled. "
            "Estonia is ENTSO-E-member-grade data quality; this is a starting "
            "point, not a limit — the live Elering API can extend this to "
            "hourly resolution in a future iteration."
        ),
    )


def load_estonia_generation_by_technology(csv_path: str | Path) -> pd.DataFrame:
    """
    Loads Estonia's real quarterly generation-by-technology data
    (wind/solar/biomass for Q3 2025) — used by the generation.py module
    (Level 2), not by the Level 1 balance engine.
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)
    required = {"quarter", "technology", "generation_mwh", "installed_capacity_mw", "renewable"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Estonia generation-by-technology CSV missing columns: {missing}")
    return df


def load_estonia_hourly_2019(csv_path: str | Path) -> CountryTimeSeries:
    """
    Loads Estonia's REAL hourly 2019 balance — MASTER PROMPT Phase 11.

    Source: B_data/raw/elering/2019_arhiiv_0.xls (uploaded by
    the project owner; this sandbox has no network access to elering.ee).
    Processed by ingest_elering_2019_archive.py, which documents two
    real data-quality corrections (a source-file typo, and an explicit,
    logged resolution of the one real DST fall-back ambiguity).

    losses_mwh is set to 0 for every row — DELIBERATELY, not as a
    simplifying assumption. Phase 11 explicitly says: don't assume you
    know 'losses'. The resulting system_balance_mwh IS the residual to
    study (it closed to 0.0026% of demand across the full year using
    only demand, generation and the three physical cross-border flow
    columns — see docs/data_discovery notes).

    imports/exports are DERIVED (netted from three physical flow
    columns: EE-FI, EE-RU, EE-LV), not directly reported as single
    columns in the source. demand and generation ARE directly reported
    (SCADA-measured).
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run ingest_elering_2019_archive.py first "
            f"(requires B_data/raw/elering/2019_arhiiv_0.xls to be present)."
        )

    raw = pd.read_csv(csv_path, parse_dates=["timestamp_utc"])

    df = pd.DataFrame({
        "date": raw["timestamp_utc"],
        "demand_mwh": raw["demand_mw"],       # hourly MW average == MWh for a 1h period
        "domestic_generation_mwh": raw["generation_mw"],
        "imports_mwh": raw["imports_mw"],
        "exports_mwh": raw["exports_mw"],
        "losses_mwh": 0.0,
        "data_quality": "derived",  # imports/exports are netted/derived; demand/generation are measured
    })

    return CountryTimeSeries(
        country="Estonia",
        resolution="hourly",
        data=df[BALANCE_COLUMNS],
        source="Elering historical archive (2019_arhiiv_0.xls), ingested via ingest_elering_2019_archive.py",
        notes=(
            "REAL, hourly, full year 2019 (8760 rows, 0 missing). demand_mwh and "
            "domestic_generation_mwh are directly SCADA-measured. imports_mwh/"
            "exports_mwh are DERIVED (netted from 3 physical flow columns: "
            "EE-FI, EE-RU, EE-LV). losses_mwh intentionally left at 0, not "
            "assumed — see Phase 11: the resulting balance residual (~0.0026% "
            "of demand) is itself the finding, not an error to hide."
        ),
    )

