"""
Tests for A_engine/models/dc_power_flow.py and the synthetic
connectivity-completion step in ingest_osm_network_credible.py.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.network import PowerNetwork, Bus, Line
from A_engine.power_flow.dc_power_flow import line_reactance_pu, run_dc_power_flow


def build_toy_triangle() -> PowerNetwork:
    """3 buses, fully connected (a simple loop) — the smallest network
    that meaningfully exercises DC power flow."""
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="A", voltage_kv=110))
    net.add_bus(Bus(id="B", name="B", voltage_kv=110))
    net.add_bus(Bus(id="C", name="C", voltage_kv=110))
    net.add_line(Line(id="AB", from_bus_id="A", to_bus_id="B", voltage_kv=110, length_km=10))
    net.add_line(Line(id="BC", from_bus_id="B", to_bus_id="C", voltage_kv=110, length_km=10))
    net.add_line(Line(id="CA", from_bus_id="C", to_bus_id="A", voltage_kv=110, length_km=10))
    return net


def test_line_reactance_pu_positive():
    x = line_reactance_pu(110.0, 50.0)
    assert x > 0


def test_line_reactance_scales_with_length():
    x_short = line_reactance_pu(110.0, 10.0)
    x_long = line_reactance_pu(110.0, 100.0)
    assert x_long > x_short


def test_dc_power_flow_requires_connected_network():
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="A", voltage_kv=110))
    net.add_bus(Bus(id="B", name="B", voltage_kv=110))  # disconnected
    with pytest.raises(ValueError):
        run_dc_power_flow(net, {"A": 100, "B": -100}, slack_bus="A")


def test_dc_power_flow_balanced_injection_zero_net_flow_symmetric_network():
    net = build_toy_triangle()
    # Symmetric network, symmetric injection -> by symmetry flows should be equal magnitude
    result = run_dc_power_flow(net, {"A": 100, "B": -50, "C": -50}, slack_bus="A")
    assert set(result.line_flows_mw.keys()) == {"AB", "BC", "CA"}
    # BC should carry zero flow by symmetry (B and C are electrically identical relative to slack A)
    assert abs(result.line_flows_mw["BC"]) < 1e-6


def test_dc_power_flow_no_injection_no_flow():
    net = build_toy_triangle()
    result = run_dc_power_flow(net, {"A": 0, "B": 0, "C": 0}, slack_bus="A")
    for flow in result.line_flows_mw.values():
        assert abs(flow) < 1e-9


def test_dc_power_flow_slack_bus_angle_is_zero():
    net = build_toy_triangle()
    result = run_dc_power_flow(net, {"A": 50, "B": -50, "C": 0}, slack_bus="A")
    assert result.bus_angles_rad["A"] == 0.0
