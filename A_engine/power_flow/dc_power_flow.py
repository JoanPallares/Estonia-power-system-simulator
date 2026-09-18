"""
dc_power_flow.py
==================
Level 3: a simple DC power flow, done "in a credible way" as requested.

*** LINE REACTANCE IS ASSUMED, NOT MEASURED ***
OSM gives geometry, not electrical parameters. This uses standard
textbook per-km reactance values for overhead transmission lines:
  - 110 kV: ~0.4 ohm/km (typical range 0.35-0.45)
  - 330 kV: ~0.3 ohm/km (typical range 0.28-0.32, larger conductors/bundling)
These are GENERIC ENGINEERING TEXTBOOK VALUES, not Estonia-specific
measurements — exactly like the generic wind/PV models in
renewable_physical.py. Combined with real (OSM-derived) line lengths,
they give a per-line reactance in ohms, then per-unit on a chosen base.

DC power flow assumptions (standard for this class of approximate
analysis, not unique to this project):
  - voltage magnitude = 1.0 pu everywhere
  - line resistance and losses ignored
  - reactive power ignored
  - one slack bus (largest generation/reference bus)
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import numpy as np


class BusType(str, Enum):
    """
    Phase 39 concept, made explicit in code (previously implicit).
    In a DC power flow there is no real distinction between PV and PQ
    buses (voltage magnitude is irrelevant to the DC approximation) —
    every non-slack bus behaves as a PQ bus: injection is specified,
    angle is solved for.
    """
    SLACK = "slack"   # angle fixed at 0, absorbs the system's power imbalance
    PQ = "pq"         # injection (P) specified, angle solved for


TYPICAL_REACTANCE_OHM_PER_KM = {
    110.0: 0.4,
    330.0: 0.3,
}

# Phase 40: typical thermal limits by voltage class — AGAIN generic
# textbook values (a single 110kV overhead circuit typically carries
# 100-200 MW, a 330kV circuit 400-800 MW, depending on conductor size),
# NOT measured Estonian line ratings (OSM gives geometry, not thermal
# ratings). Used to demonstrate the Section concept that "generation
# sufficient" does not imply "load supplied" if a specific line is
# congested, even when the SYSTEM-WIDE balance is fine.
TYPICAL_THERMAL_LIMIT_MW = {
    110.0: 150.0,
    330.0: 600.0,
}

BASE_MVA = 100.0
BASE_KV_DEFAULT = 110.0


@dataclass
class CongestionViolation:
    line_id: str
    flow_mw: float
    limit_mw: float
    overload_pct: float


def check_congestion(line_flows_mw: dict, net) -> list[CongestionViolation]:
    """Phase 40: flags every line whose flow exceeds its (assumed)
    thermal limit. A non-empty result, even when total generation >=
    total demand system-wide, is exactly the phenomenon this phase is
    about: transmission congestion preventing delivery despite
    sufficient generation."""
    violations = []
    for line_id, flow_mw in line_flows_mw.items():
        line = net.lines[line_id]
        limit = TYPICAL_THERMAL_LIMIT_MW.get(line.voltage_kv, TYPICAL_THERMAL_LIMIT_MW[110.0])
        if abs(flow_mw) > limit:
            violations.append(CongestionViolation(
                line_id=line_id, flow_mw=flow_mw, limit_mw=limit,
                overload_pct=round(100 * (abs(flow_mw) - limit) / limit, 1),
            ))
    return violations


@dataclass
class DCPowerFlowResult:
    bus_angles_rad: dict
    line_flows_mw: dict
    slack_bus: str


def line_reactance_pu(voltage_kv: float, length_km: float, base_mva: float = BASE_MVA) -> float:
    """Converts a line's physical length + assumed ohm/km to per-unit
    reactance on the given MVA base — standard power-systems formula:
    X_pu = X_ohm * base_MVA / (base_kV^2)."""
    ohm_per_km = TYPICAL_REACTANCE_OHM_PER_KM.get(voltage_kv, TYPICAL_REACTANCE_OHM_PER_KM[110.0])
    x_ohm = ohm_per_km * max(length_km, 0.1)  # floor to avoid divide-by-zero on ~0-length synthetic edges
    return x_ohm * base_mva / (voltage_kv ** 2)


def run_dc_power_flow(net, bus_injections_mw: dict, slack_bus: str) -> DCPowerFlowResult:
    """
    net: A_engine.models.network.PowerNetwork (must be fully connected —
         DC power flow needs one slack per connected component; this
         function assumes ONE component and raises otherwise).
    bus_injections_mw: {bus_id: net generation - demand, MW}. Must sum
         to ~0 for a real power-flow solution to exist (a single-slack
         DC power flow enforces this by not including the slack bus in
         the injection vector — its injection is solved for implicitly).
    """
    if not net.is_connected():
        raise ValueError("DC power flow requires a fully connected network — got a fragmented one.")

    buses = [b for b in net.buses if b != slack_bus]
    bus_index = {b: i for i, b in enumerate(buses)}
    n = len(buses)

    B = np.zeros((n, n))
    line_x_pu = {}

    for line in net.lines.values():
        x_pu = line_reactance_pu(line.voltage_kv or BASE_KV_DEFAULT, line.length_km or 1.0)
        line_x_pu[line.id] = x_pu
        b_val = 1.0 / x_pu

        i, j = line.from_bus_id, line.to_bus_id
        if i in bus_index:
            B[bus_index[i], bus_index[i]] += b_val
        if j in bus_index:
            B[bus_index[j], bus_index[j]] += b_val
        if i in bus_index and j in bus_index:
            B[bus_index[i], bus_index[j]] -= b_val
            B[bus_index[j], bus_index[i]] -= b_val

    P = np.array([bus_injections_mw.get(b, 0.0) / BASE_MVA for b in buses])

    theta = np.linalg.solve(B, P)  # DC power flow: P = B * theta

    bus_angles = {slack_bus: 0.0}
    for b, i in bus_index.items():
        bus_angles[b] = theta[i]

    line_flows_mw = {}
    for line in net.lines.values():
        x_pu = line_x_pu[line.id]
        theta_i = bus_angles.get(line.from_bus_id, 0.0)
        theta_j = bus_angles.get(line.to_bus_id, 0.0)
        flow_pu = (theta_i - theta_j) / x_pu
        line_flows_mw[line.id] = flow_pu * BASE_MVA

    return DCPowerFlowResult(bus_angles_rad=bus_angles, line_flows_mw=line_flows_mw, slack_bus=slack_bus)
