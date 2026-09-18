"""
balance.py
==========
Level 1 of the project: the national electricity balance.

Implements the core physical identity (MASTER PROMPT, Section 6):

    Domestic Generation + Imports - Exports - Demand - Losses = System Balance

For a historical period, System Balance should be close to zero by
construction (energy is conserved) — the residual is a *consistency
check* on the data, not a prediction. In later levels, this same
function is reused to compare a *simulated* generation/demand model
against the real system.

This module is completely country-agnostic: it only operates on the
standard schema defined in schema.py.
"""

from __future__ import annotations
import pandas as pd
from .schema import CountryTimeSeries


def compute_balance(ts: CountryTimeSeries) -> pd.DataFrame:
    """
    Computes the national electricity balance residual for every period.

    Returns a copy of the input DataFrame with two extra columns:
      - system_balance_mwh: Generation + Imports - Exports - Demand - Losses
      - self_sufficiency_ratio: domestic_generation / demand (0-1+)
      - import_dependency_ratio: imports / demand (0-1+)
    """
    df = ts.data.copy()

    df["system_balance_mwh"] = (
        df["domestic_generation_mwh"]
        + df["imports_mwh"]
        - df["exports_mwh"]
        - df["demand_mwh"]
        - df["losses_mwh"]
    )

    # Guard against division by zero (should not happen for real demand data)
    safe_demand = df["demand_mwh"].replace(0, pd.NA)

    df["self_sufficiency_ratio"] = df["domestic_generation_mwh"] / safe_demand
    df["import_dependency_ratio"] = df["imports_mwh"] / safe_demand

    return df


def balance_summary(balance_df: pd.DataFrame) -> dict:
    """
    Aggregate KPIs over the whole period (MASTER PROMPT, Section 26 —
    Energy KPIs). Useful for a quick sanity check after loading a new
    country dataset.
    """
    total_demand = balance_df["demand_mwh"].sum()
    total_generation = balance_df["domestic_generation_mwh"].sum()
    total_imports = balance_df["imports_mwh"].sum()
    total_exports = balance_df["exports_mwh"].sum()
    total_losses = balance_df["losses_mwh"].sum()
    residual = balance_df["system_balance_mwh"].sum()

    return {
        "n_periods": len(balance_df),
        "total_demand_mwh": round(total_demand, 1),
        "total_domestic_generation_mwh": round(total_generation, 1),
        "total_imports_mwh": round(total_imports, 1),
        "total_exports_mwh": round(total_exports, 1),
        "total_losses_mwh": round(total_losses, 1),
        "balance_residual_mwh": round(residual, 1),
        "balance_residual_pct_of_demand": round(100 * residual / total_demand, 3) if total_demand else None,
        "avg_self_sufficiency_ratio": round(balance_df["self_sufficiency_ratio"].mean(), 3),
        "avg_import_dependency_ratio": round(balance_df["import_dependency_ratio"].mean(), 3),
    }
