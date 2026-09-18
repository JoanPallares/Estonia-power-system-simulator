"""
run_cascading_failure_demo.py
================================
Phase 42: starts a cascade from a line that causes CONGESTION (not
outright disconnection — that would trivially "end" the cascade at
step 1, which isn't an interesting demonstration of redistribution).
"""

from A_engine.power_flow.cascading_failure import run_cascading_failure
from A_engine.power_flow.n_minus_1 import run_n_minus_1_lines
from run_dc_power_flow_demo import build_credible_network, REAL_AVG_GENERATION_MW, REAL_AVG_DEMAND_MW


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

    print("Finding a congestion-causing (non-disconnecting) line to start the cascade from...")
    n1_results = run_n_minus_1_lines(net, injections, slack)
    candidates = [r for r in n1_results if not r.disconnects_network and r.new_violations_count > 0]
    candidates.sort(key=lambda r: -r.worst_overload_pct)

    if not candidates:
        print("No non-disconnecting congestion-causing line found in this network/scenario — nothing to cascade from.")
        return

    starting_line = candidates[0]
    from_name = net.buses[starting_line.from_bus].name
    to_name = net.buses[starting_line.to_bus].name
    print(f"Starting cascade at: {from_name} <-> {to_name} "
          f"(initial worst overload if tripped alone: {starting_line.worst_overload_pct}%)\n")

    result = run_cascading_failure(net, injections, slack, starting_line.line_id, trip_threshold_pct=20.0)

    print(f"=== Cascade trace ({len(result.steps)} step(s)) ===")
    for i, step in enumerate(result.steps):
        line = net.lines[step.tripped_line_id]
        from_n = net.buses[line.from_bus_id].name
        to_n = net.buses[line.to_bus_id].name
        if step.reason == "initial":
            print(f"  Step {i}: INITIAL TRIP: {from_n} <-> {to_n}")
        else:
            print(f"  Step {i}: cascading trip: {from_n} <-> {to_n} "
                  f"(was at {step.worst_overload_pct_before_trip}% overload, "
                  f"{step.n_violations_before_trip} total violations before this trip)")

    if result.ended_in_blackout:
        print(f"\nOUTCOME: cascade ended in disconnection — {result.final_isolated_bus_count} bus(es) isolated.")
    else:
        print(f"\nOUTCOME: cascade stabilized after {len(result.steps)-1} additional trip(s) — no more overloads above threshold.")

    print(
        "\nCaveat (same as N-1): the trip threshold (20% over an assumed thermal "
        "limit) is illustrative, not a real Estonian protection setting. This "
        "demonstrates the MECHANISM (Section 17: failure -> redistribution -> "
        "overload -> trip -> repeat) working correctly, not a real prediction "
        "of how an actual Estonian cascade would unfold."
    )


if __name__ == "__main__":
    main()
