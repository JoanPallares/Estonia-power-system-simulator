"""
economic_dispatch.py
======================
Phase 43: economic dispatch as a linear program (scipy.optimize.linprog).

    minimize:   Σ (marginal_cost_i * generation_i) + import_cost * imports
                - export_price * exports + storage_cost * (charge+discharge)
    subject to: generation + imports + discharge
                = demand + exports + charge + losses

*** ALL PRICES BELOW ARE ILLUSTRATIVE ASSUMPTIONS ***
- Oil shale marginal cost: real figure unconfirmed (see
  B_data/sources/oil_shale.md) — uses an illustrative 40 EUR/MWh
  (a commonly-cited order-of-magnitude for oil-shale generation
  including today's CO2 allowance costs, NOT a sourced Estonian figure).
- Import/export price: no real Nord Pool price series has been ingested
  into this project — uses an illustrative flat 60 EUR/MWh.
- Wind/solar/hydro: 0 EUR/MWh (standard assumption, no fuel cost).
This is built to demonstrate the OPTIMIZATION MECHANISM working
correctly on real demand/wind data, not to produce a trustworthy cost
estimate for Estonia.
"""

from __future__ import annotations
from dataclasses import dataclass
from scipy.optimize import linprog

ASSUMED_OIL_SHALE_COST_EUR_MWH = 40.0
ASSUMED_IMPORT_PRICE_EUR_MWH = 60.0
ASSUMED_EXPORT_PRICE_EUR_MWH = 55.0  # slightly below import price - a documented simplification (real markets can have export > import price at times)


@dataclass
class DispatchResult:
    oil_shale_mw: float
    imports_mw: float
    exports_mw: float
    battery_charge_mw: float
    battery_discharge_mw: float
    total_cost_eur_per_h: float
    success: bool
    message: str


def solve_economic_dispatch(
    demand_mw: float,
    wind_mw: float,
    oil_shale_capacity_mw: float,
    interconnection_capacity_mw: float,
    battery_power_mw: float = 0.0,
) -> DispatchResult:
    """
    Decision variables, in order: [oil_shale, imports, exports, charge, discharge]
    Wind is NOT a decision variable — non-dispatchable, fixed at its real
    resource-limited output (Section 8: variable renewables can't be
    dispatched up, only curtailed down, which this simple version doesn't
    model as a separate choice — wind is just consumed in full here).
    """
    c = [
        ASSUMED_OIL_SHALE_COST_EUR_MWH,
        ASSUMED_IMPORT_PRICE_EUR_MWH,
        -ASSUMED_EXPORT_PRICE_EUR_MWH,  # negative cost = revenue
        0.0,  # charging has no direct cost here (efficiency losses ignored for simplicity)
        0.0,
    ]

    # Equality: oil_shale + wind + imports + discharge - exports - charge = demand
    A_eq = [[1, 1, -1, -1, 1]]
    b_eq = [demand_mw - wind_mw]

    bounds = [
        (0, oil_shale_capacity_mw),
        (0, interconnection_capacity_mw),
        (0, interconnection_capacity_mw),
        (0, battery_power_mw),
        (0, battery_power_mw),
    ]

    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

    if not res.success:
        return DispatchResult(0, 0, 0, 0, 0, 0.0, False, res.message)

    oil_shale, imports, exports, charge, discharge = res.x
    return DispatchResult(
        oil_shale_mw=round(oil_shale, 2), imports_mw=round(imports, 2),
        exports_mw=round(exports, 2), battery_charge_mw=round(charge, 2),
        battery_discharge_mw=round(discharge, 2),
        total_cost_eur_per_h=round(res.fun, 2), success=True, message="optimal",
    )
