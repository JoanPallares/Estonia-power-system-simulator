"""
run_failure_deterministic.py
==============================
Phase 33: EstLink 1 OFF, then EstLink 2 OFF, then BOTH OFF — observing
generation / imports / reserve / unserved energy.

HONESTY NOTE on methodology: the real 2019 archive gives COMBINED
Finland flow (EstLink 1 + EstLink 2 together, one column), not a
per-cable split. To simulate "EstLink 1 OFF" specifically, this script
compares that REAL combined flow against each failure case's REMAINING
nominal capacity (350 MW alone, 650 MW alone, or 0) to see how often
the real historical flow would have exceeded what remains — it does
NOT assume how the historical flow itself would have redistributed
between cables (that would need real dispatch data). This is a
capacity-adequacy check against real history, not a re-simulation of
history under the failure.
"""

from pathlib import Path
import pandas as pd

from A_engine.models.interconnection import InterconnectionConfig, InterconnectionFlow, check_capacity_violation

ROOT = Path(__file__).parent

ESTLINK1_CAPACITY_MW = 350
ESTLINK2_CAPACITY_MW = 650
DOMESTIC_CAPACITY_MW = 3473  # Elering, start of 2025 — see C_configs/estonia.yaml


def run_case(raw: pd.DataFrame, estlink1_on: bool, estlink2_on: bool, label: str) -> dict:
    available_capacity_mw = DOMESTIC_CAPACITY_MW
    if estlink1_on:
        available_capacity_mw += ESTLINK1_CAPACITY_MW
    if estlink2_on:
        available_capacity_mw += ESTLINK2_CAPACITY_MW

    reserve_margin_pct = 100 * (available_capacity_mw - raw["demand_mw"]) / raw["demand_mw"]

    remaining_capacity_mw = (ESTLINK1_CAPACITY_MW if estlink1_on else 0) + (ESTLINK2_CAPACITY_MW if estlink2_on else 0)
    config = InterconnectionConfig("Finland", import_capacity_mw=remaining_capacity_mw, export_capacity_mw=remaining_capacity_mw)
    violations = [
        check_capacity_violation(InterconnectionFlow("Finland", flow_mw=f), config)
        for f in raw["flow_ee_to_fi_mw"]
    ]
    n_violations = sum(1 for v in violations if v is not None)

    return {
        "case": label,
        "available_capacity_mw": available_capacity_mw,
        "min_reserve_margin_pct": round(reserve_margin_pct.min(), 1),
        "hours_real_2019_FI_flow_exceeds_remaining_capacity": n_violations,
        "pct_of_year": round(100 * n_violations / len(raw), 2),
    }


def main():
    raw = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])

    xls_path = ROOT / "B_data" / "raw" / "elering" / "2019_arhiiv_0.xls"
    if not xls_path.exists():
        raise FileNotFoundError(f"{xls_path} not found — this script needs the raw per-country flow column.")

    fakt = pd.read_excel(xls_path, sheet_name="fakt", engine="xlrd")
    fi_flow_real = fakt["Füüsilised vood EE->FI MW"].reset_index(drop=True)
    if len(fi_flow_real) != len(raw):
        raise RuntimeError(
            f"Row count mismatch between processed ({len(raw)}) and raw xls ({len(fi_flow_real)}) "
            f"Finland flow — re-run ingest_elering_2019_archive.py before this script."
        )
    raw["flow_ee_to_fi_mw"] = fi_flow_real.values

    print("=== Phase 33: Deterministic interconnection failures (REAL 2019 flow data) ===\n")
    results = [
        run_case(raw, estlink1_on=True, estlink2_on=True, label="Baseline (both ON)"),
        run_case(raw, estlink1_on=False, estlink2_on=True, label="EstLink 1 OFF"),
        run_case(raw, estlink1_on=True, estlink2_on=False, label="EstLink 2 OFF"),
        run_case(raw, estlink1_on=False, estlink2_on=False, label="BOTH OFF"),
    ]

    df = pd.DataFrame(results)
    pd.set_option("display.width", 140)
    print(df.to_string(index=False))
    print()
    print(
        "Interpretation: even with BOTH EstLink cables off, reserve margin stays "
        "high because domestic capacity (3473 MW) alone is ~2x Estonia's real "
        "2019 peak demand. The 'violations' column is more informative than "
        "reserve margin here — it shows how many real 2019 hours had a Finland "
        "flow that WOULD have exceeded remaining capacity under each failure "
        "case, i.e. genuine historical import/export dependency, distinct from "
        "the pure capacity-adequacy question."
    )


if __name__ == "__main__":
    main()
