"""
run_grid_simulation.py
========================
Phase 54: canonical Level 3 entry point — "python run_grid_simulation.py"
-> network + power flow.

Uses the CREDIBLE (fully-connected) network — DC power flow requires a
single connected component, and the real-only reconstruction is
honestly fragmented (see docs/limitations.md). For N-1 / cascading
failure specifically, see run_n_minus_1_analysis.py /
run_cascading_failure_demo.py — kept separate, not folded in here, so
each output stays readable.
"""

from run_dc_power_flow_demo import build_credible_network, REAL_AVG_GENERATION_MW, REAL_AVG_DEMAND_MW
from A_engine.power_flow.dc_power_flow import run_dc_power_flow, check_congestion


def main():
    net = build_credible_network()
    print(f"\n=== Grid (credible, fully-connected network): {net.summary()} ===\n")

    buses_330 = [b.id for b in net.buses.values() if b.voltage_kv == 330]
    gen_per_bus = REAL_AVG_GENERATION_MW / len(buses_330)
    dem_per_bus = REAL_AVG_DEMAND_MW / len(net.buses)
    injections = {b: -dem_per_bus for b in net.buses}
    for b in buses_330:
        injections[b] += gen_per_bus
    slack_candidates = [b.id for b in net.buses.values() if b.name == "Kiisa alajaam"]
    slack = slack_candidates[0] if slack_candidates else buses_330[0]
    injections[slack] -= sum(injections.values())

    result = run_dc_power_flow(net, injections, slack)
    violations = check_congestion(result.line_flows_mw, net)
    print(f"Slack bus: {net.buses[slack].name}")
    print(f"Congestion violations: {len(violations)} / {len(net.lines)} lines\n")
    for v in violations[:10]:
        line = net.lines[v.line_id]
        print(f"  {net.buses[line.from_bus_id].name} <-> {net.buses[line.to_bus_id].name}: "
              f"{v.flow_mw:.1f} MW (limit {v.limit_mw}, overload {v.overload_pct}%)")

    print("\nFor N-1 contingency ranking: python run_n_minus_1_analysis.py")
    print("For cascading failure simulation: python run_cascading_failure_demo.py")


if __name__ == "__main__":
    main()
