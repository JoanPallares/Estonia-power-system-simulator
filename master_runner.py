"""
master_runner.py
================

ESTONIA POWER SYSTEM SIMULATOR

Master execution, validation and figure-generation runner.

One command executes the complete reproducible project workflow:

    1. Test suite
    2. Data ingestion
    3. Analysis and simulation scripts
    4. All named scenarios
    5. Main project figures

Generated figures:

    docs/figures/demand_vs_capacity_2019.png
    docs/figures/network_map.png
    docs/figures/vulnerability_map.png

Usage
-----

    python master_runner.py

Exit code
----------

    0 -> all checks and figure generation passed
    1 -> one or more checks failed

The script uses the Python interpreter that launches it, so it is
recommended to run it from the project's virtual environment.
"""


# ============================================================
# IMPORTS
# ============================================================

import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parent

TIMEOUT_SECONDS = 120

FIGURES_DIR = ROOT / "docs" / "figures"

FIGURES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DATA PATHS
# ============================================================

HOURLY_DATA = (
    ROOT
    / "B_data"
    / "processed"
    / "estonia_hourly_2019.csv"
)

SUBSTATIONS_DATA = (
    ROOT
    / "B_data"
    / "processed"
    / "estonia_substations_CREDIBLE.csv"
)

ADJACENCIES_DATA = (
    ROOT
    / "B_data"
    / "processed"
    / "estonia_substation_adjacencies_CREDIBLE.csv"
)

VULNERABILITY_DATA = (
    ROOT
    / "B_data"
    / "processed"
    / "vulnerability_map.csv"
)


# ============================================================
# FIGURE OUTPUTS
# ============================================================

DEMAND_FIGURE = (
    FIGURES_DIR
    / "demand_vs_capacity_2019.png"
)

NETWORK_FIGURE = (
    FIGURES_DIR
    / "network_map.png"
)

VULNERABILITY_FIGURE = (
    FIGURES_DIR
    / "vulnerability_map.png"
)


# ============================================================
# DATA INGESTION SCRIPTS
# ============================================================

INGEST_SCRIPTS = [
    "ingest_elering_2019_archive.py",
    "ingest_osm_network.py",
    "ingest_osm_network_credible.py",
    "ingest_weather_era5.py",
]


# ============================================================
# ANALYSIS / SIMULATION SCRIPTS
# ============================================================

RUN_SCRIPTS = [
    "run_build_estonia_network.py",
    "run_capacity_optimization_sweep.py",
    "run_cascading_failure_demo.py",
    "run_dc_power_flow_demo.py",
    "run_demand_model_analysis.py",
    "run_economic_dispatch_demo.py",
    "run_failure_deterministic.py",
    "run_failure_scenario.py",
    "run_generation_fleet.py",
    "run_grid_simulation.py",
    "run_level1_balance.py",
    "run_level1_balance_report.py",
    "run_level2_dynamic_simulation.py",
    "run_level2_simulation.py",
    "run_level2_status.py",
    "run_monte_carlo.py",
    "run_monte_carlo_reliability.py",
    "run_n_minus_1_analysis.py",
    "run_pipeline_demo.py",
    "run_renewable_penetration_sweep.py",
    "run_scenario_sweep.py",
    "run_vulnerability_map.py",
    "run_weather_correlation_analysis.py",
]


# ============================================================
# SCENARIOS
# ============================================================

SCENARIO_ALIASES = [
    "current",
    "high_demand",
    "low_demand",
    "high_wind",
    "low_wind",
    "low_solar",
    "low_hydro",
    "oil_shale_outage",
    "finland_outage",
    "latvia_outage",
    "imports_minus_50",
    "imports_zero",
    "high_renewables",
    "high_renewables_storage",
    "extreme_winter",
    "extreme_winter_interconnection_failure",
]


SCENARIO_DISPLAY_NAMES = {
    "current": "Current System",
    "high_demand": "High Demand",
    "low_demand": "Low Demand",
    "high_wind": "High Wind",
    "low_wind": "Low Wind",
    "low_solar": "Low Solar",
    "low_hydro": "Low Hydro",
    "oil_shale_outage": "Oil Shale Outage",
    "finland_outage": "Finland Interconnection Outage",
    "latvia_outage": "Latvia Interconnection Outage",
    "imports_minus_50": "Imports -50%",
    "imports_zero": "Imports Zero",
    "high_renewables": "High Renewables",
    "high_renewables_storage": "High Renewables + Storage",
    "extreme_winter": "Extreme Winter",
    "extreme_winter_interconnection_failure":
        "Extreme Winter + Interconnection Failure",
}


