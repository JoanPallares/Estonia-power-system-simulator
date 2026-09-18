# Source: Elering (Estonia TSO)

Primary source for this project. See `docs/data_discovery_estonia.md`
Section 1.1-1.3 for the full investigation; this file is the
per-source reference summary that `data_catalogue.csv` rows point back to.

## What Elering publishes

1. **Static historical archive** (`elering.ee/en/power-system`) — one
   downloadable xls/xlsx file per year (or year-range) from 2003 to
   2019. Confirmed URLs in `data_catalogue.csv`. Content: system
   consumption, generation, cross-border flows. Resolution: hourly
   (averaged from 5-minute SCADA readings — the 5-minute granularity
   itself is NOT preserved in these files).
2. **Elering Live / dashboard API** (`dashboard.elering.ee`) — covers
   2020-present. Public, no API key required for at least the Nord Pool
   price endpoint (confirmed). Production/consumption endpoint not yet
   confirmed — see the `BLOCKING OPEN ITEM` row in `data_catalogue.csv`.
3. **Web pages / press releases** — point-in-time figures (installed
   capacity, peak demand records, quarterly renewable summaries).
   Already used for `electricity_balance_annual.csv`,
   `generation_by_technology_quarterly.csv`, and `estonia.yaml`.

## Known limitations

- Pre-2010 data has no planned/actual distinction (SCADA only).
- Cross-border flow data uses a different metering system (AMR) than
  domestic consumption/generation (SCADA) — flagged in case the two
  ever need to be reconciled at high time resolution.
- Timezone convention of the archive files is NOT yet confirmed
  (assumed Europe/Tallinn, unverified — see Phase 9).
- No confirmed API endpoint yet for technology-level generation at
  sub-annual resolution beyond the one press-release quarter already
  captured.

## Access notes

No registration/API key required for anything used so far. The static
archive files are direct HTTP downloads. The dashboard API appears to
be genuinely open (confirmed by multiple independent third-party
integrations found during research, e.g. Home Assistant add-ons).
