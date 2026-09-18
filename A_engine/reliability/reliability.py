"""
reliability.py
===============
Phase 35: standard reliability metrics computed from Monte Carlo output
(simulation/monte_carlo.py). Country/scenario-agnostic.
"""

from __future__ import annotations
import numpy as np


def compute_reliability_metrics(mc_result: dict, reserve_threshold_pct: float = 10.0) -> dict:
    """
    LOLP: Loss of Load Probability — fraction of all (iteration, hour)
          pairs with unserved energy > 0.
    LOLE: Loss of Load Expectation — expected number of hours per year
          (per iteration, then averaged) with unserved energy > 0.
    EENS: Expected Energy Not Served — average total unserved MWh per
          simulated year (per iteration, then averaged).
    Reserve violations: count of (iteration, hour) pairs where reserve
          margin < reserve_threshold_pct (a weaker condition than
          actual unserved energy — an early-warning metric).
    """
    deficit_hour = mc_result["deficit_hour"]
    unserved_mw = mc_result["unserved_mw"]
    demand_mw = mc_result["demand_mw"]
    available_capacity_mw = mc_result["available_capacity_mw"]
    n_iter = mc_result["n_iterations"]
    n_hours = mc_result["n_hours"]

    lolp = deficit_hour.sum() / (n_iter * n_hours)

    hours_with_deficit_per_iteration = deficit_hour.sum(axis=1)  # shape (n_iter,)
    lole_hours_per_year = hours_with_deficit_per_iteration.mean()

    unserved_mwh_per_iteration = unserved_mw.sum(axis=1)  # shape (n_iter,)
    eens_mwh_per_year = unserved_mwh_per_iteration.mean()

    reserve_margin_pct = 100 * (available_capacity_mw - demand_mw) / demand_mw
    reserve_violation = reserve_margin_pct < reserve_threshold_pct
    n_reserve_violations = int(reserve_violation.sum())
    reserve_violations_per_iteration = reserve_violation.sum(axis=1).mean()

    return {
        "n_iterations": n_iter,
        "n_hours_per_iteration": n_hours,
        "LOLP": round(float(lolp), 6),
        "LOLP_pct": round(float(lolp) * 100, 4),
        "LOLE_hours_per_year": round(float(lole_hours_per_year), 2),
        "EENS_mwh_per_year": round(float(eens_mwh_per_year), 2),
        "total_reserve_violations": n_reserve_violations,
        "avg_reserve_violations_per_year": round(float(reserve_violations_per_iteration), 2),
        "worst_iteration_unserved_mwh": round(float(unserved_mwh_per_iteration.max()), 2),
        "best_iteration_unserved_mwh": round(float(unserved_mwh_per_iteration.min()), 2),
    }
