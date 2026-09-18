"""
n_minus_1.py
=============
Phase 41: N-1 contingency analysis for LINES (the analysis that fits
our DC power flow model directly — generator and interconnection
contingencies are already covered by the reserve-margin-style analysis
in run_failure_deterministic.py / Phase 33, a different, complementary
paradigm; conflating them into one DC-power-flow-based function would
misrepresent what a generator/interconnection outage actually means
physically in this model).

For each line: remove it, recompute, check:
  1. Does the network stay connected? (if not: real load loss — some
     buses become physically unreachable from the slack bus)
  2. Do any OTHER lines become congested as a result? (Section
     17's "power redistribution -> overload" mechanism, one step)

Produces a criticality ranking.
"""

from __future__ import annotations
from dataclasses import dataclass
import networkx as nx

from ..models.network import PowerNetwork, Line
from .dc_power_flow import run_dc_power_flow, check_congestion


@dataclass
class ContingencyResult:
    line_id: str
    from_bus: str
    to_bus: str
    is_synthetic: bool
    disconnects_network: bool
    isolated_bus_count: int
    new_violations_count: int
    worst_overload_pct: float


def run_n_minus_1_lines(net: PowerNetwork, base_injections: dict, slack_bus: str) -> list[ContingencyResult]:
    results = []

    for line_id, line in net.lines.items():
        test_net = _network_without_line(net, line_id)

        if not test_net.is_connected():
            components = list(nx.connected_components(test_net.graph))
            components.sort(key=len, reverse=True)
            isolated_count = sum(len(c) for c in components[1:])
            results.append(ContingencyResult(
                line_id=line_id, from_bus=line.from_bus_id, to_bus=line.to_bus_id,
                is_synthetic=(line.length_km is not None and line.length_km < 0.15),
                disconnects_network=True, isolated_bus_count=isolated_count,
                new_violations_count=-1, worst_overload_pct=-1,  # power flow not meaningful on a split network
            ))
            continue

        try:
            result = run_dc_power_flow(test_net, base_injections, slack_bus)
            violations = check_congestion(result.line_flows_mw, test_net)
            worst = max((v.overload_pct for v in violations), default=0.0)
            results.append(ContingencyResult(
                line_id=line_id, from_bus=line.from_bus_id, to_bus=line.to_bus_id,
                is_synthetic=(line.length_km is not None and line.length_km < 0.15),
                disconnects_network=False, isolated_bus_count=0,
                new_violations_count=len(violations), worst_overload_pct=worst,
            ))
        except Exception:
            # Singular B matrix or similar numerical issue on this specific
            # contingency — recorded, not silently skipped.
            results.append(ContingencyResult(
                line_id=line_id, from_bus=line.from_bus_id, to_bus=line.to_bus_id,
                is_synthetic=(line.length_km is not None and line.length_km < 0.15),
                disconnects_network=False, isolated_bus_count=0,
                new_violations_count=-2, worst_overload_pct=-2,  # -2 = numerical failure, distinct from -1 = disconnected
            ))

    return results


def _network_without_line(net: PowerNetwork, exclude_line_id: str) -> PowerNetwork:
    new_net = PowerNetwork()
    for bus in net.buses.values():
        new_net.add_bus(bus)
    for lid, line in net.lines.items():
        if lid != exclude_line_id:
            new_net.add_line(line)
    return new_net


def criticality_ranking(results: list[ContingencyResult]) -> list[ContingencyResult]:
    """Sorts worst-first: disconnection (real load loss) ranks above
    any congestion-only outcome; among congestion outcomes, more/worse
    violations rank higher."""
    def sort_key(r: ContingencyResult):
        return (
            0 if r.disconnects_network else 1,
            -r.isolated_bus_count,
            -r.new_violations_count,
            -r.worst_overload_pct,
        )
    return sorted(results, key=sort_key)
