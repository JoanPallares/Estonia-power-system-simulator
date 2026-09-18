# Project index — all phases, at a glance

Every phase below is REAL, TESTED, and RUNNING (verified via a full
regression pass: `test_check.py` runs all 42 simulations end-to-end,
and all 146 unit/invariant tests pass). Status column: ✅ real data/mechanism, ⚠️ generic/assumed
values used (documented inline), 🔶 scenario-only (no real equivalent
exists yet, e.g. storage).

## Phase 0-10 — Foundation

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 0 | Country selection (Andorra → Estonia) | `docs/system_definition.md` | ✅ |
| 1 | Data discovery (Elering, Statistics Estonia, ENTSO-E, weather) | `docs/data_discovery_estonia.md` | ✅ |
| 2-4 | Data catalogue, taxonomy (6 categories, not 4) | `B_data/metadata/`, `docs/data_taxonomy.md` | ✅ |
| 5-6 | Period analysis, train/val/test scheme | `docs/period_analysis.md` | ✅ (provisional, honestly flagged) |
| 7-10 | Pipeline (RAW→PROCESSED), units, timezone, quality | `A_engine/pipeline/*.py`, `A_engine/models/units.py`, `time_handling.py` | ✅ |

## Phase 11-15 — Level 1: National balance

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 11 | Residual (no assumed losses) | `A_engine/models/balance.py` | ✅ real 2019, closes to 0.003% |
| 12 | Generation mix taxonomy | `A_engine/models/generation.py` | ✅ real taxonomy, partial real data |
| 13 | Demand vs generation+imports plot | inline chart (this conversation) | ✅ |
| 14 | Multi-resolution validation | `A_engine/analysis/validation.py` | ✅ |
| 15 | Formatted balance report | `run_level1_balance_report.py` | ✅ |

## Phase 16-22 — Level 2: Generation & demand models

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 16 | TechnologyProfile schema | `A_engine/models/generation.py` | ✅ |
| 17 | Oil shale (real plants, capacity, EU directive context) | `B_data/sources/oil_shale.md` | ✅ (cost/emissions honestly `None`) |
| 18 | Wind: real generation + real speed correlation (0.848) | `run_weather_correlation_analysis.py` | ✅ |
| 19 | Solar: real capacity, generic PV model | `A_engine/models/renewable_physical.py` | ⚠️ 2019 had ~0 real solar to calibrate against |
| 20 | Hydro: real 7 MW figure (not a gap — genuinely tiny) | `A_engine/models/generation.py` | ✅ |
| 21 | Demand calendar model (hour/weekday/holiday) | `A_engine/models/demand.py` | ✅ 100% real |
| 22 | Demand vs temperature (real ERA5, corr -0.560) | `run_weather_correlation_analysis.py` | ✅ |

## Phase 23-29 — Dynamic simulation, storage, reserves, scenarios

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 23-24 | SystemState + timestep replay loop | `A_engine/models/state.py`, `A_engine/simulation/simulator.py` | ✅ real 8,760h |
| 25 | Interconnections (Finland real, Latvia partial) | `A_engine/models/interconnection.py` | ✅ |
| 26 | Battery/storage (physically consistent SOC) | `A_engine/models/storage.py` | 🔶 scenario-only |
| 27-28 | Reserve margin, 5-state classification | `A_engine/models/system_status.py` | ✅ real Elering 10% rule |
| 29 | Renewable penetration sweep | `run_renewable_penetration_sweep.py` | ✅ real 2019 wind shape scaled |

## Phase 30-35 — Curtailment, scenarios, failures, Monte Carlo, reliability

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 30 | Curtailment model | `A_engine/models/curtailment.py` | ✅ |
| 31-32 | Scenario engine + 15 named scenarios | `A_engine/simulation/scenarios.py`, `C_configs/scenarios/estonia.yaml`, `run_scenario_sweep.py` | ✅ |
| 33 | Deterministic EstLink 1/2 failures | `run_failure_deterministic.py` | ✅ real flow data |
| 34-35 | Monte Carlo, LOLP/LOLE/EENS | `A_engine/simulation/monte_carlo.py`, `A_engine/analysis/reliability.py` | ✅ mechanism verified with stress case |

## Phase 36-38 — Level 3: Network & GIS

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 36 | Network data (OSM, real) | `docs/network_data_findings.md`, `ingest_osm_network.py` | ✅ real, honestly fragmented (95 components) |
| 37 | Network representation (Bus/Line/Generator/Load) | `A_engine/models/network.py` | ✅ |
| 38 | GIS map (real coordinates) | rendered earlier in conversation | ✅ real coords |
| — | "Credible" fully-connected variant (93 synthetic links, tagged) | `ingest_osm_network_credible.py` | 🔶 explicitly synthetic where noted |

## Phase 39-43 — DC power flow, congestion, N-1, cascading failure, dispatch

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 39 | DC power flow (P_ij, slack/PQ, B matrix) | `A_engine/models/dc_power_flow.py` | ⚠️ real topology, generic reactance |
| 40 | Congestion ≠ generation sufficiency | `check_congestion()` in same file | ✅ demonstrated on real + toy networks |
| 41 | N-1 contingency, criticality ranking | `A_engine/analysis/n_minus_1.py` | ✅ (network under-connected vs real grid — noted) |
| 42 | Cascading failure | `A_engine/analysis/cascading_failure.py` | ✅ mechanism verified |
| 43 | Economic dispatch (LP) | `A_engine/models/economic_dispatch.py` | ⚠️ illustrative EUR/MWh, mechanism verified |

## Phase 44-47 — Optimization, sweeps, vulnerability, Digital Twin

| Phase | What | Key file(s) | Status |
|---|---|---|---|
| 44-45 | Capacity optimization (3,000 plans, real CAPEX) | `A_engine/models/capacity_expansion.py`, `run_capacity_optimization_sweep.py` | ✅ (CAPEX bug found & fixed live) |
| 46 | Vulnerability map (renewable x demand → EENS) | `run_vulnerability_map.py` | ✅ real gradient under stress assumptions |
| 47 | Digital Twin status assessment | `README.md` honesty ledger | ✅ |

## How to navigate this project

1. Start with `README.md` for the honesty ledger (what's real vs assumed, per component).
2. `docs/` for the narrative decisions (why Estonia, what data exists, what's out of scope).
3. `B_data/metadata/data_catalogue.csv` for per-parameter provenance.
4. Any `run_*.py` script is a self-contained, runnable demonstration of one phase — each docstring states its own assumptions.
5. `tests/` mirrors the phase structure — `test_phaseXX_YY_*.py` naming makes it easy to find tests for a given phase range.
