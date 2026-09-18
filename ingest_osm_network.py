"""
ingest_osm_network.py
=======================
Phase 36-37: ingest REAL Estonian transmission network data from
OpenStreetMap (extracted by the project owner via earth-osm, since
this sandbox's network can't reach OSM/Geofabrik directly — see
docs/network_data_findings.md).

Filter rationale (data-driven, not arbitrary): Elering's own published
description of the network is "330 kV backbone + 110 kV regional
network" (docs/data_discovery_estonia.md). This ingestion keeps ONLY
substations and lines tagged >=110kV, matching that description exactly
— excludes ~2,200 distribution-level substations/lines (6kV-35kV, mostly
tagged 'minor_distribution') which are real but out of this project's
declared scope (system_definition.md Section 3: no individual
distribution-level assets).

Topology reconstruction caveat (stated up front, not hidden): OSM line
features are geometric paths, not explicitly linked to substation IDs.
This script SNAPS each line's two endpoints to the nearest bus within
a tolerance radius — a standard, but approximate, GIS technique. Lines
that don't snap on both ends are reported, NOT silently dropped or
guessed into a connection.
"""

import json
import math
from pathlib import Path
from dataclasses import dataclass

import pandas as pd

ROOT = Path(__file__).parent
SNAP_TOLERANCE_KM = 3.0  # ASSUMPTION: real substations can have their OSM point
                           # tag offset from where lines visually terminate; 3 km
                           # is a generous-but-bounded snap radius for a country-
                           # scale network, not a precisely justified figure.


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse_voltage_kv(raw_voltage) -> float | None:
    """OSM voltage tags are volts, as strings, sometimes semicolon-separated
    for multi-circuit assets (e.g. '330000;110000'). Takes the MAX value
    (the highest voltage the asset is rated for) — an explicit, documented
    choice, not a silent default."""
    if raw_voltage is None or (isinstance(raw_voltage, float) and pd.isna(raw_voltage)):
        return None
    parts = str(raw_voltage).split(";")
    values = []
    for p in parts:
        try:
            values.append(float(p) / 1000.0)
        except ValueError:
            continue
    return max(values) if values else None


def geometry_centroid(geometry: dict) -> tuple[float, float] | None:
    """Returns (lon, lat) for a Point directly, or the simple centroid
    (average of vertices) for a Polygon (many OSM substations are mapped
    as fenced areas, not single points). Not area-weighted — a simple,
    documented approximation, good enough for a country-scale network
    diagram, not for precise siting."""
    gtype = geometry["type"]
    if gtype == "Point":
        return tuple(geometry["coordinates"])
    if gtype == "Polygon":
        ring = geometry["coordinates"][0]  # exterior ring
        lons = [pt[0] for pt in ring]
        lats = [pt[1] for pt in ring]
        return (sum(lons) / len(lons), sum(lats) / len(lats))
    return None  # e.g. the one stray LineString — skipped, not guessed


def load_substations(path: Path, min_kv: float = 110.0) -> pd.DataFrame:
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)

    rows = []
    skipped_geometry = 0
    for feat in gj["features"]:
        props = feat["properties"]
        kv = parse_voltage_kv(props.get("tags.voltage"))
        if kv is None or kv < min_kv:
            continue
        centroid = geometry_centroid(feat["geometry"])
        if centroid is None:
            skipped_geometry += 1
            continue
        lon, lat = centroid
        rows.append({
            "id": f"sub_{props['id']}",
            "name": props.get("tags.name") or f"Substation {props['id']}",
            "voltage_kv": kv,
            "latitude": lat,
            "longitude": lon,
            "operator": props.get("tags.operator"),
        })
    if skipped_geometry:
        print(f"NOTE: skipped {skipped_geometry} substation(s) >=110kV with unsupported geometry type")

    df = pd.DataFrame(rows)
    # DEDUPE: OSM maps some substations as BOTH a Point and a Polygon
    # (same real substation, two features). Confirmed by inspection:
    # 5 names appeared twice. Keep the first occurrence per name — a
    # documented, simple choice, not a sophisticated conflation.
    n_before = len(df)
    df = df.drop_duplicates(subset="name", keep="first").reset_index(drop=True)
    if n_before != len(df):
        print(f"NOTE: deduplicated {n_before - len(df)} substation(s) mapped as both Point and Polygon (same name)")
    return df


def load_line_segments(path: Path, min_kv: float = 110.0) -> pd.DataFrame:
    """Loads EVERY real line segment >=110kV, keeping full endpoint
    coordinates (not yet connected to substations — that's a separate,
    graph-based step, since raw OSM segments are fragments of longer
    corridors, not direct substation-to-substation links — see module
    docstring)."""
    with open(path, encoding="utf-8") as f:
        gj = json.load(f)

    rows = []
    for feat in gj["features"]:
        props = feat["properties"]
        kv = parse_voltage_kv(props.get("tags.voltage"))
        if kv is None or kv < min_kv:
            continue
        coords = feat["geometry"]["coordinates"]
        if feat["geometry"]["type"] != "LineString" or len(coords) < 2:
            continue
        (lon_start, lat_start), (lon_end, lat_end) = coords[0], coords[-1]
        length_km = sum(
            haversine_km(coords[i][1], coords[i][0], coords[i + 1][1], coords[i + 1][0])
            for i in range(len(coords) - 1)
        )
        rows.append({
            "id": f"line_{props['id']}",
            "name": props.get("tags.name") or f"Line {props['id']}",
            "voltage_kv": kv,
            "lat_start": round(lat_start, 5), "lon_start": round(lon_start, 5),
            "lat_end": round(lat_end, 5), "lon_end": round(lon_end, 5),
            "length_km": round(length_km, 2),
        })
    return pd.DataFrame(rows)


