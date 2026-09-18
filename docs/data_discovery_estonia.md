# Data discovery — Estonia (Phase 1)

No models were written for this phase. This is a findings document only,
per the instruction: investigate first, code later. Structure follows
MASTER PROMPT Section 38.B (dataset / source / resolution / years /
variables / units / accessibility / reliability).

## 1.1 – 1.3 Elering — primary source

### Elering Data Archive (historical, downloadable files)

Confirmed directly from `elering.ee/en/power-system`:

> "The data archive contains all data concerning the Estonian
> electricity system since 2003... Data for 2003–2009 include
> generation and consumption data from the SCADA metering system; data
> measured on cross-border lines come from the commercial metering
> system (AMR). Since 2010, the files have included planned and actual
> data... The SCADA system saves the average measurements of the
> previous 5 minutes to its archive every 5 minutes, the files below
> contain the average of all 5-minute average measurements for each
> hour."

**This confirms, precisely, the resolution chain the master prompt
flagged as important**: raw SCADA = 5-minute averages internally →
archived historical files = hourly averages of those 5-minute values.
The 5-minute granularity is NOT preserved in the downloadable archive
files — only its hourly average is. If true 5-minute or 15-minute
resolution is needed later, it would have to come from a different,
likely non-public, source.

**Directly downloadable files found (year → format → size):**

| Period | Format | Size | URL |
|---|---|---|---|
| 2003–2005 | xls | 2.5 MB | elering.ee/sites/default/files/attachments/2003-2005_Systeemi_tarbimine__eksport__import.xls |
| 2006–2009 | xls | 7.1 MB | elering.ee/sites/default/files/attachments/2006-2009%20Systeemi_tootmine_tarbimine__eksport__import_0.xls |
| 2010–2014 | xls | 8.5 MB | elering.ee/sites/default/files/attachments/2010-2014_archives.xls |
| 2015 | xlsx | 2.5 MB | elering.ee/sites/default/files/attachments/Archive_2015_1.xlsx |
| 2016 | xlsx | 2 MB | elering.ee/sites/default/files/attachments/Archive_2016_1.xlsx |
| 2017 | xlsx | 1.9 MB | elering.ee/sites/default/files/attachments/Archive_2017.xlsx |
| 2018 | xls | 4.5 MB | elering.ee/sites/default/files/attachments/2018_archive.xls |
| 2019 | xls | 4.9 MB | elering.ee/sites/default/files/2020-03/2019_arhiiv_0.xls |
| 2020 onward | — | — | Not a static file. Lives on "Elering Live" (dashboard.elering.ee) |

**Not yet done:** actually opening these files to confirm exact column
names/units. That is the natural first coding step of Phase 2, not
Phase 1 — flagging it here rather than guessing column names.

### Elering Live / dashboard API (2020–present)

- Base: `dashboard.elering.ee`
- Public API, **no key required** for at least some endpoints — confirmed
  working example (third-party, but verifiable): Nord Pool day-ahead
  price endpoint, e.g.
  `https://dashboard.elering.ee/api/nps/price?start=...&end=...`
  and a CSV variant `https://dashboard.elering.ee/api/nps/price/csv?...`
- Full Swagger/OpenAPI documentation exists at
  `dashboard.elering.ee/assets/api-doc.html` (not machine-fetchable from
  here — the page requires a JS-rendered browser — so its full endpoint
  list has NOT been enumerated yet).
- **Not yet confirmed**: the exact endpoint path for production/consumption
  by technology (as opposed to price). This is the single most important
  thing to verify before Phase 2 coding starts, since it is what would
  give us real hourly technology-level generation instead of the one
  quarter we currently have.

## 1.4 Statistics Estonia — validation source

- Table **KE21**: "Electricity production, imports, exports and sale
  (monthly)" — `andmed.stat.ee/en/stat/majandus__energeetika__energia-tarbimine-ja-tootmine__luhiajastatistika/KE21`
- Browsable/exportable via their table tool (PxWeb-style: choose
  variables, then export).
- Confirmed: since 2023, Statistics Estonia's own hydro/wind/solar
  production figures are **sourced from Elering**, not independently
  measured. This matters for validation — KE21 is not a fully
  independent check on Elering for those three technologies from 2023
  onward, only for imports/exports/sales and pre-2023 generation figures.
- Resolution: monthly. Years available: not yet checked, PxWeb tables of
  this type on Statistics Estonia typically go back well over a decade —
  to be confirmed when actually pulling data.

## 1.5 ENTSO-E — third source

