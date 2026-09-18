# Source: ENTSO-E

Third source — independent cross-check, not primary. See
`docs/data_discovery_estonia.md` Section 1.5.

## What it publishes

Estonia is a full ENTSO-E member (confirmed directly by Elering:
"Estonia is a member of the European Network of Transmission System
Operators for Electricity"). The Transparency Platform
(`transparency.entsoe.eu`) provides, per country:

- Load (demand)
- Generation by type
- Cross-border physical flows
- Installed capacity
- Day-ahead forecasts
- Transmission data
- Day-ahead / balancing prices

At hourly, monthly and yearly resolution.

## Role in this project

Independent verification against Elering, since ENTSO-E aggregates
TSO-submitted data through a separate reporting pipeline with its own
quality checks — a genuine second opinion, unlike Statistics Estonia's
KE21 (which is partly Elering-sourced since 2023).

## Open items

- Estonia's exact reporting start date on the platform not yet
  confirmed (Baltic states joined ENTSO-E relatively recently in
  historical terms — full synchronisation with Continental Europe only
  completed February 2025 — so the depth of usable historical data may
  be shallower than the platform's theoretical maximum range for
  longer-established Western European members).
- Full list of usable endpoints/API not yet enumerated — this project
  has only confirmed that the platform and categories exist, not
  queried it directly yet.
