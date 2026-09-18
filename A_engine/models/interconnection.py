"""
interconnection.py
===================
Phase 25: cross-border interconnections. Country-agnostic — the class
takes capacity/name as parameters; the REAL numbers live in
C_configs/estonia.yaml and B_data/, not here.

Estonia's two real interconnections, per Elering and the real 2019
archive data already ingested:
  - Finland: EstLink 1 (350 MW) + EstLink 2 (650 MW), HVDC, ~1000-1016 MW combined
  - Latvia: AC-connected (part of the same synchronous area post-2025)

A third historical connection (Russia) existed in the 2019 data but is
explicitly OUT of scope for the current system (see system_definition.md).
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class InterconnectionConfig:
    name: str
    import_capacity_mw: float | None
    export_capacity_mw: float | None
    available: bool = True   # can be flipped False to simulate an outage scenario (Section 15/22)


@dataclass
class InterconnectionFlow:
    """One timestep's flow on one interconnection. Positive = exporting
    FROM the home country, negative = importing INTO it — same
    convention confirmed against the real 2019 Elering data."""
    interconnection: str
    flow_mw: float

    def import_mw(self) -> float:
        return max(0.0, -self.flow_mw)

    def export_mw(self) -> float:
        return max(0.0, self.flow_mw)


def check_capacity_violation(flow: InterconnectionFlow, config: InterconnectionConfig) -> str | None:
    """Returns a description of the violation if the flow exceeds the
    interconnection's rated capacity, else None. Does not clip or hide
    the violation — Level 3/N-1 analysis needs to know this happened."""
    if not config.available:
        if flow.flow_mw != 0:
            return f"{config.name}: nonzero flow ({flow.flow_mw} MW) on an interconnection marked unavailable"
        return None

    if config.export_capacity_mw is not None and flow.export_mw() > config.export_capacity_mw:
        return f"{config.name}: export {flow.export_mw():.1f} MW exceeds rated {config.export_capacity_mw} MW"
    if config.import_capacity_mw is not None and flow.import_mw() > config.import_capacity_mw:
        return f"{config.name}: import {flow.import_mw():.1f} MW exceeds rated {config.import_capacity_mw} MW"
    return None
