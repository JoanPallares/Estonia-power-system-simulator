"""
run_n_minus_1_analysis.py
============================
Phase 41: runs N-1 across all 286 lines of the credible Estonia network.
"""

from pathlib import Path
from A_engine.power_flow.n_minus_1 import run_n_minus_1_lines, criticality_ranking
from run_dc_power_flow_demo import build_credible_network, REAL_AVG_GENERATION_MW, REAL_AVG_DEMAND_MW

ROOT = Path(__file__).parent


def main():
    net = build_credible_network()
    buses_330 = [b.id for b in net.buses.values() if b.voltage_kv == 330]
    gen_per_bus = REAL_AVG_GENERATION_MW / len(buses_330)
    dem_per_bus = REAL_AVG_DEMAND_MW / len(net.buses)
    injections = {b: -dem_per_bus for b in net.buses}
    for b in buses_330:
        injections[b] += gen_per_bus
    slack = [b.id for b in net.buses.values() if b.name == "Kiisa alajaam"][0]
    injections[slack] -= sum(injections.values())

    print(f"Running N-1 across {len(net.lines)} lines...")
    results = run_n_minus_1_lines(net, injections, slack)
    ranked = criticality_ranking(results)

    disconnecting = [r for r in ranked if r.disconnects_network]
    print(f"\nLines whose removal DISCONNECTS the network (real load loss): {len(disconnecting)}")
    print("=== Top 10 most critical (worst first) ===")
    for r in ranked[:10]:
        from_name = net.buses[r.from_bus].name
        to_name = net.buses[r.to_bus].name
        tag = " [synthetic]" if r.is_synthetic else ""
        if r.disconnects_network:
            print(f"  {from_name} <-> {to_name}{tag}: DISCONNECTS network, isolates {r.isolated_bus_count} bus(es)")
        elif r.worst_overload_pct == -2:
            print(f"  {from_name} <-> {to_name}{tag}: numerical failure on this contingency")
        else:
            print(f"  {from_name} <-> {to_name}{tag}: {r.new_violations_count} new violation(s), worst overload {r.worst_overload_pct}%")

    print(
        f"\n{sum(1 for r in ranked if r.is_synthetic and r.disconnects_network)} of the disconnecting lines "
        f"are SYNTHETIC connectivity fixes (Fase creíble) — meaning that specific 'connection' was the ONLY "
        f"path we reconstructed to that part of the network, real or not. This is an honest artifact of the "
        f"credible-reconstruction step, not a finding about Estonia's real grid resilience."
    )


if __name__ == "__main__":
    main()
