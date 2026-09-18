# Network data findings — Phase 36

## UPDATE: real data obtained (see below) — this section kept for the record

## What's confirmed (aggregate stats only, already in the project)

From Elering directly (`elering.ee/en/electricity-transmission-system`):
5,198 km overhead lines, 284 km cable, 158 substations, 330 kV backbone,
110 kV regional network. These are AGGREGATE counts, not a usable list
of individual substations/lines with coordinates.

## e-Gridmap — re-confirmed, still no bulk export

Elering's e-Gridmap (relaunched 29 Aug 2025) is confirmed to be an
**interactive connection-cost calculator**, built for prospective grid
connection applicants — not a public open-data export. No GeoJSON/CSV
bulk download was found.

## OpenStreetMap — RESOLVED: real data obtained

This sandbox's own network couldn't reach OSM/Geofabrik (confirmed by
actually running `earth-osm` here and watching it fail on the download
step). **The project owner ran the extraction on his own machine and
uploaded the results**: `estonia_substation.geojson` (2,233 features)
and `estonia_line.geojson` (1,973 features), now stored in
`B_data/raw/osm/`.

### What was actually built from this data (see ingest_osm_network.py)

- Filtered to >=110kV (matching Elering's own "330kV backbone + 110kV
  regional" description) — 160 raw substation records, deduplicated to
  **155** (OSM maps some substations as both a Point AND a Polygon;
  confirmed 5 such duplicates by name, kept first occurrence).
- 875 raw line segments >=110kV.
- **Real, non-trivial finding**: OSM line segments are geometric
  fragments (one physical corridor split into many "ways" at
  towers/junctions), NOT direct substation-to-substation links. A naive
  endpoint-snap only connected 147/875 segments to two substations. A
  proper fix was built: a networkx graph over segment endpoints, with
  BFS from each substation that stops at (and records) the first other
  substation reached — this correctly reconstructed **161 real
  substation-to-substation adjacencies**, using real path lengths
  summed from the actual fragments traversed.
- Substations successfully matched to the line graph: **153/155**.

### Honest limitation found: the reconstructed network is fragmented

Building the actual `PowerNetwork` (Phase 37) from this data shows **95
separate connected components**, the largest containing only 12 of 155
buses (7.7%). Elering's own network is NOT fragmented in reality — this
reflects **incomplete OSM line-segment coverage/tagging for Estonia**,
not a real characteristic of the grid. Not silently smoothed over or
hidden; documented here and in the network-build script's output.
Possible next steps if this matters for future work: loosen the
voltage/snap-tolerance filters, or obtain official Elering topology
data instead of relying on OSM.

## Practical outcome

Level 3 now has a REAL (if incomplete/fragmented) Estonian transmission
network — 155 real substations with real coordinates, 161 real
reconstructed adjacencies — visualized in Phase 38's map. This is a
categorically different starting point than a toy 3-bus example, even
with the fragmentation caveat.

## OSM data quality caveat, still applies

OSM power-infrastructure data is crowdsourced. Every value derived from
it (substation names, voltages, line lengths, the reconstructed
adjacencies) is classified **DERIVED (third-party, community-sourced)**,
not REAL/official Elering data, per docs/data_taxonomy.md.

