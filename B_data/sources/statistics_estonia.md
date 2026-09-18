# Source: Statistics Estonia

Secondary / validation source. See `docs/data_discovery_estonia.md`
Section 1.4.

## What it publishes

**KE21**: "Electricity production, imports, exports and sale (monthly)"
— `andmed.stat.ee/en/stat/majandus__energeetika__energia-tarbimine-ja-tootmine__luhiajastatistika/KE21`.
Browsable/exportable via a PxWeb-style table tool (choose variable →
choose values → show/export data).

## Critical limitation for validation use

Since 2023, Statistics Estonia's own hydro/wind/solar production
figures are sourced **from Elering**, not independently collected. This
means:

- **Before 2023**: KE21 is a genuinely independent cross-check against
  Elering for renewable generation.
- **From 2023 onward**: KE21's renewable columns are not independent —
  a match against Elering proves nothing about data quality, only that
  the republishing pipeline works. Imports/exports/sale figures may
  still be independent (sourced from customs/foreign-trade statistics
  per Statistics Estonia's own methodology page) — not yet confirmed
  which specific columns retain independence past 2023.

## Open items

- Exact years of coverage not yet checked (likely goes back well over
  a decade based on typical PxWeb table conventions, but not confirmed).
- Exact units per column not yet checked.
- Whether imports/exports/sale (as opposed to production) remain
  independently sourced past 2023 — not yet confirmed.
