import subprocess
import sys
import time
from pathlib import Path


# ============================================================
# ESTONIA POWER SYSTEM SIMULATOR
# MASTER EXECUTION SCRIPT
# ============================================================

ROOT = Path(__file__).resolve().parent


def run_step(name, command):
    """Run one simulation step and report its status."""

    print("\n" + "=" * 80)
    print(f"▶ {name}")
    print("=" * 80)

    start = time.time()

    result = subprocess.run(
        [sys.executable] + command,
        cwd=ROOT
    )

    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n✓ {name} — PASSED ({elapsed:.1f} s)")
        return True
    else:
        print(f"\n✗ {name} — FAILED ({elapsed:.1f} s)")
        return False


def main():

    print("\n")
    print("=" * 80)
    print("        ESTONIA POWER SYSTEM SIMULATOR")
    print("                 PLAY SIMULATION")
    print("=" * 80)
    print()
    print(f"Project directory:")
    print(ROOT)
    print()

    results = []

    # ========================================================
    # 1. TESTS
    # ========================================================

    results.append((
        "Tests",
        run_step(
            "TEST SUITE",
            ["-m", "pytest", "-q"]
        )
    ))

    # ========================================================
    # 2. DATA PIPELINE
    # ========================================================

    data_pipeline = [
        (
            "Data Pipeline Demo",
            ["run_pipeline_demo.py"]
        ),
        (
            "Level 1 National Balance",
            ["run_level1_balance.py"]
        ),
        (
            "Level 1 Balance Report",
            ["run_level1_balance_report.py"]
        ),
        (
            "Generation Fleet",
            ["run_generation_fleet.py"]
        ),
        (
            "Weather Correlation Analysis",
            ["run_weather_correlation_analysis.py"]
        ),
        (
            "Demand Model Analysis",
            ["run_demand_model_analysis.py"]
        ),
    ]

    for name, command in data_pipeline:
        results.append((name, run_step(name, command)))

    # ========================================================
    # 3. LEVEL 2 SYSTEM SIMULATION
    # ========================================================

    level2 = [
        (
            "Level 2 System Status",
            ["run_level2_status.py"]
        ),
        (
            "Level 2 Simulation",
            ["run_level2_simulation.py"]
        ),
        (
            "Level 2 Dynamic Simulation",
            ["run_level2_dynamic_simulation.py"]
        ),
        (
            "Grid Simulation",
            ["run_grid_simulation.py"]
        ),
    ]

    for name, command in level2:
        results.append((name, run_step(name, command)))

    # ========================================================
    # 4. RENEWABLES AND SCENARIOS
    # ========================================================

    scenarios = [
        (
            "Renewable Penetration Sweep",
            ["run_renewable_penetration_sweep.py"]
        ),
        (
            "Scenario Sweep",
            ["run_scenario_sweep.py"]
        ),
    ]

    for name, command in scenarios:
        results.append((name, run_step(name, command)))

    # Individual scenarios
    individual_scenarios = [
        ("Current System", "current"),
        ("High Demand", "high_demand"),
        ("Low Demand", "low_demand"),
        ("High Wind", "high_wind"),
        ("Low Wind", "low_wind"),
        ("Low Solar", "low_solar"),
        ("Low Hydro", "low_hydro"),
        ("Oil Shale Outage", "oil_shale_outage"),
        ("Finland Interconnection Outage", "finland_outage"),
        ("Latvia Interconnection Outage", "latvia_outage"),
        ("Imports -50%", "imports_minus_50"),
        ("Imports Zero", "imports_zero"),
        ("High Renewables", "high_renewables"),
        ("High Renewables + Storage", "high_renewables_storage"),
        ("Extreme Winter", "extreme_winter"),
        (
            "Extreme Winter + Interconnection Failure",
            "extreme_winter_interconnection_failure"
        ),
    ]

    for name, scenario in individual_scenarios:
        results.append((
            f"Scenario: {name}",
            run_step(
                f"SCENARIO — {name}",
                ["run_scenario.py", "--scenario", scenario]
            )
        ))

    # ========================================================
    # 5. FAILURE AND RELIABILITY ANALYSIS
    # ========================================================

    reliability = [
        (
            "Deterministic Failure Analysis",
            ["run_failure_deterministic.py"]
        ),
        (
            "Failure Scenario Analysis",
            ["run_failure_scenario.py"]
        ),
        (
            "Monte Carlo Simulation",
            ["run_monte_carlo.py"]
        ),
        (
            "Monte Carlo Reliability",
            ["run_monte_carlo_reliability.py"]
        ),
    ]

    for name, command in reliability:
        results.append((name, run_step(name, command)))

    # ========================================================
    # 6. NETWORK
    # ========================================================

    network = [
        (
            "Build Estonia Network",
            ["run_build_estonia_network.py"]
        ),
        (
            "OSM Network Ingestion",
            ["ingest_osm_network.py"]
        ),
        (
            "Credible OSM Network Ingestion",
            ["ingest_osm_network_credible.py"]
        ),
        (
            "DC Power Flow",
            ["run_dc_power_flow_demo.py"]
        ),
        (
            "N-1 Analysis",
            ["run_n_minus_1_analysis.py"]
        ),
        (
            "Cascading Failure Analysis",
            ["run_cascading_failure_demo.py"]
        ),
    ]

    for name, command in network:
        results.append((name, run_step(name, command)))

    # ========================================================
    # 7. OPTIMIZATION
    # ========================================================

    optimization = [
        (
            "Economic Dispatch",
            ["run_economic_dispatch_demo.py"]
        ),
        (
            "Capacity Optimization Sweep",
            ["run_capacity_optimization_sweep.py"]
        ),
        (
            "Vulnerability Map",
            ["run_vulnerability_map.py"]
        ),
    ]

    for name, command in optimization:
        results.append((name, run_step(name, command)))

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n\n")
    print("=" * 80)
    print("                    FINAL REPORT")
    print("=" * 80)

    passed = 0
    failed = 0

    for name, success in results:

        if success:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"{status:<10} {name}")

    print("-" * 80)
    print(f"TOTAL : {len(results)}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print("=" * 80)

    if failed == 0:
        print("\n🎉 ALL SIMULATIONS COMPLETED SUCCESSFULLY")
        print()
        print("The Estonia Power System Simulator executed")
        print("all registered simulations without errors.")
        print()
        return 0

    else:
        print("\n⚠ SOME SIMULATIONS FAILED")
        print()
        print("Check the FAILED entries above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())