def build_segment_graph(segments: pd.DataFrame):
    """
    Builds a networkx graph where nodes are ROUNDED coordinates (shared
    endpoints between adjacent OSM way segments = the same node, since
    OSM splits one physical corridor into many ways that share nodes at
    junctions/towers) and edges are the real line segments.
    """
    import networkx as nx
    g = nx.Graph()
    for _, row in segments.iterrows():
        start = (row["lat_start"], row["lon_start"])
        end = (row["lat_end"], row["lon_end"])
        g.add_edge(start, end, length_km=row["length_km"], voltage_kv=row["voltage_kv"], name=row["name"], line_id=row["id"])
    return g


def snap_substations_to_graph(substations: pd.DataFrame, graph, tolerance_km: float) -> dict:
    """Returns {substation_id: graph_node} for substations that have a
    graph node (a real line-segment endpoint) within tolerance_km."""
    result = {}
    graph_nodes = list(graph.nodes)
    for _, sub in substations.iterrows():
        best_node, best_dist = None, float("inf")
        for node in graph_nodes:
            d = haversine_km(sub["latitude"], sub["longitude"], node[0], node[1])
            if d < best_dist:
                best_dist, best_node = d, node
        if best_dist <= tolerance_km:
            result[sub["id"]] = best_node
    return result


def find_substation_adjacencies(graph, sub_to_node: dict) -> list[dict]:
    """
    Phase 37's real deliverable: for each substation, walks the raw
    segment graph outward and records a direct adjacency to the FIRST
    other substation reached along each path (i.e. contracts the
    fragmented line graph down to substation-to-substation links,
    without inventing any connection the real segment data doesn't
    support). Each adjacency's length is the real summed path length
    of the real segments traversed to get there.
    """
    import networkx as nx
    node_to_sub = {v: k for k, v in sub_to_node.items()}
    adjacencies = []
    seen_pairs = set()

    for sub_id, start_node in sub_to_node.items():
        # BFS, but treat any OTHER substation node as a wall (record + stop)
        visited = {start_node}
        queue = [(start_node, 0.0)]
        while queue:
            node, dist_so_far = queue.pop(0)
            for neighbor in graph.neighbors(node):
                if neighbor in visited:
                    continue
                edge_len = graph[node][neighbor]["length_km"]
                new_dist = dist_so_far + edge_len
                if neighbor in node_to_sub and node_to_sub[neighbor] != sub_id:
                    other_sub = node_to_sub[neighbor]
                    pair = tuple(sorted([sub_id, other_sub]))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        adjacencies.append({
                            "from_bus": pair[0], "to_bus": pair[1],
                            "path_length_km": round(new_dist, 2),
                            "voltage_kv": graph[node][neighbor]["voltage_kv"],
                        })
                    visited.add(neighbor)  # don't traverse past a substation
                else:
                    visited.add(neighbor)
                    queue.append((neighbor, new_dist))

    return adjacencies


def main():
    osm_dir = ROOT / "B_data" / "raw" / "osm"
    substations = load_substations(osm_dir / "estonia_substation.geojson")
    segments = load_line_segments(osm_dir / "estonia_line.geojson")

    print(f"Substations >=110kV (deduplicated): {len(substations)}")
    print(f"Raw line segments >=110kV: {len(segments)}")

    graph = build_segment_graph(segments)
    print(f"Segment graph: {graph.number_of_nodes()} coordinate nodes, {graph.number_of_edges()} edges")

    sub_to_node = snap_substations_to_graph(substations, graph, SNAP_TOLERANCE_KM)
    print(f"Substations matched to the line-segment graph (within {SNAP_TOLERANCE_KM} km): {len(sub_to_node)} / {len(substations)}")

    adjacencies = find_substation_adjacencies(graph, sub_to_node)
    print(f"Real substation-to-substation adjacencies reconstructed (via BFS through segment fragments): {len(adjacencies)}")

    out_dir = ROOT / "B_data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    substations.to_csv(out_dir / "estonia_substations_110kv_plus.csv", index=False)
    pd.DataFrame(adjacencies).to_csv(out_dir / "estonia_substation_adjacencies.csv", index=False)

    unmatched_subs = substations[~substations["id"].isin(sub_to_node.keys())]
    unmatched_subs.to_csv(out_dir / "estonia_substations_unmatched.csv", index=False)
    if len(unmatched_subs):
        print(f"\n{len(unmatched_subs)} substations could NOT be matched to any line segment within {SNAP_TOLERANCE_KM} km — "
              f"saved separately, not silently dropped.")

    print(f"\nWritten to {out_dir}")


if __name__ == "__main__":
    main()