# ============================================================
# DISPLAY
# ============================================================

WIDTH = 80


def print_header(title: str):
    print()
    print("=" * WIDTH)
    print(title.center(WIDTH))
    print("=" * WIDTH)


def print_section(title: str):
    print()
    print("-" * WIDTH)
    print(f"▶ {title}")
    print("-" * WIDTH)


# ============================================================
# RUN ONE CHECK
# ============================================================

def run_check(
    name: str,
    command: list[str],
):
    """
    Execute one project check.

    Returns
    -------
    success : bool
    elapsed : float
    error : str
    """

    start = time.time()

    try:

        result = subprocess.run(
            [sys.executable] + command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )

        elapsed = time.time() - start

        success = result.returncode == 0

        if success:
            return True, elapsed, ""

        error = result.stderr.strip()

        if not error:
            error = result.stdout.strip()

        return False, elapsed, error

    except subprocess.TimeoutExpired:

        elapsed = time.time() - start

        return (
            False,
            elapsed,
            f"TIMEOUT after {TIMEOUT_SECONDS}s",
        )

    except Exception as exc:

        elapsed = time.time() - start

        return (
            False,
            elapsed,
            repr(exc),
        )


# ============================================================
# FIGURE 1
# DEMAND VS GENERATION + NET IMPORTS
# ============================================================

