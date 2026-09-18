# Assumptions ledger

Every value in this project is REAL, DERIVED, ESTIMATED, or ASSUMED
(see `data_taxonomy.md`). This document is the structured, numbered
index of every ASSUMED value — each one already lives, documented,
next to the code that uses it; this is for finding them quickly, not
a new source of truth. If this file and the code ever disagree, the
code comment is authoritative.

Format: each assumption gets a stable ID (`ASSUMPTION-NNN`), so it can
be cited/referenced elsewhere without ambiguity.

---

### ASSUMPTION-001
**Parameter:** Oil shale marginal generation cost
**Value:** 40 EUR/MWh
**Reason:** No confirmed current Estonian figure was found (see
`B_data/sources/oil_shale.md`); this is an illustrative order-of-
magnitude figure used to demonstrate the economic dispatch mechanism.
**Source:** None — not sourced, deliberately flagged rather than guessed with false precision.
**Confidence:** LOW
**Where used:** `A_engine/optimization/economic_dispatch.py`, `capacity_expansion.py`

### ASSUMPTION-002
**Parameter:** Import price
**Value:** 60 EUR/MWh
**Reason:** No real Nord Pool price series has been ingested into this project.
**Source:** None.
**Confidence:** LOW
**Where used:** same files as ASSUMPTION-001

### ASSUMPTION-003
**Parameter:** Export price
**Value:** 55 EUR/MWh (below import price — a documented simplification)
**Reason:** Illustrative only; real markets can have export price exceed import price at times.
**Source:** None.
**Confidence:** LOW
**Where used:** `economic_dispatch.py`

### ASSUMPTION-004
**Parameter:** Wind overnight capital cost
**Value:** 1,300,000 EUR/MW
**Reason:** Generic industry benchmark figure, needed to stop the
capacity-optimization sweep from favouring infinite free-fuel
renewable overbuild (a real bug this project found and fixed — see
`docs/limitations.md`).
**Source:** General industry knowledge, not an Estonia-specific quote.
**Confidence:** MEDIUM
**Where used:** `capacity_expansion.py`

### ASSUMPTION-005
**Parameter:** Solar overnight capital cost
**Value:** 700,000 EUR/MW
**Reason:** Same as ASSUMPTION-004.
**Source:** General industry knowledge.
**Confidence:** MEDIUM
**Where used:** `capacity_expansion.py`

### ASSUMPTION-006
**Parameter:** Storage overnight capital cost
**Value:** 300,000 EUR/MWh
**Reason:** Same as ASSUMPTION-004.
**Source:** General industry knowledge.
**Confidence:** MEDIUM
**Where used:** `capacity_expansion.py`

### ASSUMPTION-007
**Parameter:** Discount rate for capital recovery
**Value:** 5%
**Reason:** Standard illustrative rate for an infrastructure capital recovery factor calculation.
**Source:** None — generic.
**Confidence:** LOW
**Where used:** `capacity_expansion.py`

### ASSUMPTION-008
**Parameter:** Battery duration ratio (power = energy / 4)
**Value:** 4 hours
**Reason:** Common real-world grid-battery duration class, used as a default when only energy capacity is specified.
**Source:** General industry pattern.
**Confidence:** MEDIUM
**Where used:** `capacity_expansion.py`

### ASSUMPTION-009
**Parameter:** 110kV overhead line reactance
**Value:** 0.4 ohm/km
**Reason:** Standard textbook range (0.35-0.45) for this voltage class; OSM gives geometry, not electrical parameters.
**Source:** General power-systems textbook knowledge, not Estonian line data.
**Confidence:** MEDIUM
**Where used:** `A_engine/power_flow/dc_power_flow.py`

### ASSUMPTION-010
**Parameter:** 330kV overhead line reactance
**Value:** 0.3 ohm/km
**Reason:** Standard textbook range (0.28-0.32) for this voltage class.
**Source:** General power-systems textbook knowledge.
**Confidence:** MEDIUM
**Where used:** `dc_power_flow.py`

### ASSUMPTION-011
**Parameter:** 110kV line thermal limit
**Value:** 150 MW
**Reason:** Typical single-circuit overhead thermal rating for this voltage class.
**Source:** General power-systems textbook knowledge.
**Confidence:** MEDIUM
**Where used:** `dc_power_flow.py`

### ASSUMPTION-012
**Parameter:** 330kV line thermal limit
**Value:** 600 MW
**Reason:** Typical single-circuit overhead thermal rating for this voltage class.
**Source:** General power-systems textbook knowledge.
**Confidence:** MEDIUM
**Where used:** `dc_power_flow.py`

### ASSUMPTION-013
**Parameter:** Cascading-failure trip threshold
**Value:** 20% over the assumed thermal limit
**Reason:** Illustrative protection-relay setting; real Estonian relay settings are not public.
**Source:** None.
**Confidence:** LOW
**Where used:** `A_engine/power_flow/cascading_failure.py`

