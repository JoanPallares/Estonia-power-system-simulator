"""
ingest_osm_network_credible.py
================================
A DELIBERATELY LOOSER reconstruction of the Estonia network, built at
the project owner's explicit request: "assume what works best, connect
what needs connecting, this is a simulation exercise, not a precision
GIS project."

*** THIS IS NOT THE SAME AS THE REAL-DATA VERSION ***
ingest_osm_network.py (the original, strict version) stays untouched —
that's the honestly-fragmented, real-data-only reconstruction. THIS
script produces a SEPARATE, CREDIBLE-LOOKING network for simulation
purposes, with two explicit, documented relaxations:

  1. Lines with NO voltage tag are ASSUMED to be 110 kV (checked first:
     only 8/129 of these are confirmed Elering-operated, so this is a
     genuine assumption, not a well-supported inference — stated
     plainly, not disguised as a finding).
  2. Substation-to-graph snap tolerance raised from 3 km to 15 km, to
     bridge real gaps in OSM's line coverage.

Every bus/line produced by THIS script is tagged data_quality="assumed"
in its output files — never mixed silently with the real-only version.
"""

from pathlib import Path
import pandas as pd

from ingest_osm_network import (
    load_substations, build_segment_graph, snap_substations_to_graph,
    find_substation_adjacencies, parse_voltage_kv, geometry_centroid, haversine_km,
)
import json

ROOT = Path(__file__).parent
CREDIBLE_SNAP_TOLERANCE_KM = 15.0
ASSUMED_VOLTAGE_KV_FOR_UNTAGGED = 110.0


def load_line_segments_credible(path: Path, min_kv: float = 110.0) -> pd.DataFrame:
    """Same as ingest_osm_network.load_line_segments, EXCEPT lines with
    no voltage tag are kept and ASSUMED to be min_kv (110 kV), instead
    of being dropped."""
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)

    rows = []
    n_assumed = 0
    for feat in gj["features"]:
        props = feat["properties"]
        kv = parse_voltage_kv(props.get("tags.voltage"))
        assumed = False
        if kv is None:
            kv = ASSUMED_VOLTAGE_KV_FOR_UNTAGGED
            assumed = True
        elif kv < min_kv:
            continue

        coords = feat["geometry"]["coordinates"]
        if feat["geometry"]["type"] != "LineString" or len(coords) < 2:
            continue
        (lon_start, lat_start), (lon_end, lat_end) = coords[0], coords[-1]
        length_km = sum(
            haversine_km(coords[i][1], coords[i][0], coords[i + 1][1], coords[i + 1][0])
            for i in range(len(coords) - 1)
        )
        if assumed:
            n_assumed += 1
        rows.append({
            "id": f"line_{props['id']}",
            "name": props.get("tags.name") or f"Line {props['id']}",
            "voltage_kv": kv,
            "voltage_assumed": assumed,
            "lat_start": round(lat_start, 5), "lon_start": round(lon_start, 5),
            "lat_end": round(lat_end, 5), "lon_end": round(lon_end, 5),
            "length_km": round(length_km, 2),
        })
    print(f"Line segments included with ASSUMED voltage ({ASSUMED_VOLTAGE_KV_FOR_UNTAGGED} kV): {n_assumed}")
    return pd.DataFrame(rows)


def connect_remaining_components(substations: pd.DataFrame, adjacencies: list[dict]) -> list[dict]:
    """
    FINAL step, done at the project owner's explicit request ("if it
    needs extra connections to look credible, connect it — this is a
    simulation exercise, not a precision GIS project"):

    Repeatedly finds the two nearest buses in different components (by
    real geographic distance) and adds a SYNTHETIC edge between them,
    until the whole network is one connected component. Every such
    edge is tagged connection_type="synthetic_nearest_neighbor" so it
    is always distinguishable from a real (or assumed-voltage-but-real-
    geometry) OSM line — this is a common, legitimate technique for
    completing synthetic/illustrative network models, but it is NOT
    evidence of a real transmission line at that location.
    """
    import networkx as nx

    g = nx.Graph()
    g.add_nodes_from(substations["id"])
    for a in adjacencies:
        g.add_edge(a["from_bus"], a["to_bus"])

    sub_indexed = substations.set_index("id")
    synthetic_count = 0

    while True:
        components = list(nx.connected_components(g))
        if len(components) <= 1:
            break

        components.sort(key=len, reverse=True)
        main_component = components[0]
        best_pair, best_dist = None, float("inf")

        for other_component in components[1:]:
            for a_id in main_component:
                a = sub_indexed.loc[a_id]
                for b_id in other_component:
                    b = sub_indexed.loc[b_id]
                    d = haversine_km(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
                    if d < best_dist:
                        best_dist, best_pair = d, (a_id, b_id)

        g.add_edge(best_pair[0], best_pair[1])
        adjacencies.append({
            "from_bus": best_pair[0], "to_bus": best_pair[1],
            "path_length_km": round(best_dist, 2),
            "voltage_kv": 110.0,
            "connection_type": "synthetic_nearest_neighbor",
        })
        synthetic_count += 1

    print(f"Added {synthetic_count} synthetic nearest-neighbor connections to fully connect the network")
    for a in adjacencies:
        a.setdefault("connection_type", "osm_derived")
    return adjacencies


def main():
    osm_dir = ROOT / "B_data" / "raw" / "osm"
    substations = load_substations(osm_dir / "estonia_substation.geojson")
    segments = load_line_segments_credible(osm_dir / "estonia_line.geojson")

    print(f"Substations >=110kV (deduplicated): {len(substations)}")
    print(f"Line segments (real + assumed-voltage): {len(segments)}")

    graph = build_segment_graph(segments)
    sub_to_node = snap_substations_to_graph(substations, graph, CREDIBLE_SNAP_TOLERANCE_KM)
    print(f"Substations matched within {CREDIBLE_SNAP_TOLERANCE_KM} km: {len(sub_to_node)} / {len(substations)}")

    adjacencies = find_substation_adjacencies(graph, sub_to_node)
    print(f"OSM-derived substation-to-substation adjacencies: {len(adjacencies)}")

    # Any substation that never matched the line graph at all still needs
    # to be included as an isolated node before the connectivity fix below.
    all_ids = set(substations["id"])
    connected_ids = set()
    for a in adjacencies:
        connected_ids.add(a["from_bus"])
        connected_ids.add(a["to_bus"])
    isolated = all_ids - connected_ids
    if isolated:
        print(f"{len(isolated)} substations had zero OSM-derived connections at all")

    adjacencies = connect_remaining_components(substations, adjacencies)

    substations = substations.copy()
    substations["data_quality"] = "assumed_network_credible_reconstruction"

    out_dir = ROOT / "B_data" / "processed"
    substations.to_csv(out_dir / "estonia_substations_CREDIBLE.csv", index=False)
    pd.DataFrame(adjacencies).to_csv(out_dir / "estonia_substation_adjacencies_CREDIBLE.csv", index=False)

    n_synthetic = sum(1 for a in adjacencies if a["connection_type"] == "synthetic_nearest_neighbor")
    print(f"\nFinal network: {len(substations)} buses, {len(adjacencies)} lines "
          f"({len(adjacencies) - n_synthetic} OSM-derived, {n_synthetic} synthetic connectivity fixes)")
    print(f"Written to {out_dir} (files suffixed _CREDIBLE)")


if __name__ == "__main__":
    main()
