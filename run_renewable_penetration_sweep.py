"""
run_renewable_penetration_sweep.py
====================================
Phase 29: renewable penetration sensitivity sweep.

MASTER PROMPT Section 9 is explicit: "Do not assume these exact
percentages are physically realistic... the purpose is controlled
sensitivity analysis." So is Section 22: every scenario must be
reproducible from a configuration file, and clearly hypothetical.

Method: scale the REAL 2019 wind generation shape (the only real
per-technology hourly series we have) up/down to hit target renewable
penetration levels, holding demand and non-wind generation shape fixed.
This is a deliberately simple, transparent mechanism (Section 3), NOT a
capacity-expansion optimization — it answers "what if the SHAPE of
today's wind output were scaled to hit X% penetration", not "what is
the optimal wind buildout".

Explicit limitation: because our only real per-technology series is
WIND (not solar/hydro/biomass — see data_catalogue.csv), this sweep
scales wind only. Extending to a realistic multi-technology mix needs
the technology-level data this project doesn't have yet.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
AVAILABLE_CAPACITY_MW = 3473  # same definition as run_level2_dynamic_simulation.py
PENETRATION_TARGETS_PCT = [0, 20, 40, 60, 80, 100]


def main():
    raw = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])
    total_demand_mwh = raw["demand_mw"].sum()
    real_wind_mwh = raw["wind_generation_mw"].sum()
    real_wind_penetration_pct = 100 * real_wind_mwh / total_demand_mwh

    print(f"Real 2019 wind penetration (wind generation / demand): {real_wind_penetration_pct:.1f}%")
    print(
        "NOTE: 'penetration' here means WIND ONLY as a share of demand, not "
        "total renewables — see module docstring for why (only wind is "
        "disaggregated in this dataset).\n"
    )

    results = []

    for target_pct in PENETRATION_TARGETS_PCT:
        scale_factor = target_pct / real_wind_penetration_pct if real_wind_penetration_pct > 0 else 0

        scaled_wind_mw = raw["wind_generation_mw"] * scale_factor
        # Keep total domestic generation shape consistent: swap the real wind
        # for scaled wind, holding non-wind generation exactly as observed.
        non_wind_mw = raw["generation_mw"] - raw["wind_generation_mw"]
        scaled_generation_mw = non_wind_mw + scaled_wind_mw

        # Curtailment: wind output above what demand+exports could absorb,
        # DEFINED simply here as scaled wind exceeding total demand for that
        # hour (a crude proxy — a real curtailment model needs transmission
        # and merit-order dispatch, not built yet).
        curtailment_mw = (scaled_wind_mw - raw["demand_mw"]).clip(lower=0)
        curtailment_total_mwh = curtailment_mw.sum()
        curtailment_pct_of_wind = 100 * curtailment_total_mwh / scaled_wind_mw.sum() if scaled_wind_mw.sum() > 0 else 0

        # Reserve margin: available capacity (constant, see AVAILABLE_CAPACITY_MW)
        # vs demand — scaling wind doesn't change installed capacity in this
        # simple sweep (a real study would need wind CAPACITY, not just
        # output, to change — flagged as a further simplification).
        reserve_margin_pct = 100 * (AVAILABLE_CAPACITY_MW - raw["demand_mw"]) / raw["demand_mw"]

        # Import dependency: how much of demand isn't covered by scaled
        # domestic generation (imports proxy, ignoring interconnection limits).
        import_need_mw = (raw["demand_mw"] - scaled_generation_mw).clip(lower=0)
        import_dependency_pct = 100 * import_need_mw.sum() / total_demand_mwh

        results.append({
            "target_wind_penetration_pct": target_pct,
            "scale_factor_applied": round(scale_factor, 2),
            "curtailment_pct_of_wind_output": round(curtailment_pct_of_wind, 2),
            "curtailment_total_gwh": round(curtailment_total_mwh / 1000, 1),
            "import_dependency_pct": round(import_dependency_pct, 2),
            "min_reserve_margin_pct": round(reserve_margin_pct.min(), 1),
        })

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print()
    print(
        "What this sweep does NOT show (be clear about the limits): blackout "
        "probability, EENS, storage requirement and cost all need either a "
        "real dispatch/Monte Carlo layer (Section 16) or real cost/storage "
        "data neither of which exist yet for this project. Reserve margin "
        "barely moves across scenarios here because it's computed against "
        "constant installed capacity, not against the scaled wind capacity — "
        "a genuinely useful reserve-margin sweep needs wind/solar CAPACITY "
        "(MW) scaling, not just output (MWh) scaling. Flagging this rather "
        "than presenting a falsely dramatic result."
    )


if __name__ == "__main__":
    main()
