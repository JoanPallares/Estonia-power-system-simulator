# A_engine/optimization/

Economic dispatch (`economic_dispatch.py`, single-hour LP via
scipy.optimize.linprog) and capacity expansion screening
(`capacity_expansion.py`, fast heuristic evaluation of thousands of
capacity plans against the real 8,760-hour 2019 shape).

## What's real vs assumed

- **Real**: demand and wind shapes (Elering 2019 archive); solar shape
  (generic PV model over real ERA5 irradiance, uncalibrated — see
  `limitations.md`).
- **Assumed**: every EUR/MWh and EUR/MW figure — oil shale cost, import/
  export prices, annualized capital costs (`assumptions.md`).

## Why two different tools, not one

`economic_dispatch.py` solves a real LP per hour — correct, but too
slow to run for thousands of capacity plans x 8,760 hours each.
`capacity_expansion.py` trades LP-optimality for speed (a greedy
hourly heuristic) specifically to make the Phase 44-45 sweep (3,000+
plans in ~30 seconds) tractable. Neither is a substitute for the other;
see each module's docstring for exactly what it does and doesn't model.

See `run_economic_dispatch_demo.py` and
`run_capacity_optimization_sweep.py` for runnable examples.
