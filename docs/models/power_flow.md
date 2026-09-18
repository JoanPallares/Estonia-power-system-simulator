# A_engine/power_flow/

DC power flow (`dc_power_flow.py`), N-1 contingency analysis
(`n_minus_1.py`), and cascading failure simulation
(`cascading_failure.py`).

## What's real vs assumed

- **Real**: the network topology feeding these modules (155 buses, real
  OSM-derived coordinates and voltages — see `docs/limitations.md` for
  the fragmentation/synthetic-connection caveats).
- **Assumed**: line reactance and thermal limits (generic textbook
  values by voltage class — `assumptions.md`).

## Flow

```
PowerNetwork (A_engine/models/network.py)
    -> run_dc_power_flow()          # theta = B^-1 * P, one slack bus
    -> check_congestion()           # flags lines over their assumed thermal limit
    -> run_n_minus_1_lines()        # remove each line, recheck, rank by criticality
    -> run_cascading_failure()      # iterative: trip -> redistribute -> re-check -> repeat
```

See `run_dc_power_flow_demo.py`, `run_n_minus_1_analysis.py`,
`run_cascading_failure_demo.py` for runnable examples against the real
(credible) Estonia network.
