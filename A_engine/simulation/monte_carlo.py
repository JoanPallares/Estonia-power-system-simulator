"""
monte_carlo.py
===============
Phase 34: stochastic reliability simulation.

*** ALL RANDOMNESS PARAMETERS BELOW ARE ASSUMPTIONS ***
MASTER PROMPT Section 15: "Never invent probability values and present
them as real-world statistics." The default MonteCarloConfig values
(std devs, outage probabilities) are ROUND, GENERIC, illustrative
numbers — not sourced from any real Estonian reliability study. Anyone
citing results from this module MUST cite these assumptions alongside
them, not just the output numbers.

Vectorized with numpy for speed at 1,000-10,000 iterations x 8760 hours.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class MonteCarloConfig:
    n_iterations: int = 1000
    random_seed: int = 42  # reproducibility (MASTER PROMPT Section 24: reproducible random seeds)

    # ALL of the following are ASSUMPTIONS, not measured Estonian statistics:
    demand_std_fraction: float = 0.05        # demand multiplier ~ Normal(1.0, this)
    wind_std_fraction: float = 0.30           # wind is far more variable than demand — generic illustrative value
    dispatchable_forced_outage_prob: float = 0.03   # ASSUMED per-hour probability the dispatchable fleet is at reduced capacity
    dispatchable_outage_severity_fraction: float = 0.20  # ASSUMED: when in outage, capacity reduced by this fraction
    interconnection_forced_outage_prob: float = 0.01     # ASSUMED per-hour probability Finland interconnection is unavailable


def run_monte_carlo(
    baseline_demand_mw: np.ndarray,
    baseline_wind_mw: np.ndarray,
    domestic_dispatchable_capacity_mw: float,
    wind_capacity_mw: float,
    solar_capacity_mw: float,
    interconnection_capacity_mw: float,
    config: MonteCarloConfig = MonteCarloConfig(),
) -> dict:
    """
    Returns per-iteration and aggregate results for LOLP/LOLE/EENS
    (Phase 35 consumes this). Available capacity per (iteration, hour):

        wind_capacity + solar_capacity
        + dispatchable_capacity x (1 - outage_draw x severity)
        + interconnection_capacity x (1 - interconnection_outage_draw)

    Demand per (iteration, hour): baseline_demand x Normal(1, demand_std)

    This does NOT use baseline_wind_mw for capacity (capacity is fixed
    nameplate, per the same simplification used throughout Level 2) —
    it's accepted as a parameter for future extension (e.g. a real
    capacity-credit model) but not currently used in the capacity calc.
    """
    rng = np.random.default_rng(config.random_seed)
    n_hours = len(baseline_demand_mw)
    n_iter = config.n_iterations

    baseline_demand_mw = baseline_demand_mw.astype(np.float32)

    demand_mw = rng.normal(1.0, config.demand_std_fraction, size=(n_iter, n_hours)).astype(np.float32)
    np.clip(demand_mw, 0.5, 1.5, out=demand_mw)  # sanity bound — never negative/absurd demand
    demand_mw *= baseline_demand_mw[None, :]

    available_capacity_mw = np.full((n_iter, n_hours), wind_capacity_mw + solar_capacity_mw, dtype=np.float32)

    dispatchable_outage_draw = rng.random((n_iter, n_hours), dtype=np.float32) < config.dispatchable_forced_outage_prob
    available_capacity_mw += domestic_dispatchable_capacity_mw * (1 - dispatchable_outage_draw * config.dispatchable_outage_severity_fraction)
    del dispatchable_outage_draw

    interconnection_outage_draw = rng.random((n_iter, n_hours), dtype=np.float32) < config.interconnection_forced_outage_prob
    available_capacity_mw += interconnection_capacity_mw * (~interconnection_outage_draw)
    del interconnection_outage_draw

    unserved_mw = demand_mw - available_capacity_mw
    np.clip(unserved_mw, 0, None, out=unserved_mw)
    deficit_hour = unserved_mw > 0

    return {
        "demand_mw": demand_mw,
        "available_capacity_mw": available_capacity_mw,
        "unserved_mw": unserved_mw,
        "deficit_hour": deficit_hour,
        "n_iterations": n_iter,
        "n_hours": n_hours,
        "config": config,
    }
