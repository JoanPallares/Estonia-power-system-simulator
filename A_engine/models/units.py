"""
units.py
========
Phase 8: canonical unit definitions and conversions.

Every value that enters `A_engine` past the raw-ingestion stage must be
in its canonical unit. This module is the single place that defines
what "canonical" means, and the only place conversions happen — no
ad-hoc "* 1000" scattered around the codebase.
"""

from __future__ import annotations
from dataclasses import dataclass


class UnitError(ValueError):
    """Raised when a value's stated unit doesn't match what a function expects."""


# Canonical unit per physical quantity used in this project.
CANONICAL_UNITS: dict[str, str] = {
    "power": "MW",
    "energy": "MWh",
    "energy_total": "GWh",       # used for large aggregates/reporting only
    "temperature": "degC",
    "wind_speed": "m/s",
    "irradiance": "W/m2",
}


def mwh_to_gwh(value_mwh: float) -> float:
    return value_mwh / 1000.0


def gwh_to_mwh(value_gwh: float) -> float:
    return value_gwh * 1000.0


def kw_to_mw(value_kw: float) -> float:
    return value_kw / 1000.0


def mw_to_kw(value_mw: float) -> float:
    return value_mw * 1000.0


def kwh_to_mwh(value_kwh: float) -> float:
    return value_kwh / 1000.0


def mwh_to_kwh(value_mwh: float) -> float:
    return value_mwh * 1000.0


@dataclass
class ValueWithUnit:
    """
    Wraps a numeric value with its declared unit so a pipeline stage can
    check it against CANONICAL_UNITS instead of assuming.
    """
    value: float
    unit: str
    quantity: str  # key into CANONICAL_UNITS, e.g. "power", "energy"

    def to_canonical(self) -> float:
        canonical = CANONICAL_UNITS.get(self.quantity)
        if canonical is None:
            raise UnitError(f"Unknown quantity '{self.quantity}' — not in CANONICAL_UNITS")

        if self.unit == canonical:
            return self.value

        conversion = _CONVERSIONS.get((self.quantity, self.unit, canonical))
        if conversion is None:
            raise UnitError(
                f"No known conversion from '{self.unit}' to canonical '{canonical}' "
                f"for quantity '{self.quantity}'. Add one to units.py explicitly — "
                f"never guess a conversion factor inline."
            )
        return conversion(self.value)


_CONVERSIONS = {
    ("energy", "GWh", "MWh"): gwh_to_mwh,
    ("energy", "kWh", "MWh"): kwh_to_mwh,
    ("power", "kW", "MW"): kw_to_mw,
}
