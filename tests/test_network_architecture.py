"""
Tests for Phase 37's generic network architecture. Uses a tiny FICTIONAL
example network (3 buses) — NOT real Estonian topology, which this
project does not have (see docs/network_data_findings.md).
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from A_engine.models.network import (
    PowerNetwork, Bus, Generator, Load, Line, Transformer, NetworkInterconnection,
)


def build_toy_network() -> PowerNetwork:
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="Bus A", voltage_kv=330))
    net.add_bus(Bus(id="B", name="Bus B", voltage_kv=330))
    net.add_bus(Bus(id="C", name="Bus C", voltage_kv=110))
    net.add_line(Line(id="L1", from_bus_id="A", to_bus_id="B", voltage_kv=330, thermal_limit_mw=500))
    net.add_transformer(Transformer(id="T1", bus_id_primary="B", bus_id_secondary="C", rating_mva=200))
    net.add_generator(Generator(id="G1", bus_id="A", technology="oil_shale", capacity_mw=1000))
    net.add_load(Load(id="D1", bus_id="C", peak_demand_mw=300))
    net.add_interconnection(NetworkInterconnection(id="IC1", bus_id="A", neighbouring_country="Finland", import_capacity_mw=1000))
    return net


def test_toy_network_summary():
    net = build_toy_network()
    summary = net.summary()
    assert summary["n_buses"] == 3
    assert summary["n_lines"] == 1
    assert summary["n_transformers"] == 1
    assert summary["is_connected"] is True


def test_generator_references_unknown_bus_raises():
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="Bus A"))
    with pytest.raises(KeyError):
        net.add_generator(Generator(id="G1", bus_id="Z", technology="wind"))


def test_disconnected_network_detected():
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="Bus A"))
    net.add_bus(Bus(id="B", name="Bus B"))  # no line connecting them
    assert net.is_connected() is False


def test_line_references_unknown_bus_raises():
    net = PowerNetwork()
    net.add_bus(Bus(id="A", name="Bus A"))
    with pytest.raises(KeyError):
        net.add_line(Line(id="L1", from_bus_id="A", to_bus_id="Z"))
