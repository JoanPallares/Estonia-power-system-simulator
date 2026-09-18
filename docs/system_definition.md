# System definition — Estonia

Phase 0 deliverable. This document defines the **boundary of the model**:
what is inside the system we simulate, what is outside it, and what
crosses the boundary. Nothing in `A_engine/` should represent anything
outside this boundary; nothing inside this boundary should be silently
skipped without being logged here.

This follows MASTER PROMPT Section 33 directly: we are not building an
operational replica of Estonia's grid. We are building a transparent,
documented, simplified model — this file is where "simplified" gets
turned into precise, checkable statements instead of a vague disclaimer.

## 1. System boundary diagram

```
                    ESTONIA
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
   GENERATION        DEMAND        INTERCONNECTIONS
       │                │                │
       │                │         ┌──────┴──────┐
       │                │         │             │
       │                │      FINLAND        LATVIA
       │                │         │             │
       └────────────────┴─────────┴─────────────┘
                         │
                         ▼
                     BALANCE
```

Note: the version of this diagram as originally sketched did not draw an
explicit connector from `DEMAND` down to `BALANCE`. That connector is
added here because it is physically required — the balance identity
(Section 6) is `Generation + Imports - Exports - Demand - Losses =
Balance`, so demand is a necessary input. Treated as a drawing
simplification, not an intentional exclusion. **Flag for confirmation.**

## 2. What is inside the boundary (in scope)

| Block | Contents at this stage | Status |
|---|---|---|
| **Generation** | Aggregate domestic generation (Level 1); per-technology capacity and empirical capacity factors for wind, solar, biomass/biogas/waste (Level 2, partial — Q3 2025 only) | Partial, real data |
| **Demand** | Total national electricity demand (annual, 2024) and the all-time instantaneous peak (5 Feb 2026) | Minimal — no time-varying profile yet |
| **Interconnections** | Two named cross-border links: **Finland** (Estlink 1+2, real MW capacity) and **Latvia** (partial — only the 3rd-interconnection increment is confirmed in MW) | Partial, real data where available |
| **Balance** | The Level 1 identity, computed from the above | Implemented and tested |

## 3. What is explicitly outside the boundary (out of scope for now)

Per Section 33, these are not modelled, not estimated, and not implied
anywhere in the code. If a future data source makes one of these
feasible, it gets added here first, then to the config schema.

- **Any interconnection other than Finland and Latvia.** Estonia has no
  other electrical interconnections at the time of writing (it is not
  connected to Russia operationally since the February 2025
  synchronisation with Continental Europe).
- **Network topology** — buses, substations, individual transmission
  lines, line-level thermal limits. Interconnections are modelled as two
  single aggregate MW limits (import/export), not as a network.
- **Individual generation assets/plants.** "Generation" here means
  national aggregates and, for Level 2, technology-level aggregates
  (all wind farms summed, all solar summed) — not named power plants
  with their own parameters.
- **Frequency, inertia, voltage, protection systems.** This is an energy
  (MW/MWh) model, not an electromagnetic-transient or stability model.
- **Storage.** No utility-scale storage is currently modelled for
  Estonia (see Section 13 of the master prompt — this is a known,
  intentional gap, not an oversight).
- **Dispatch / merit order.** The model does not currently decide *which*
  generator serves demand at each instant — see Section 20.
- **Heat, gas, or any other energy vector.** Electricity only, even
  though Eesti Energia and Estonia's energy system are heavily coupled to
  district heating and gas.
- **Sub-annual demand dynamics.** No daily/weekly/seasonal load profile
  yet (see Section 10) — this is the single largest gap between this
  document's boundary and a working Level 2 simulator, and is tracked
  separately, not silently assumed away.

## 4. What crosses the boundary

Only two things cross the system boundary as drawn:

1. **Imports/exports** through the Finland and Latvia interconnections
   (the only two arrows leaving the `INTERCONNECTIONS` block toward the
   outside world in the fuller picture — Finland and Latvia are outside
   the boundary; only the interconnection capacity that touches them is
   inside).
2. Nothing else. Fuel supply (oil shale, biomass feedstock) is treated as
   unconstrained/always-available at this stage — a simplification, not
   a claim that Estonia's fuel supply chains are outside all real-world
   constraints. Flagged here so it is not forgotten later (e.g. if a
   future scenario wants to model a fuel-supply disruption, this
   boundary would need to be redrawn first).

## 5. Data status summary (see also data_catalogue.csv per country)

- REAL: national demand (annual), installed capacity by technology
  (wind, solar), Finland interconnection capacity, official reserve
  margin rule, Q3-2025 renewable generation by technology.
- DERIVED: domestic generation (2024), computed to close the balance
  identity rather than independently measured.
- ESTIMATED / not yet resolved: import share year-alignment (flagged
  in `B_data/metadata/data_catalogue.csv`), Latvia total
  interconnection capacity (only the +600 MW increment is confirmed).
- SYNTHETIC data now exists within this project: 93 of the 286 lines in
  the "credible" reconstructed network are synthetic nearest-neighbor
  connections with no real geometric basis (see `docs/limitations.md`
  and `ingest_osm_network_credible.py`) — always tagged
  `connection_type="synthetic_nearest_neighbor"`, never silently mixed
  with real OSM-derived data.

## 6. Open questions before Level 2 can be built properly

1. Confirm: should `DEMAND` feed `BALANCE` directly (assumed yes, see
   Section 1 note)?
2. Is a single national demand number sufficient for the next step, or
   is sourcing an hourly/daily demand profile (even for one recent year)
   a blocking prerequisite before building the timestep simulator?
3. Should Latvia be included in Level 2 with only its partial capacity
   figure (600 MW increment), or excluded until a total figure is found?