- Estonia is a full ENTSO-E member (confirmed directly by Elering:
  "Estonia is a member of the European Network of Transmission System
  Operators for Electricity (ENTSO-E)").
- Platform: `transparency.entsoe.eu` — load, generation by type,
  cross-border flows, installed capacity, forecasts, transmission,
  prices, balancing, all at hourly/monthly/yearly resolution.
- Role in this project: **independent cross-check** against Elering,
  not the primary source (Elering is more granular and is the direct
  system operator).

## 1.6 Meteorology

Three distinct sources found, each with different strengths:

1. **Riigi Ilmateenistus (Estonian Weather Service / Estonian Environment
   Agency)** — `ilmateenistus.ee`. 108 observation stations across
   Estonia. Wind, temperature, hydrology (river/water level, snow cover)
   all present. Quality-checked data downloadable as CSV; raw
   near-real-time data is explicitly flagged as NOT quality-checked on
   the live pages. This is the right source for ground-truth Estonian
   weather.
2. **Baltic Solar Atlas** — joint Estonia/Latvia/Lithuania/Poland
   initiative, based on EUMETSAT CM SAF SARAH satellite data, **covering
   1991–2014 only** (per the source page). This is a real gap: no
   confirmed public satellite irradiance dataset for Estonia was found
   covering the 2015–2026 period the electricity data mostly covers.
   Flagged as an open question, not resolved by assumption.
3. **Open-Meteo** (`open-meteo.com`) — free, no API key, global
   reanalysis-based historical weather including solar radiation (GHI,
   tilted irradiance), wind at multiple heights, 80+ years of coverage.
   Not an Estonia-specific source, but likely the practical answer to
   the 2015–2026 solar-irradiance gap left by the Solar Atlas, since it
   is continuously updated and covers the exact years needed. Would need
   to be clearly labelled as reanalysis/modelled data, not ground
   station measurement, in the data catalogue.

## 1.7 Installed capacity

Already documented in `B_data/metadata/data_catalogue.csv` from
Phase 0 — reconfirmed here, no new figures: ~3,473 MW total net installed
capacity (start 2025), of which 695 MW wind and 1,210 MW solar.

## 1.8 Transmission network

Confirmed directly from `elering.ee/en/electricity-transmission-system`:

- 5,198 km of overhead lines
- 284 km of cable lines
- 158 substations
- Backbone: 330 kV overhead lines; regional distribution: 110 kV
- Cross-border: AC connections to Latvia, DC connections to Finland
  (EstLink 1 + EstLink 2)

**e-Gridmap** (`egle.ee` / linked from Elering) is a public interactive
tool showing substation/line locations and available connection
capacity. It is built for prospective grid-connection applicants
(shows CapEx/ROI for connecting a new plant), not as a bulk open-data
export. **Accessibility limitation, not resolved yet**: no bulk
downloadable topology file (e.g. GeoJSON/shapefile of the network) was
found in this pass — only the interactive map. If Level 3 (network
model) needs actual coordinates/line data, this is the next thing to
investigate, possibly by contacting Elering directly rather than
scraping the map tool.

## Summary table

| Dataset | Source | Resolution | Years | Accessibility | Reliability |
|---|---|---|---|---|---|
| System balance archive | Elering | hourly (avg of 5-min SCADA) | 2003–2019 (static files), 2020+ (API) | Direct download (2003-2019); API, partially unverified (2020+) | High (official TSO) |
| Nord Pool prices | Elering dashboard API | hourly | Not yet checked | Confirmed public, no key | High |
| Production/consumption API | Elering dashboard API | Unknown | Unknown | **Not yet confirmed** | — |
| KE21 (production/imports/exports/sale) | Statistics Estonia | monthly | Not yet checked, likely 10+ years | Public table browser, exportable | High (but partly Elering-sourced since 2023) |
| Load, generation, cross-border, capacity | ENTSO-E | hourly/monthly/yearly | Full ENTSO-E history | Public, transparency platform | High, independent-ish |
| Wind/temperature/hydrology | Riigi Ilmateenistus | station-level, varies | Ongoing | CSV download (quality-checked) | High |
| Solar irradiance (satellite) | Baltic Solar Atlas | — | 1991–2014 only | Public | High but outdated |
| Solar irradiance (reanalysis, gap-filler) | Open-Meteo | hourly | 80+ years, current | Free API, no key | Medium (modelled, not measured) |
| Installed capacity | Elering | point-in-time | start 2025 | Public page | High |
| Transmission network (aggregate stats) | Elering | static description | current | Public page | High |
| Transmission network (topology/coordinates) | e-Gridmap | — | current | Interactive only, **no bulk export found** | — |

## Open items before Phase 2 coding starts

1. Confirm the exact Elering dashboard API endpoint(s) for
   production/consumption by technology (not just price).
2. Open one of the downloadable archive files (e.g. 2019) to confirm
   real column names, units, and whether cross-border flows are split
   by direction (Finland/Latvia, import/export) at that resolution.
3. Decide whether to bridge the 2015–2026 solar irradiance gap with
   Open-Meteo now, or leave weather-driven generation modelling for
   later and continue with Elering's own production figures directly
   (which don't require weather as an intermediate step).
4. Decide whether e-Gridmap's lack of a bulk export blocks Level 3, or
   whether a simplified/aggregate network representation (just the
   already-confirmed voltage tiers and substation count) is enough for
   this project's stated scope (Section 33: simplified, transparent
   model, not an operational replica).
