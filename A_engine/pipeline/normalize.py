"""
normalize.py — Phase 7, stage 4: CLEAN -> NORMALIZE

Converts columns to canonical units (Phase 8, see A_engine/models/units.py).
Every conversion is explicit and logged in the returned report — never
a silent "assume it's already MWh".
"""

from __future__ import annotations
import pandas as pd

from ..models.units import ValueWithUnit, UnitError


def normalize_units(
    df: pd.DataFrame,
    column_units: dict[str, tuple[str, str]],
) -> tuple[pd.DataFrame, list[str]]:
    """
    column_units: {column_name: (quantity, unit_as_found_in_raw_data)}
    e.g. {"generation": ("energy", "GWh")}

    Returns (converted_df, log) where log is a list of human-readable
    strings describing every conversion actually performed (or, if
    already canonical, that no conversion was needed) — so a reviewer
    can see exactly what happened without re-deriving it.
    """
    df = df.copy()
    log = []

    for col, (quantity, unit) in column_units.items():
        if col not in df.columns:
            raise KeyError(f"normalize_units: column '{col}' not found")

        converted_values = []
        for v in df[col]:
            if pd.isna(v):
                converted_values.append(v)  # NaN stays NaN — not this stage's job to decide
                continue
            vwu = ValueWithUnit(value=float(v), unit=unit, quantity=quantity)
            try:
                converted_values.append(vwu.to_canonical())
            except UnitError as e:
                raise UnitError(f"Column '{col}': {e}")

        df[col] = converted_values
        canonical = _canonical_unit_name(quantity)
        if unit == canonical:
            log.append(f"{col}: already in canonical unit ({canonical}), no conversion applied")
        else:
            log.append(f"{col}: converted {unit} -> {canonical}")

    return df, log


def _canonical_unit_name(quantity: str) -> str:
    from ..models.units import CANONICAL_UNITS
    return CANONICAL_UNITS[quantity]
