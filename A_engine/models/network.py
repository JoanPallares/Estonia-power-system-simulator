"""
network.py
==========
Phase 37 (Level 3 foundation): generic network representation.

*** NO REAL ESTONIAN TOPOLOGY IS POPULATED HERE ***
This is pure architecture — Bus/Generator/Load/Line/Transformer/
Interconnection classes and a NetworkX-backed graph container — ready
for real substation/line data the moment it's available (see
docs/network_data_findings.md for exactly what's blocking that and the
two ways to unblock it). Populating this with invented coordinates or
line capacities would violate this project's core data-honesty rule.

Uses NetworkX (MASTER PROMPT Section 24 explicitly allows it).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import networkx as nx


@dataclass
class Bus:
    id: str
    name: str
    voltage_kv: float | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class Generator:
    id: str
    bus_id: str
    technology: str
    capacity_mw: float | None = None


@dataclass
class Load:
    id: str
    bus_id: str
    peak_demand_mw: float | None = None


@dataclass
class Line:
    id: str
    from_bus_id: str
    to_bus_id: str
    voltage_kv: float | None = None
    thermal_limit_mw: float | None = None
    length_km: float | None = None


@dataclass
class Transformer:
    id: str
    bus_id_primary: str
    bus_id_secondary: str
    rating_mva: float | None = None


@dataclass
class NetworkInterconnection:
    id: str
    bus_id: str
    neighbouring_country: str
    import_capacity_mw: float | None = None
    export_capacity_mw: float | None = None


class PowerNetwork:
    """
    Thin wrapper around a networkx.Graph — buses are nodes, lines/
    transformers/interconnections are edges. Generators and loads are
    attached to buses (a bus can have zero, one, or several of each).
    """

    def __init__(self):
        self.graph = nx.Graph()
        self.buses: dict[str, Bus] = {}
        self.generators: dict[str, Generator] = {}
        self.loads: dict[str, Load] = {}
        self.lines: dict[str, Line] = {}
        self.transformers: dict[str, Transformer] = {}
        self.interconnections: dict[str, NetworkInterconnection] = {}

    def add_bus(self, bus: Bus) -> None:
        self.buses[bus.id] = bus
        self.graph.add_node(bus.id, **bus.__dict__)

    def add_generator(self, generator: Generator) -> None:
        if generator.bus_id not in self.buses:
            raise KeyError(f"Generator '{generator.id}' references unknown bus '{generator.bus_id}'")
        self.generators[generator.id] = generator

    def add_load(self, load: Load) -> None:
        if load.bus_id not in self.buses:
            raise KeyError(f"Load '{load.id}' references unknown bus '{load.bus_id}'")
        self.loads[load.id] = load

    def add_line(self, line: Line) -> None:
        for bus_id in (line.from_bus_id, line.to_bus_id):
            if bus_id not in self.buses:
                raise KeyError(f"Line '{line.id}' references unknown bus '{bus_id}'")
        self.lines[line.id] = line
        self.graph.add_edge(line.from_bus_id, line.to_bus_id, kind="line", id=line.id)

    def add_transformer(self, transformer: Transformer) -> None:
        for bus_id in (transformer.bus_id_primary, transformer.bus_id_secondary):
            if bus_id not in self.buses:
                raise KeyError(f"Transformer '{transformer.id}' references unknown bus '{bus_id}'")
        self.transformers[transformer.id] = transformer
        self.graph.add_edge(transformer.bus_id_primary, transformer.bus_id_secondary, kind="transformer", id=transformer.id)

    def add_interconnection(self, ic: NetworkInterconnection) -> None:
        if ic.bus_id not in self.buses:
            raise KeyError(f"Interconnection '{ic.id}' references unknown bus '{ic.bus_id}'")
        self.interconnections[ic.id] = ic

    def is_connected(self) -> bool:
        """Whether the network graph (buses + lines/transformers) forms
        a single connected component — a basic sanity check before any
        power-flow analysis (Level 3, not yet built)."""
        if len(self.graph.nodes) == 0:
            return True
        return nx.is_connected(self.graph)

    def summary(self) -> dict:
        return {
            "n_buses": len(self.buses),
            "n_generators": len(self.generators),
            "n_loads": len(self.loads),
            "n_lines": len(self.lines),
            "n_transformers": len(self.transformers),
            "n_interconnections": len(self.interconnections),
            "is_connected": self.is_connected(),
        }