### ASSUMPTION-014
**Parameter:** Monte Carlo demand random standard deviation
**Value:** 5% (default), 10% (stress scenarios)
**Reason:** Illustrative, round values for a sensitivity distribution — not fitted to real Estonian demand forecast-error statistics.
**Source:** None.
**Confidence:** LOW
**Where used:** `A_engine/simulation/monte_carlo.py`

### ASSUMPTION-015
**Parameter:** Dispatchable-fleet forced outage probability
**Value:** 3% per hour (default), 30% (stress scenarios)
**Reason:** Illustrative, not a measured Estonian generator forced-outage rate.
**Source:** None.
**Confidence:** LOW
**Where used:** `monte_carlo.py`

### ASSUMPTION-016
**Parameter:** Outage severity (capacity reduction when in outage)
**Value:** 20% (default), 80% (stress scenarios)
**Reason:** Illustrative.
**Source:** None.
**Confidence:** LOW
**Where used:** `monte_carlo.py`

### ASSUMPTION-017
**Parameter:** Interconnection forced outage probability
**Value:** 1% per hour (default), 20% (stress scenarios)
**Reason:** Illustrative — the one REAL interconnection outage this project uses (Estlink 2, Dec 2024) is handled separately as a deterministic historical replay, not through this probability.
**Source:** None.
**Confidence:** LOW
**Where used:** `monte_carlo.py`

### ASSUMPTION-018
**Parameter:** Blackout classification threshold
**Value:** Unserved energy > 1% of demand
**Reason:** A round, defensible threshold to distinguish "deficit" from "blackout-scale" — not an official Estonian regulatory definition.
**Source:** None (Elering's own official definition is the 10% reserve-margin rule — see `C_configs/estonia.yaml` — which is REAL, not this threshold).
**Confidence:** LOW
**Where used:** `A_engine/models/system_status.py`

### ASSUMPTION-019
**Parameter:** Untagged OSM line voltage (credible network only)
**Value:** 110 kV
**Reason:** Needed to include otherwise-excluded line segments when building the fully-connected "credible" network at the project owner's request; only 8/129 untagged lines were confirmed Elering-operated, so this is a genuine assumption, not a well-supported inference.
**Source:** None — explicitly checked and found weak (see `ingest_osm_network_credible.py`).
**Confidence:** LOW
**Where used:** `ingest_osm_network_credible.py`

### ASSUMPTION-020
**Parameter:** Substation-to-line-graph snap tolerance
**Value:** 3 km (real-only network), 15 km (credible network)
**Reason:** A bounded radius to account for OSM substation points not landing exactly on line endpoints.
**Source:** None — chosen empirically after the naive 3km/real-only pass left many substations unmatched.
**Confidence:** LOW
**Where used:** `ingest_osm_network.py`, `ingest_osm_network_credible.py`

### ASSUMPTION-021
**Parameter:** Synthetic connectivity-fix edges (credible network only)
**Value:** 93 of 286 lines, nearest-neighbor, no real geometric basis
**Reason:** Explicit project-owner instruction to make the network fully connected for simulation purposes even where real OSM data doesn't support it.
**Source:** None — always tagged `connection_type="synthetic_nearest_neighbor"`.
**Confidence:** LOW (by construction — not meant to represent anything real)
**Where used:** `ingest_osm_network_credible.py`

### ASSUMPTION-022
**Parameter:** ERA5 weather timestamp timezone
**Value:** UTC
**Reason:** Inferred from the absence of any 23/25-hour DST transition day in the data (unlike the real Elering archive, which has them) — not confirmed directly against Open-Meteo's export documentation.
**Source:** Indirect inference from the data itself.
**Confidence:** MEDIUM
**Where used:** `run_weather_correlation_analysis.py`, `A_engine/optimization/capacity_expansion.py`

---

## Open items — real values sought, not found, deliberately left `None`

| Parameter | Status | Where |
|---|---|---|
| Oil shale marginal cost (real, current) | Not found with confidence | `B_data/sources/oil_shale.md` |
| Oil shale emissions factor (tCO2/MWh) | Not found with confidence | same |
| Latvia total interconnection NTC | Only the +600MW 2020 increment confirmed | `B_data/metadata/data_catalogue.csv` |
| Statistics Estonia KE21 2024 annual figure | Not retrieved — interactive query tool, not fetchable | `docs/cross_validation.md` |
| ENTSO-E 2024 annual Estonia load | Not retrieved — same reason | `docs/cross_validation.md` |

Never treat an item in the "open items" table as 0 or as any other
silent default — code that needs these values leaves them `None` and
requires the caller to handle that explicitly.
