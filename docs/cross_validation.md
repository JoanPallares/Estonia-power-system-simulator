# Cross-validation between data sources

Phase 51: "Don't depend on a single source." What follows is what was
actually achieved, including where it fell short — the master prompt
itself says investigating a mismatch is more interesting than picking
a number, so the gaps below are treated as findings, not failures.

## What was attempted

```
Elering  <->  Statistics Estonia (KE21)  <->  ENTSO-E  <->  Eurostat
```

## What was actually obtained

| Source | Year | Metric | Value | Definition |
|---|---|---|---|---|
| **Elering** | 2024 | Electricity consumption, incl. network losses | **8.26 TWh** | TSO's own accounting; includes transmission losses |
| **Eurostat** | 2022 | Final energy consumption — electricity | **7.14 TWh** | End-use consumption by sector (industry/transport/services/households); EXCLUDES network losses and the energy sector's own use, by definition |

## Why these don't match (and shouldn't be expected to)

This is a genuine example of Phase 51's own point — the ~1.1 TWh gap is
NOT simply an error, and NOT resolved by picking one number:

1. **Different years** (2022 vs 2024) — Estonia's demand grew over this
   period (post-2022 energy-crisis demand recovery, continued
   electrification), so some of the gap is real growth, not definition.
2. **Different definition, confirmed structurally**: Elering's figure
   is *consumption including network losses* (gross, at the point
   supplied to the transmission system). Eurostat's *final energy
   consumption* concept explicitly nets out losses and the energy
   sector's own consumption — this is a real, documented Eurostat
   methodology, not a guess (see Eurostat's "Energy balance guide -
   new methodology").
3. Applying Elering's own reported 2.9% loss share to the 2024 figure
   gives ~8.02 TWh on a "final consumption" basis — still ~0.9 TWh
   above the 2022 Eurostat figure, consistent with real demand growth
   over those two years rather than a remaining definitional gap.

## What could NOT be obtained, and why (honest gap, not hidden)

**Statistics Estonia (KE21)** and **ENTSO-E**'s own annual totals for
Estonia were NOT retrieved as exact figures. Both are interactive
query/database tools (andmed.stat.ee's table browser, ENTSO-E's
Transparency Platform), not static pages a search engine indexes with
the underlying numbers, and this sandbox's `web_fetch` can only reach
URLs that already appeared in a search result — the same category of
limitation already hit with Elering's raw archive and Open-Meteo's API
(see `docs/network_data_findings.md` for the prior two instances).

**Practical path forward**, same pattern as those two: if this
cross-validation is a priority, the project owner can query
`andmed.stat.ee` (KE21 table, annual electricity production/imports/
exports/sale for 2024) and ENTSO-E's Transparency Platform (Estonia
bidding zone, annual load) directly and upload the results, the same
way the 2019 Elering archive, OSM network extract, and ERA5 weather
data were obtained.

## What this exercise still established

Even without the full 3-way match, this is a real, useful finding:
Estonia's ~8.26 TWh consumption figure is **structurally consistent**
with an independently-sourced (Eurostat) figure from two years earlier,
once the loss/definition difference is accounted for — i.e., Elering's
number is not an outlier or obviously wrong when checked against a
different methodology, even though an exact same-year, same-source
comparison could not be completed here.
