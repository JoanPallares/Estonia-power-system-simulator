# Oil shale — Estonia's defining generation technology

Phase 17. Confirmed via web search (not from the hourly archive, which
doesn't disaggregate technologies beyond wind — see data_catalogue.csv).

## Plants

Historically >95% of Estonia's electricity came from two plants near
Narva, owned/operated by Narva Power (Enefit Power, an Eesti Energia
subsidiary):

| Plant | Design/nameplate capacity | Actual max achievable (all boilers running) | Commissioned |
|---|---|---|---|
| Eesti Power Plant | 1,610 MWe gross design | ~1,355 MW | 1969–1973 (8 blocks) |
| Balti Power Plant | 765 MW (as of end-2005) | ~432 MW | 1959–1965 |
| Auvere Power Plant | 300 MW (single CFB unit) | 300 MW | 2015 |

**Combined historical design capacity: ~2,900 MWe.** The gap between
"design capacity" and "actual achievable" is real and important: many
of the original 1960s-70s pulverised-fuel (PF) units have been retired
or restricted. Per the EU Industrial Emissions Directive 2010/75/EU,
~749 MW of old units that don't meet sulphur emission limits were
restricted to a combined 17,500 operating hours total across 2016-2023
— i.e. a chunk of Estonia's nameplate oil shale capacity was never
meant to run continuously in recent years. **This is why this project's
`C_configs/estonia.yaml` uses an aggregate "other_dispatchable" figure
(1,568 MW, from Elering's own recent total) rather than these older,
larger nameplate numbers — the older figures overstate what's actually
available today.**

## Technology transition (repowering)

Some units have been repowered from pulverised-fuel (PF) to circulating
fluidised bed (CFB) combustion:
- MCR output per repowered unit increases from 170–180 MWe to 215 MWe.
- Efficiency increases from ~30% to ~36.5%.
- SO2 emissions cut ~95%, NOx ~55%, CO2 ~23%, particulates ~97%
  (plant-level, PF→CFB conversion — NOT the same as an absolute
  tCO2/MWh emissions factor, see below).

## Emissions factor — OPEN ITEM, not fabricated

Multiple sources confirm oil shale has a "high specific carbon emission
factor" and that Estonia's power sector is the country's largest CO2
emitter, but **no single, clearly-sourced tCO2/MWh figure was found in
this pass** precise enough to put in `TechnologyProfile.emissions_factor`
without guessing. Left as `null` in code, not estimated. A dedicated
follow-up search (e.g. Estonia's EU ETS reporting, or Elering/Statistics
Estonia's own emissions intensity publications) is needed before this
field can be populated honestly.

## Marginal cost — OPEN ITEM, not fabricated

Not found with a specific, current €/MWh figure in this pass either.
One 2016-era source mentions oil-shale generation subsidy schemes
(14-16 €/MWh depending on CO2 price bracket) but that's a subsidy, not
a marginal generation cost, and it's a decade out of date. Left as
`null`.

## Why this matters for the project

Estonia's declining-but-still-dominant oil shale fleet, alongside its
fast-growing solar/wind, is a genuine energy-transition case study —
per Statistics Estonia (cited in Phase 1), solar went from <0.08% of
generation in 2016 to 15.21% in 2025. This is a much more interesting
transition story than a system with a static generation mix, and part
of why Estonia was chosen as the primary case study over Andorra.
