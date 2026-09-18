# Data strategy

Short version of `data_discovery_estonia.md` (source-by-source
findings) and `period_analysis.md` (what period each variable actually
covers) — both kept in full detail alongside this file; this is the
navigable summary, not a replacement.

## Sources, by confidence

1. **Elering** (TSO) — primary source. Real hourly archive (2019
   obtained; 2003-2018 and 2020+ theoretically available but not yet
   ingested — see `data_discovery_estonia.md` Section 1.2).
2. **OpenStreetMap** — real network topology (substations, lines),
   crowdsourced, DERIVED not official.
3. **Open-Meteo (ERA5 reanalysis)** — real weather, 2015-2025, 6 grid
   points across Estonia. DERIVED/ESTIMATED (reanalysis, not
   ground-station measurement).
4. **Statistics Estonia (KE21)** — catalogued, not yet ingested;
   NOT independent of Elering for hydro/wind/solar since 2023 (see
   `data_discovery_estonia.md` Section 1.4).
5. **ENTSO-E** — catalogued as an independent cross-check source, not
   yet used as primary.

## What's actually in hand vs what's theoretically available

The single most important finding from `period_analysis.md`: Elering's
own documentation claims 2003-2025 coverage, but this project has only
actually ingested and verified **one real year (2019)** end to end.
Every "REAL" hourly-resolution claim in this project traces back to
that one year, not the full theoretical range.

## Where to look for more detail

- `data_discovery_estonia.md` — full Phase 1 findings, per source.
- `period_analysis.md` — per-variable candidate vs actually-in-hand
  coverage, and the (still-provisional) train/validation/test split
  design.
- `network_data_findings.md` — the OSM network story specifically.
- `data_catalogue.csv` (`B_data/metadata/`) — the authoritative,
  per-parameter provenance record.
