# Limitations

Brutally honest, on purpose — per the project owner's own framing,
this does not weaken the project, it makes it more scientifically
credible.

- Exact generator dispatch parameters (ramp rates, minimum stable
  output, start-up costs, real marginal costs) are not publicly
  available for Estonia's oil shale fleet. Every cost figure used in
  this project is a generic illustrative assumption (`assumptions.md`).
- Network topology has been simplified and, in the "credible" version,
  partly fabricated for connectivity (93 of 286 lines are synthetic —
  see below). Line electrical parameters (reactance, thermal limits)
  are generic textbook values, not measured Estonian data.
- Failure probabilities (generator outages, interconnection outages,
  demand forecast error) used in the Monte Carlo reliability layer are
  assumed, illustrative values, not derived from real Estonian
  equipment failure-rate statistics.
- Certain transmission parameters are estimated (line reactance) or
  entirely assumed (thermal limits) rather than sourced from Elering.
- This project has only actually ingested and verified **one real year
  (2019)** of hourly data end to end, despite Elering's archive
  theoretically covering 2003-2025 — see `data_strategy.md`.
- Real independent cross-validation (Statistics Estonia, ENTSO-E) could
  not be completed — see `cross_validation.md` for exactly what was and
  wasn't obtained, and why.

A single, honest place listing what this project does NOT do, or does
imperfectly — consolidating notes previously scattered across
`network_data_findings.md`, script docstrings, and inline comments
(those originals stay in place with full detail; this is the index).

## Scope

- **Andorra was removed** (see `A_engine/io/country_registry.py`'s
  docstring). This project is now Estonia-specific; the country
  registry pattern remains as architecture, not as a currently
  multi-country demonstration.
- This is not an operational replica of Elering's grid, not a real
  reliability assessment, and not an investment recommendation (Master
  Prompt Section 33).

## Network (Level 3)

- The OSM-derived real network reconstruction is **honestly fragmented**
  — 95 separate connected components, the largest holding only 12 of
  155 buses. This reflects incomplete OSM line-segment coverage for
  Estonia, not Estonia's real (fully connected) grid.
- A separate **"credible" fully-connected version** exists for
  power-flow/N-1/cascading-failure demonstrations, built at the project
  owner's explicit request. 93 of its 286 lines are **synthetic**
  nearest-neighbor connections with no real geometric basis — always
  tagged `connection_type="synthetic_nearest_neighbor"`, never silently
  mixed with the 193 OSM-derived lines.
- Because the credible network has less redundancy (fewer real loops)
  than Estonia's actual designed grid, **N-1 criticality results
  overstate real fragility** — 107/286 lines "disconnect the network"
  in this reconstruction; a real meshed grid would have far fewer
  single points of failure.
- Line reactance and thermal limits are generic textbook values by
  voltage class, not measured Estonian line parameters (see
  `assumptions.md`).

## Weather / renewables (Level 2)

- Solar generation has **no real hourly calibration for any year** —
  2019 (the only year with real hourly demand/generation) had ~0 real
  Estonian solar output. The PV model (`renewable_physical.py`) is
  generic/uncalibrated, applied to real 2019 irradiance as a best
  available proxy.
- The wind power curve used for capacity-expansion sweeps is the REAL
  empirical Estonia 2019 shape (not the generic textbook curve) — but
  reflects the AGGREGATE fleet, not any single turbine.
- ERA5 weather timestamps are treated as UTC based on the absence of
  DST transition days in the data — inferred, not confirmed by Open-Meteo
  documentation directly.

## Economic dispatch / capacity optimization (Level 3)

- All costs (oil shale, imports, exports, capital costs) are
  **illustrative, generic assumptions**, not sourced Estonian prices —
  see `assumptions.md`.
- The economic dispatch LP uses **flat marginal cost** (not a real
  increasing merit-order curve), which produces a real, documented
  artifact: the optimizer over-generates cheap capacity purely to
  export when export price exceeds generation cost, with no natural
  disincentive. Seen and kept, not hidden, in `economic_dispatch.py`'s
  own test suite.
- The capacity-expansion screening tool uses a fast heuristic (thermal
  dispatch first, then storage, then imports), not a true per-hour
  cost-optimal LP across thousands of plans — a documented tractability
  trade-off (Section 3: avoid unnecessary complexity).

## Reliability (Monte Carlo)

- See `reliability.md` for the full methodology and its limitations —
  in short, all outage probabilities are illustrative assumptions, and
  Estonia's real current capacity makes LOLP/LOLE/EENS come out near
  zero under non-stress assumptions (a real finding, not a bug).

## Data provenance

Every dataset's exact status (REAL / DERIVED / ESTIMATED / ASSUMED /
SYNTHETIC) is tracked per-parameter in `B_data/metadata/data_catalogue.csv`
— this document is a narrative summary, that CSV is the authoritative
per-value record.
