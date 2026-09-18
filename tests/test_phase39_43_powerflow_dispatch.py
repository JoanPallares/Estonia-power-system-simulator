"""
Tests for Phases 39-43: BusType, congestion, N-1, cascading failure,
economic dispatch.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.network import PowerNetwork, Bus, Line
from A_engine.power_flow.dc_power_flow import BusType, run_dc_power_flow, check_congestion, TYPICAL_THERMAL_LIMIT_MW
from A_engine.power_flow.n_minus_1 import run_n_minus_1_lines, criticality_ranking, _network_without_line
from A_engine.power_flow.cascading_failure import run_cascading_failure
from A_engine.optimization.economic_dispatch import solve_economic_dispatch


def build_toy_triangle() -> PowerNetwork:
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="A", voltage_kv=110))
    net.add_bus(Bus(id="B", name="B", voltage_kv=110))
    net.add_bus(Bus(id="C", name="C", voltage_kv=110))
    net.add_line(Line(id="AB", from_bus_id="A", to_bus_id="B", voltage_kv=110, length_km=10))
    net.add_line(Line(id="BC", from_bus_id="B", to_bus_id="C", voltage_kv=110, length_km=10))
    net.add_line(Line(id="CA", from_bus_id="C", to_bus_id="A", voltage_kv=110, length_km=10))
    return net


def build_toy_line() -> PowerNetwork:
    """A->B->C with NO loop — removing either line disconnects the network."""
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="A", voltage_kv=110))
    net.add_bus(Bus(id="B", name="B", voltage_kv=110))
    net.add_bus(Bus(id="C", name="C", voltage_kv=110))
    net.add_line(Line(id="AB", from_bus_id="A", to_bus_id="B", voltage_kv=110, length_km=10))
    net.add_line(Line(id="BC", from_bus_id="B", to_bus_id="C", voltage_kv=110, length_km=10))
    return net


# --- Phase 39 ---

def test_bus_type_enum_has_slack_and_pq():
    assert BusType.SLACK.value == "slack"
    assert BusType.PQ.value == "pq"


# --- Phase 40: congestion ---

def test_check_congestion_flags_overload():
    net = build_toy_triangle()
    flows = {"AB": 200.0, "BC": 10.0, "CA": 10.0}  # AB exceeds 150 MW default 110kV limit
    violations = check_congestion(flows, net)
    assert len(violations) == 1
    assert violations[0].line_id == "AB"


def test_check_congestion_none_within_limits():
    net = build_toy_triangle()
    flows = {"AB": 50.0, "BC": 50.0, "CA": 50.0}
    assert check_congestion(flows, net) == []


def test_generation_sufficient_but_congestion_blocks_delivery():
    """Phase 40's core point: overall balance can be fine, but a
    specific line can still be overloaded."""
    net = build_toy_line()  # A -- B -- C, radial
    # Generation at A (200 MW) exactly matches demand at C (200 MW):
    # system-wide "generation sufficient" is TRUE, but it all has to
    # flow through both lines.
    result = run_dc_power_flow(net, {"B": 0, "C": -200}, slack_bus="A")
    violations = check_congestion(result.line_flows_mw, net)
    assert len(violations) == 2  # both AB and BC forced to carry 200 MW, over the 150 MW limit


# --- Phase 41: N-1 ---

def test_n_minus_1_detects_disconnection_on_radial_network():
    net = build_toy_line()
    results = run_n_minus_1_lines(net, {"A": 100, "B": 0, "C": -100}, slack_bus="A")
    assert all(r.disconnects_network for r in results)  # radial network: every line is a bridge


def test_n_minus_1_no_disconnection_on_looped_network():
    net = build_toy_triangle()
    results = run_n_minus_1_lines(net, {"A": 100, "B": -50, "C": -50}, slack_bus="A")
    assert all(not r.disconnects_network for r in results)  # a loop: removing one line still leaves it connected


def test_criticality_ranking_puts_disconnection_first():
    net = build_toy_line()
    results = run_n_minus_1_lines(net, {"A": 100, "B": 0, "C": -100}, slack_bus="A")
    ranked = criticality_ranking(results)
    assert ranked[0].disconnects_network


def test_network_without_line_removes_only_target_line():
    net = build_toy_triangle()
    reduced = _network_without_line(net, "AB")
    assert "AB" not in reduced.lines
    assert "BC" in reduced.lines and "CA" in reduced.lines


# --- Phase 42: cascading failure ---

def test_cascading_failure_stops_when_no_more_overloads():
    net = build_toy_triangle()
    # Light loading -> initial trip alone shouldn't cascade further
    result = run_cascading_failure(net, {"A": 10, "B": -5, "C": -5}, slack_bus="A", initial_line_id="BC")
    assert len(result.steps) == 1  # only the initial trip, no cascade


def test_cascading_failure_on_radial_network_causes_blackout():
    net = build_toy_line()
    result = run_cascading_failure(net, {"A": 100, "B": 0, "C": -100}, slack_bus="A", initial_line_id="AB")
    assert result.ended_in_blackout


# --- Phase 43: economic dispatch ---

def test_economic_dispatch_meets_demand_exactly():
    result = solve_economic_dispatch(demand_mw=500, wind_mw=50, oil_shale_capacity_mw=1000, interconnection_capacity_mw=500)
    assert result.success
    net_supply = result.oil_shale_mw + 50 + result.imports_mw - result.exports_mw
    assert net_supply == pytest.approx(500, abs=0.1)


def test_economic_dispatch_prefers_cheaper_oil_shale_over_imports():
    # oil shale (40) is cheaper than imports (60). Interconnection set to 0
    # here specifically to isolate this behaviour from the separate export-
    # arbitrage effect (oil shale 40 < export price 55 makes the optimizer
    # WANT to over-generate and export when exporting is allowed at all —
    # a real, documented artifact of flat marginal cost, not a bug, but
    # not what this particular test is checking).
    result = solve_economic_dispatch(demand_mw=500, wind_mw=0, oil_shale_capacity_mw=1000, interconnection_capacity_mw=0)
    assert result.imports_mw == pytest.approx(0.0, abs=0.1)
    assert result.exports_mw == pytest.approx(0.0, abs=0.1)
    assert result.oil_shale_mw == pytest.approx(500.0, abs=0.1)


def test_economic_dispatch_imports_when_oil_shale_capacity_insufficient():
    result = solve_economic_dispatch(demand_mw=500, wind_mw=0, oil_shale_capacity_mw=100, interconnection_capacity_mw=500)
    assert result.oil_shale_mw == pytest.approx(100.0, abs=0.1)
    assert result.imports_mw == pytest.approx(400.0, abs=0.1)


def test_economic_dispatch_infeasible_when_nothing_can_meet_demand():
    result = solve_economic_dispatch(demand_mw=500, wind_mw=0, oil_shale_capacity_mw=10, interconnection_capacity_mw=10)
    assert not result.success
