"""
state.py
========
Phase 23: SystemState — a complete snapshot of the system at one
timestep. This is the object the timestep simulation loop (simulator.py)
produces once per step, and everything downstream (reserve, status
classification, KPIs) reads from it.

Country-agnostic, technology-agnostic. Deliberately a plain dataclass,
not a class with behaviour — state should be inspectable and easy to
serialize (e.g. to a DataFrame row) without surprises.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class SystemState:
    timestamp: pd.Timestamp

    demand_mw: float
    domestic_generation_mw: float
    renewable_generation_mw: float | None      # None if not disaggregated at this timestep (be honest, don't force 0)

    available_capacity_mw: float | None         # what COULD be supplied right now — None if unknown, never guessed

    imports_mw: float
    exports_mw: float

    reserve_mw: float | None                    # available_capacity - demand, once available_capacity is known
    reserve_margin_pct: float | None

    storage_soc_mwh: float | None                # None if no storage modelled
    storage_charge_mw: float = 0.0                # positive = charging, negative = discharging
    curtailment_mw: float = 0.0                   # renewable output that COULD have been produced but wasn't used
    unserved_energy_mw: float = 0.0               # demand that could not be met

    component_status: dict[str, str] = field(default_factory=dict)  # e.g. {"finland_interconnection": "normal", "battery": "offline"}

    def to_dict(self) -> dict:
        d = {
            "timestamp": self.timestamp,
            "demand_mw": self.demand_mw,
            "domestic_generation_mw": self.domestic_generation_mw,
            "renewable_generation_mw": self.renewable_generation_mw,
            "available_capacity_mw": self.available_capacity_mw,
            "imports_mw": self.imports_mw,
            "exports_mw": self.exports_mw,
            "reserve_mw": self.reserve_mw,
            "reserve_margin_pct": self.reserve_margin_pct,
            "storage_soc_mwh": self.storage_soc_mwh,
            "storage_charge_mw": self.storage_charge_mw,
            "curtailment_mw": self.curtailment_mw,
            "unserved_energy_mw": self.unserved_energy_mw,
        }
        for k, v in self.component_status.items():
            d[f"status__{k}"] = v
        return d


def states_to_dataframe(states: list[SystemState]) -> pd.DataFrame:
    return pd.DataFrame([s.to_dict() for s in states])
