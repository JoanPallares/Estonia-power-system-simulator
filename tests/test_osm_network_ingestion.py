"""
Tests for Phase 36-37: OSM network ingestion and real Estonia network build.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest_osm_network import parse_voltage_kv, geometry_centroid, haversine_km


def test_parse_voltage_kv_simple():
    assert parse_voltage_kv("110000") == 110.0


def test_parse_voltage_kv_semicolon_takes_max():
    assert parse_voltage_kv("330000;110000") == 330.0


def test_parse_voltage_kv_none_input():
    assert parse_voltage_kv(None) is None


def test_parse_voltage_kv_unparseable_returns_none():
    assert parse_voltage_kv("MV") is None


def test_geometry_centroid_point():
    geom = {"type": "Point", "coordinates": [25.0, 59.0]}
    assert geometry_centroid(geom) == (25.0, 59.0)


def test_geometry_centroid_polygon_averages_ring():
    geom = {"type": "Polygon", "coordinates": [[[24.0, 59.0], [26.0, 59.0], [26.0, 61.0], [24.0, 61.0]]]}
    lon, lat = geometry_centroid(geom)
    assert lon == pytest.approx(25.0)
    assert lat == pytest.approx(60.0)


def test_geometry_centroid_unsupported_type_returns_none():
    assert geometry_centroid({"type": "LineString", "coordinates": [[0, 0], [1, 1]]}) is None


def test_haversine_zero_distance_same_point():
    assert haversine_km(59.0, 25.0, 59.0, 25.0) == pytest.approx(0.0)


def test_haversine_known_distance_tallinn_tartu():
    # Tallinn (~59.437, 24.754) to Tartu (~58.378, 26.729) is ~185 km real-world
    d = haversine_km(59.437, 24.754, 58.378, 26.729)
    assert 150 < d < 220  # generous bound, sanity check not precision check


def test_build_estonia_network_from_real_processed_data():
    """Only runs if the OSM ingestion has already been executed — skips
    cleanly otherwise rather than failing on missing fixtures."""
    root = Path(__file__).parent.parent
    processed = root / "B_data" / "processed" / "estonia_substations_110kv_plus.csv"
    if not processed.exists():
        pytest.skip("Real OSM-derived network data not present — run ingest_osm_network.py first")

    sys.path.insert(0, str(root))
    from run_build_estonia_network import build_estonia_network

    net = build_estonia_network()
    summary = net.summary()
    assert summary["n_buses"] > 100  # real Estonia has ~150+ substations >=110kV
    assert summary["n_lines"] > 100
    # Voltage sanity: only 110/330 kV buses should be present (filter worked)
    voltages = {bus.voltage_kv for bus in net.buses.values()}
    assert voltages <= {110.0, 330.0}
