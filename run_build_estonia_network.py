"""
run_build_estonia_network.py
==============================
Phase 37: builds the real PowerNetwork object (A_engine/models/network.py)
from the REAL, OSM-derived, graph-reconstructed Estonian transmission
topology (ingest_osm_network.py output).

This is REAL data (with the documented caveats: OSM crowdsourced,
~3km snap tolerance, simple centroid for polygon substations, DERIVED
not official-Elering topology — see docs/network_data_findings.md) —
the first time this project has a genuine Level 3 network, not a toy
3-bus example.
"""

from pathlib import Path
import pandas as pd

from A_engine.models.network import PowerNetwork, Bus, Line

ROOT = Path(__file__).parent


def build_estonia_network() -> PowerNetwork:
    out_dir = ROOT / "B_data" / "processed"
    substations = pd.read_csv(out_dir / "estonia_substations_110kv_plus.csv")
    adjacencies = pd.read_csv(out_dir / "estonia_substation_adjacencies.csv")

    net = PowerNetwork()
    for _, row in substations.iterrows():
        net.add_bus(Bus(
            id=row["id"], name=row["name"], voltage_kv=row["voltage_kv"],
            latitude=row["latitude"], longitude=row["longitude"],
        ))

    skipped = 0
    for _, row in adjacencies.iterrows():
        if row["from_bus"] not in net.buses or row["to_bus"] not in net.buses:
            skipped += 1  # references an unmatched substation — see ingest script output
            continue
        net.add_line(Line(
            id=f"{row['from_bus']}__{row['to_bus']}",
            from_bus_id=row["from_bus"], to_bus_id=row["to_bus"],
            voltage_kv=row["voltage_kv"], length_km=row["path_length_km"],
        ))
    if skipped:
        print(f"NOTE: skipped {skipped} adjacency record(s) referencing an unmatched substation")

    return net


def main():
    net = build_estonia_network()
    summary = net.summary()
    print("=== Estonia transmission network (REAL, OSM-derived) ===\n")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    if not summary["is_connected"]:
        import networkx as nx
        components = list(nx.connected_components(net.graph))
        components.sort(key=len, reverse=True)
        print(f"\nNetwork is NOT fully connected: {len(components)} separate components.")
        print(f"Largest component: {len(components[0])} buses ({100*len(components[0])/summary['n_buses']:.1f}% of all buses)")
        print("Smaller components (likely islands/peninsulas with sparser OSM line coverage, or genuinely radial spurs):")
        for comp in components[1:6]:
            names = [net.buses[b].name for b in comp]
            print(f"  {names}")
    else:
        print("\nNetwork IS fully connected — every substation reachable from every other.")


if __name__ == "__main__":
    main()
