# Reliability methodology

How this project computes LOLP, LOLE, and EENS — see
`A_engine/reliability/reliability.py` and `A_engine/simulation/monte_carlo.py`
for the implementation these definitions describe.

## Definitions

- **LOLP** (Loss of Load Probability): fraction of all simulated
  (iteration, hour) pairs where demand exceeds available capacity.
  Dimensionless, 0-1 (reported as %).
- **LOLE** (Loss of Load Expectation): expected number of hours per
  year with a deficit — the per-iteration deficit-hour count, averaged
  across all Monte Carlo iterations.
- **EENS** (Expected Energy Not Served): expected total unserved MWh
  per simulated year — the per-iteration unserved-energy sum, averaged
  across iterations.
- **Reserve violations**: count of (iteration, hour) pairs where the
  reserve margin falls below a threshold (default 10%, matching
  Elering's real Grid Code minimum for Estonia — see
  `C_configs/estonia.yaml`) — a weaker, earlier-warning condition than
  an actual deficit.

## How the Monte Carlo layer produces these

Each iteration randomly draws:
- a demand multiplier (Normal distribution, ASSUMED std dev)
- a dispatchable-capacity outage flag per hour (ASSUMED probability
  and severity)
- an interconnection outage flag per hour (ASSUMED probability)

All of these are illustrative, not sourced Estonian reliability
statistics — see `assumptions.md`. What IS real: the underlying demand
and wind SHAPE the randomness is applied on top of (Estonia's actual
8,760-hour 2019 data).

## What the results mean, and don't mean

Under Estonia's REAL current capacity (dispatchable ~1,568 MW, ~2x its
real 2019 peak demand) and this project's default (non-stress) outage
assumptions, LOLP/LOLE/EENS come out at or near zero — a genuine
finding about Estonia's real capacity margin, not a broken metric. This
was specifically verified with a "stress test" configuration
(artificially reduced capacity, harsher outage rates) that DOES produce
nonzero values, confirming the machinery works correctly (see
`run_monte_carlo_reliability.py`'s own sanity-check section).

The vulnerability map (`run_vulnerability_map.py`, Phase 46) uses the
stress configuration deliberately, for exactly this reason — under real
assumptions the map would be uniformly zero and uninformative.

## Limitations

- Renewable output uses only the real wind shape; solar is generally
  excluded from Monte Carlo runs (2019 had ~0 real Estonian solar — see
  `data_catalogue.csv`).
- No correlation is modelled between simultaneous outages (e.g. a
  demand spike coinciding with low wind) beyond what the real 2019
  hourly shape already encodes for demand-wind correlation.
- This is NOT a substitute for a formal reliability study using real
  Estonian equipment failure-rate statistics, which this project does
  not have access to.
