"""
run_dc_power_flow_demo.py
============================
Level 3: DC power flow on the CREDIBLE (fully-connected) Estonia
network, built exactly as requested — "leave it in a credible way,
that's it" — with every assumption stated plainly.

Injection assumptions (ALL explicit, none hidden):
  - Total generation = 696 MW, the REAL 2019 average hourly domestic
    generation. Placed ONLY at the 330 kV buses (Estonia's backbone —
    the real, general pattern for where large plants like Narva/Balti
    connect), split EQUALLY among them (no real per-plant data exists
    at bus level, so equal split is the simplest stated assumption,
    not a calibrated allocation).
  - Total demand = 940 MW, the REAL 2019 average hourly demand, split
    EQUALLY across ALL 155 buses (a uniform-per-substation assumption —
    real demand would concentrate near population centres like
    Tallinn/Tartu, but no real per-substation load data exists, so this
    is the simplest honest default, not a claim of accuracy).
  - Slack bus: Kiisa (a real 330 kV hub near Tallinn, one of the most
    connected nodes in the reconstructed network).
"""

from pathlib import Path
import pandas as pd

from A_engine.models.network import PowerNetwork, Bus, Line
from A_engine.power_flow.dc_power_flow import run_dc_power_flow

ROOT = Path(__file__).parent
REAL_AVG_GENERATION_MW = 696.2
REAL_AVG_DEMAND_MW = 939.6


def build_credible_network() -> PowerNetwork:
    out_dir = ROOT / "B_data" / "processed"
    substations = pd.read_csv(out_dir / "estonia_substations_CREDIBLE.csv")
    adjacencies = pd.read_csv(out_dir / "estonia_substation_adjacencies_CREDIBLE.csv")

    net = PowerNetwork()
    for _, row in substations.iterrows():
        net.add_bus(Bus(id=row["id"], name=row["name"], voltage_kv=row["voltage_kv"],
                         latitude=row["latitude"], longitude=row["longitude"]))
    for _, row in adjacencies.iterrows():
        net.add_line(Line(id=f"{row['from_bus']}__{row['to_bus']}",
                           from_bus_id=row["from_bus"], to_bus_id=row["to_bus"],
                           voltage_kv=row["voltage_kv"], length_km=row["path_length_km"]))
    return net


def main():
    net = build_credible_network()
    print(f"Network: {net.summary()}\n")

    buses_330kv = [b.id for b in net.buses.values() if b.voltage_kv == 330.0]
    generation_per_bus = REAL_AVG_GENERATION_MW / len(buses_330kv)
    demand_per_bus = REAL_AVG_DEMAND_MW / len(net.buses)

    injections = {b: -demand_per_bus for b in net.buses}
    for b in buses_330kv:
        injections[b] += generation_per_bus

    slack_candidates = [b.id for b in net.buses.values() if b.name == "Kiisa alajaam"]
    slack_bus = slack_candidates[0] if slack_candidates else buses_330kv[0]
    print(f"Slack bus: {net.buses[slack_bus].name} ({slack_bus})")

    # Slack absorbs the imbalance (generation 696 MW < demand 940 MW —
    # the missing 244 MW represents real 2019 net imports, which this
    # simplified single-country DC power flow doesn't model as a
    # separate injection — it flows through the slack bus instead,
    # a standard simplification, stated plainly).
    total_injection = sum(injections.values())
    injections[slack_bus] -= total_injection
    print(f"Imbalance absorbed by slack (represents net imports in this simplified model): {-total_injection:.1f} MW\n")

    result = run_dc_power_flow(net, injections, slack_bus)

    flows = pd.Series(result.line_flows_mw).abs().sort_values(ascending=False)
    print("=== Top 10 most heavily loaded lines (credible DC power flow) ===")
    for line_id, flow in flows.head(10).items():
        line = net.lines[line_id]
        from_name = net.buses[line.from_bus_id].name
        to_name = net.buses[line.to_bus_id].name
        tag = " [SYNTHETIC]" if line.length_km and line.length_km < 0.15 else ""
        print(f"  {from_name} <-> {to_name}: {flow:.1f} MW{tag}")

    print(
        "\nInterpretation: this ranks which lines carry the most power under "
        "the stated (uniform demand, backbone-only generation) assumptions — "
        "useful to see WHICH PART of the reconstructed network is structurally "
        "important, but the actual MW numbers are illustrative, not a real "
        "loading study. A genuine one needs real per-substation demand data "
        "and real line reactances, neither of which exist for this project yet."
    )


if __name__ == "__main__":
    main()
