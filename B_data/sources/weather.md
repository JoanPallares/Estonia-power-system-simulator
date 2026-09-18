# Source: Meteorology (three distinct sources, not one)

See `docs/data_discovery_estonia.md` Section 1.6. Grouped here as one
"weather" source folder in `B_data/raw/weather/`, but they are
NOT interchangeable — kept distinct in the catalogue and in code.

## 1. Riigi Ilmateenistus (Estonian Weather Service)

- `ilmateenistus.ee` — 108 observation stations across Estonia.
- Wind, temperature, hydrology (river/water level, snow cover).
- **Real measured**, ground-station data.
- Quality-checked data downloadable as CSV. Raw near-real-time data on
  the live map pages is explicitly flagged by the source itself as NOT
  quality-checked — only use the CSV downloads for this project.
- Per-station coverage years not yet checked.

## 2. Baltic Solar Atlas

- Joint Estonia/Latvia/Lithuania/Poland initiative.
- Satellite-derived (EUMETSAT CM SAF SARAH dataset), **1991–2014 only**.
- Classified **Estimated**, not Real measured (satellite-derived, not a
  ground-station reading) — per `docs/data_taxonomy.md`.
- Does not cover the 2015–2026 period this project mostly needs. This is
  a real, unresolved gap, not something to paper over.

## 3. Open-Meteo (candidate gap-filler)

- Free, no API key, global reanalysis model, 80+ years of coverage,
  hourly resolution, includes solar irradiance (GHI, tilted irradiance),
  multi-height wind, temperature.
- Classified **Estimated** (modelled reanalysis output, not a
  measurement) if used — must never be silently presented as Real
  measured data.
- Not Estonia-specific, but plausible candidate for the 2015–2026 solar
  gap left by the Solar Atlas. Not yet ingested or tested against
  Estonian ground stations for accuracy.

## Role in this project

Weather is only needed if/when the project moves from "historical
renewable generation as reported by Elering" to "generation modelled
from weather inputs" (Section 8 of the master prompt: intermittency,
correlation between renewable sources). Until that specific modelling
step is undertaken, weather data is catalogued but not a blocking
dependency for Level 1 or the current Level 2 work.

## Open items

- Confirm per-station year coverage at Riigi Ilmateenistus.
- Decide (with the project owner) whether to use Open-Meteo now to
  bridge the solar gap, or defer weather-driven modelling entirely.
- If Open-Meteo is adopted, validate it against at least one Estonian
  ground station before trusting it for anything quantitative.
