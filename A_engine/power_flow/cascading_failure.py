"""
cascading_failure.py
======================
Phase 42: cascading failure — ONLY built after N-1 (Phase 41) works,
as instructed. Reuses the same DC power flow + congestion check.

    Line failure -> Power redistribution -> Overload -> Trip -> repeat

Trip criterion: a line trips if its overload exceeds `trip_threshold_pct`
(default 20% over its assumed thermal limit) — an ASSUMED protection
setting, not a real Estonian grid protection scheme (which would
depend on real relay settings this project doesn't have).

Stops when: no line is overloaded past the threshold, OR the network
becomes disconnected (a real blackout in this simplified model), OR a
safety cap on iterations is reached (never loop forever on a numerical
edge case).
"""

from __future__ import annotations
from dataclasses import dataclass, field

from .dc_power_flow import run_dc_power_flow, check_congestion


@dataclass
class CascadeStep:
    tripped_line_id: str
    reason: str  # "initial" or "overload_cascade"
    n_violations_before_trip: int
    worst_overload_pct_before_trip: float


@dataclass
class CascadeResult:
    steps: list[CascadeStep] = field(default_factory=list)
    ended_in_blackout: bool = False
    final_isolated_bus_count: int = 0


def _network_without_lines(net, exclude_line_ids: set[str]):
    from ..models.network import PowerNetwork
    new_net = PowerNetwork()
    for bus in net.buses.values():
        new_net.add_bus(bus)
    for lid, line in net.lines.items():
        if lid not in exclude_line_ids:
            new_net.add_line(line)
    return new_net


def run_cascading_failure(
    net, injections: dict, slack_bus: str, initial_line_id: str,
    trip_threshold_pct: float = 20.0, max_iterations: int = 20,
) -> CascadeResult:
    result = CascadeResult()
    tripped_lines: list[str] = [initial_line_id]
    result.steps.append(CascadeStep(initial_line_id, "initial", 0, 0.0))

    for _ in range(max_iterations):
        current_net = _network_without_lines(net, set(tripped_lines))

        if not current_net.is_connected():
            import networkx as nx
            components = sorted(nx.connected_components(current_net.graph), key=len, reverse=True)
            result.ended_in_blackout = True
            result.final_isolated_bus_count = sum(len(c) for c in components[1:])
            return result

        try:
            flow_result = run_dc_power_flow(current_net, injections, slack_bus)
        except Exception:
            result.ended_in_blackout = True
            return result

        violations = check_congestion(flow_result.line_flows_mw, current_net)
        over_threshold = [v for v in violations if v.overload_pct > trip_threshold_pct]

        if not over_threshold:
            return result  # cascade stabilized, no further trips needed

        worst = max(over_threshold, key=lambda v: v.overload_pct)
        result.steps.append(CascadeStep(
            tripped_line_id=worst.line_id, reason="overload_cascade",
            n_violations_before_trip=len(violations),
            worst_overload_pct_before_trip=worst.overload_pct,
        ))
        tripped_lines.append(worst.line_id)

    return result  # hit max_iterations — reported as-is, not silently truncated