def generate_demand_figure():
    """
    Generate the 2019 demand vs generation + net imports figure.

    Source:
        B_data/processed/estonia_hourly_2019.csv

    The figure uses daily averages of the real 2019 hourly dataset.
    """

    print_section("FIGURE 1 — DEMAND VS GENERATION")

    if not HOURLY_DATA.exists():

        raise FileNotFoundError(
            f"Missing data file: {HOURLY_DATA}"
        )

    df = pd.read_csv(HOURLY_DATA)

    required = [
        "timestamp_utc",
        "demand_mw",
        "generation_mw",
        "imports_mw",
        "exports_mw",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:

        raise KeyError(
            f"Missing required columns: {missing}"
        )

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        utc=True,
    )

    # Net imports = imports - exports.
    df["net_imports_mw"] = (
        df["imports_mw"]
        - df["exports_mw"]
    )

    # Generation + net imports.
    df["generation_plus_net_imports_mw"] = (
        df["generation_mw"]
        + df["net_imports_mw"]
    )

    # Daily average.
    daily = (
        df.set_index("timestamp_utc")
        [
            [
                "demand_mw",
                "generation_plus_net_imports_mw",
            ]
        ]
        .resample("D")
        .mean()
        .dropna()
    )

    fig, ax = plt.subplots(
        figsize=(15, 5.25),
        dpi=150,
    )

    ax.fill_between(
        daily.index,
        daily["generation_plus_net_imports_mw"],
        alpha=0.15,
    )

    ax.plot(
        daily.index,
        daily["generation_plus_net_imports_mw"],
        linewidth=1.8,
        label="Generation + net imports",
    )

    ax.plot(
        daily.index,
        daily["demand_mw"],
        linewidth=1.8,
        label="Demand",
    )

    ax.set_title(
        "Estonia 2019 — real hourly data, daily average (MW)",
        fontsize=15,
        loc="left",
    )

    ax.set_ylabel("MW")

    ax.grid(
        True,
        alpha=0.15,
    )

    ax.legend(
        loc="upper left",
        frameon=False,
    )

    fig.tight_layout()

    fig.savefig(
        DEMAND_FIGURE,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(
        f"   ✓ Generated: "
        f"{DEMAND_FIGURE.relative_to(ROOT)}"
    )

    return DEMAND_FIGURE


# ============================================================
# FIGURE 2
# TRANSMISSION NETWORK
# ============================================================

def generate_network_figure():
    """
    Generate the reconstructed Estonia transmission network.

    Sources:
        - estonia_substations_CREDIBLE.csv
        - estonia_substation_adjacencies_CREDIBLE.csv

    Real OSM-derived and synthetic connectivity-fix lines are shown
    separately.
    """

    print_section("FIGURE 2 — TRANSMISSION NETWORK")

    if not SUBSTATIONS_DATA.exists():

        raise FileNotFoundError(
            f"Missing data file: {SUBSTATIONS_DATA}"
        )

    if not ADJACENCIES_DATA.exists():

        raise FileNotFoundError(
            f"Missing data file: {ADJACENCIES_DATA}"
        )

    buses = pd.read_csv(
        SUBSTATIONS_DATA
    )

    lines = pd.read_csv(
        ADJACENCIES_DATA
    )

    required_bus_columns = [
        "id",
        "name",
        "voltage_kv",
        "latitude",
        "longitude",
    ]

    required_line_columns = [
        "from_bus",
        "to_bus",
        "connection_type",
    ]

    for col in required_bus_columns:

        if col not in buses.columns:
            raise KeyError(
                f"Missing bus column: {col}"
            )

    for col in required_line_columns:

        if col not in lines.columns:
            raise KeyError(
                f"Missing line column: {col}"
            )

    # --------------------------------------------------------
    # Coordinate lookup
    # --------------------------------------------------------

    coords = (
        buses
        .set_index("id")
        [
            [
                "longitude",
                "latitude",
            ]
        ]
        .to_dict("index")
    )

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(12, 12),
        dpi=150,
    )

    # --------------------------------------------------------
    # Lines
    # --------------------------------------------------------

    for _, row in lines.iterrows():

        source = coords.get(
            row["from_bus"]
        )

        target = coords.get(
            row["to_bus"]
        )

        if source is None or target is None:
            continue

        x = [
            source["longitude"],
            target["longitude"],
        ]

        y = [
            source["latitude"],
            target["latitude"],
        ]

        connection_type = (
            str(row["connection_type"])
        )

        if connection_type == "synthetic_nearest_neighbor":

            ax.plot(
                x,
                y,
                linestyle="--",
                linewidth=0.7,
                alpha=0.35,
            )

        else:

            ax.plot(
                x,
                y,
                linestyle="-",
                linewidth=0.65,
                alpha=0.65,
            )

    # --------------------------------------------------------
    # 110 kV substations
    # --------------------------------------------------------

    buses_110 = buses[
        buses["voltage_kv"] == 110
    ]

    ax.scatter(
        buses_110["longitude"],
        buses_110["latitude"],
        s=20,
        linewidths=0.5,
        label="110 kV substation",
        zorder=5,
    )

    # --------------------------------------------------------
    # 330 kV substations
    # --------------------------------------------------------

    buses_330 = buses[
        buses["voltage_kv"] == 330
    ]

    ax.scatter(
        buses_330["longitude"],
        buses_330["latitude"],
        s=85,
        linewidths=1.0,
        label="330 kV substation",
        zorder=6,
    )

    # --------------------------------------------------------
    # Titles and labels
    # --------------------------------------------------------

    ax.set_title(
        "Estonia transmission network — reconstructed from real OSM data",
        fontsize=15,
        loc="left",
    )

    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")

    ax.grid(
        True,
        alpha=0.12,
    )

    ax.legend(
        loc="lower left",
        frameon=False,
    )

    ax.set_aspect(
        "equal",
        adjustable="box",
    )

    fig.tight_layout()

    fig.savefig(
        NETWORK_FIGURE,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(
        f"   ✓ Generated: "
        f"{NETWORK_FIGURE.relative_to(ROOT)}"
    )

    return NETWORK_FIGURE


# ============================================================
# FIGURE 3
# VULNERABILITY MAP
# ============================================================

def generate_vulnerability_figure():
    """
    Generate the vulnerability heatmap.

    Source:
        B_data/processed/vulnerability_map.csv

    Metric:
        EENS (MWh/year)

    The underlying dataset explicitly represents stress assumptions.
    """

    print_section("FIGURE 3 — VULNERABILITY MAP")

    if not VULNERABILITY_DATA.exists():

        raise FileNotFoundError(
            f"Missing data file: {VULNERABILITY_DATA}"
        )

    df = pd.read_csv(
        VULNERABILITY_DATA
    )

    required = [
        "wind_multiplier",
        "demand_growth_pct",
        "EENS_mwh_per_year",
        "LOLP_pct",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:

        raise KeyError(
            f"Missing vulnerability columns: {missing}"
        )

    # --------------------------------------------------------
    # Pivot table
    # --------------------------------------------------------

    pivot = df.pivot(
        index="demand_growth_pct",
        columns="wind_multiplier",
        values="EENS_mwh_per_year",
    )

    pivot = pivot.sort_index()

    pivot = pivot[
        sorted(pivot.columns)
    ]

    x = pivot.columns.to_numpy()
    y = pivot.index.to_numpy()
    z = pivot.to_numpy()

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(12, 8.5),
        dpi=150,
    )

    image = ax.imshow(
        z,
        origin="lower",
        aspect="auto",
        interpolation="nearest",
    )

    # --------------------------------------------------------
    # Axis labels
    # --------------------------------------------------------

    ax.set_xticks(
        np.arange(len(x))
    )

    ax.set_xticklabels(
        [
            f"{value:.1f}x"
            for value in x
        ]
    )

    ax.set_yticks(
        np.arange(len(y))
    )

    ax.set_yticklabels(
        [
            f"{value:+.0f}%"
            for value in y
        ]
    )

    ax.set_xlabel(
        "Wind capacity multiplier (today = 1x, 695 MW)"
    )

    ax.set_ylabel(
        "Demand growth vs real 2019"
    )

    ax.set_title(
        "Vulnerability map — EENS (MWh/yr), STRESS assumptions",
        fontsize=15,
        loc="left",
    )

    # --------------------------------------------------------
    # Cell annotations
    # --------------------------------------------------------

    max_value = np.nanmax(z)

    for i in range(z.shape[0]):

        for j in range(z.shape[1]):

            value = z[i, j]

            if value >= 1_000_000:
                label = f"{value / 1000:.0f}k"

            elif value >= 1000:
                label = f"{value / 1000:.0f}k"

            else:
                label = f"{value:.0f}"

            # Choose text brightness based on normalized value.
            normalized = (
                value / max_value
                if max_value > 0
                else 0
            )

            text_color = (
                "white"
                if normalized > 0.35
                else "black"
            )

            ax.text(
                j,
                i,
                label,
                ha="center",
                va="center",
                fontsize=8,
                color=text_color,
            )

    # --------------------------------------------------------
    # Colorbar
    # --------------------------------------------------------

    colorbar = fig.colorbar(
        image,
        ax=ax,
        pad=0.02,
    )

    colorbar.set_label(
        "EENS (MWh/year)"
    )

    fig.tight_layout()

    fig.savefig(
        VULNERABILITY_FIGURE,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(
        f"   ✓ Generated: "
        f"{VULNERABILITY_FIGURE.relative_to(ROOT)}"
    )

    return VULNERABILITY_FIGURE


# ============================================================
# GENERATE ALL FIGURES
# ============================================================

def generate_all_figures():
    """
    Generate all official project figures.

    Returns
    -------
    success : bool
    elapsed : float
    error : str
    """

    start = time.time()

    try:

        generate_demand_figure()

        generate_network_figure()

        generate_vulnerability_figure()

        elapsed = time.time() - start

        return True, elapsed, ""

    except Exception as exc:

        elapsed = time.time() - start

        return (
            False,
            elapsed,
            repr(exc),
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")

    print_header(
        "ESTONIA POWER SYSTEM SIMULATOR"
    )

    print(
        "MASTER EXECUTION, VALIDATION "
        "& FIGURE GENERATION"
    )

    print()

    print("Project directory:")
    print(f"  {ROOT}")

    print()

    print("Python interpreter:")
    print(f"  {sys.executable}")

    print()

    # --------------------------------------------------------
    # Build checks
    # --------------------------------------------------------

    checks = []

    # Tests
    checks.append(
        (
            "Tests",
            ["-m", "pytest", "-q"],
            "TEST SUITE",
            "TESTS",
        )
    )

    # Ingestion
    for script in INGEST_SCRIPTS:

        checks.append(
            (
                f"Ingestion: {script}",
                [script],
                f"INGEST — {script}",
                "DATA INGESTION",
            )
        )

    # Analysis scripts
    for script in RUN_SCRIPTS:

        checks.append(
            (
                f"Script: {script}",
                [script],
                script,
                "ANALYSIS & SIMULATION",
            )
        )

    # Scenarios
    for alias in SCENARIO_ALIASES:

        display_name = (
            SCENARIO_DISPLAY_NAMES.get(
                alias,
                alias,
            )
        )

        checks.append(
            (
                f"Scenario: {display_name}",
                [
                    "run_scenario.py",
                    "--scenario",
                    alias,
                ],
                f"SCENARIO — {display_name}",
                "SCENARIOS",
            )
        )

    print(
        f"Running {len(checks)} execution checks..."
    )

    # --------------------------------------------------------
    # Run checks
    # --------------------------------------------------------

    results = []

    current_category = None

    for (
        name,
        command,
        display_name,
        category,
    ) in checks:

        if category != current_category:

            current_category = category

            print_section(category)

        print()
        print(
            f"▶ {display_name}"
        )

        success, elapsed, error = run_check(
            name,
            command,
        )

        if success:

            print(
                f"   ✓ PASS   ({elapsed:.1f}s)"
            )

        else:

            print(
                f"   ✗ FAIL   ({elapsed:.1f}s)"
            )

            if error:

                error_lines = [
                    line.strip()
                    for line in error.splitlines()
                    if line.strip()
                ]

                if error_lines:

                    print(
                        f"   └─ {error_lines[-1]}"
                    )

        results.append(
            {
                "name": name,
                "success": success,
                "elapsed": elapsed,
                "error": error,
            }
        )

    # ========================================================
    # FIGURE GENERATION
    # ========================================================

    figure_success, figure_elapsed, figure_error = (
        generate_all_figures()
    )

    results.append(
        {
            "name": "Figure Generation",
            "success": figure_success,
            "elapsed": figure_elapsed,
            "error": figure_error,
        }
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print("\n\n")

    print_header(
        "FINAL REPORT"
    )

    passed = sum(
        result["success"]
        for result in results
    )

    failed = (
        len(results)
        - passed
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    for result in results:

        if result["success"]:

            status = "✓ PASS"

        else:

            status = "✗ FAIL"

        print(
            f"{status:<10}"
            f"{result['name']}"
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("-" * WIDTH)

    print(
        f"TOTAL : {len(results)}"
    )

    print(
        f"PASSED: {passed}"
    )

    print(
        f"FAILED: {failed}"
    )

    print("=" * WIDTH)

    # ========================================================
    # GENERATED FIGURES
    # ========================================================

    print()

    print(
        "GENERATED FIGURES"
    )

    print("-" * WIDTH)

    for figure in [
        DEMAND_FIGURE,
        NETWORK_FIGURE,
        VULNERABILITY_FIGURE,
    ]:

        if figure.exists():

            size_kb = (
                figure.stat().st_size
                / 1024
            )

            print(
                f"✓ {figure.name}"
            )

            print(
                f"  {figure.relative_to(ROOT)}"
                f" ({size_kb:.1f} KB)"
            )

        else:

            print(
                f"✗ {figure.name}"
            )

    # ========================================================
    # SUCCESS
    # ========================================================

    if failed == 0:

        print()

        print(
            "🎉 ALL CHECKS PASSED"
        )

        print()

        print(
            "The Estonia Power System Simulator "
            "executed all registered checks successfully."
        )

        print()

        print(
            "Project status: REPRODUCIBLE ✓"
        )

        print()

        print(
            "Figures generated successfully:"
        )

        print(
            "  ✓ demand_vs_capacity_2019.png"
        )

        print(
            "  ✓ network_map.png"
        )

        print(
            "  ✓ vulnerability_map.png"
        )

        print()

        return 0

    # ========================================================
    # FAILURE
    # ========================================================

    print()

    print(
        "⚠ SOME CHECKS FAILED"
    )

    print()

    print(
        "Failed checks:"
    )

    for result in results:

        if not result["success"]:

            print(
                f"  ✗ {result['name']}"
            )

            if result["error"]:

                print(
                    f"    {result['error']}"
                )

    print()

    return 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())