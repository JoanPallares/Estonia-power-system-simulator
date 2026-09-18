# Period analysis — Estonia

**Status: PROVISIONAL.** Everything in this document is built from what
Elering, Statistics Estonia, ENTSO-E and the weather sources *claim* to
cover (their own published descriptions), not from having actually
opened and inspected the multi-year archive files row by row — that
inspection has not happened yet (see `docs/data_discovery_estonia.md`,
"Open items"). Treat every period below as a **candidate**, to be
confirmed or corrected once Phase 2 pipeline code actually reads a file.

## 1. Per-variable candidate coverage

| Variable | Candidate start | Candidate end | Confidence | Why |
|---|---|---|---|---|
| Demand (consumption) | 2003 | present | Medium | Elering states archive covers 2003+; file not yet opened to confirm no gaps |
| Generation (total) | 2003 | present | Medium | Same archive, same caveat |
| Generation by technology | 2023 (Statistics Estonia says Elering became its source for hydro/wind/solar from 2023) or earlier via Elering directly (unconfirmed) | present | Low-Medium | Only one real quarter (Q3 2025) actually in hand; technology-level granularity across the full 2003-2025 span not confirmed |
| Cross-border flows (Finland, Latvia) | 2003 | present | Medium | Same archive; measured via AMR not SCADA, per Elering's own note — different chain |
| Installed capacity by technology | 2025 (single point-in-time snapshot) | 2025 | High for that one point; **no time series confirmed** | Only "start of 2025" was published in the source used; historical capacity growth not investigated |
| Reserve margin rule (10%) | Current regulation | ongoing | High | It's a rule, not a time series |
| Weather (ground stations) | Unknown per-station | present | Low | Not yet checked |
| Weather (solar, satellite) | 1991 | 2014 | High (for that range) | Confirmed explicitly by the source; does NOT extend to present |
| Network topology (aggregate stats) | current snapshot only | current | High for the snapshot; no history | e-Gridmap has no confirmed bulk export or historical view |

## 2. Implication: different levels need different periods

Following the master prompt's own example format (Section — "this would
be perfectly fine"):

```
LEVEL 1 (national balance):
  Candidate: 2003-2025 (pending file inspection)
  Currently ACTUALLY IN HAND: 2024 only (one annual point)

LEVEL 2 (per-technology dynamics, reserve/status):
  Candidate: 2023-2025 (technology-level generation only confirmed
  reliable from when Statistics Estonia says Elering became its source)
  Currently ACTUALLY IN HAND: Q3 2025 only (one quarter) + one
  instantaneous peak-demand point (5 Feb 2026)

LEVEL 3 (network configuration):
  Candidate: 2025-2026 snapshot only — no historical topology found,
  so there is no "period" for this level in the usual sense, only a
  current-state snapshot, unless e-Gridmap's history (if any) is
  investigated further.
```

**The honest headline finding of this document**: our *candidate*
periods (from source descriptions) are much longer than what is
*actually in hand* right now (one real year for Level 1, one real
quarter for Level 2). Phase 2 coding's first real task is closing that
gap by actually ingesting the archive files — not designing a
calibration scheme for data we don't have yet.

## 3. Train / validation / test — proposed scheme, contingent on Section 1

This cannot be finalised until the archive files are actually opened
(a 2003-2025 series with unknown internal gaps cannot be split
responsibly in advance). The scheme below is the intended *shape* of
the split, to be populated with real boundary years once Section 1 is
resolved:

```
Calibration:   [earliest confirmed clean year] .. [most recent year - 2]
Validation:    [most recent year - 1]  (single held-out year)
Independent test: [most recent complete year]  (never touched during
                   calibration or validation — used once, at the end)
```

Rationale for a single-year validation and single-year test rather than
a larger split: this project's core claim to validate is the Level 1
balance identity and, eventually, Level 2 reserve/status classification
— both are evaluated per-period, so even a modest number of held-out
periods gives a meaningful, honest test, and reserving more years than
that just delays having a usable calibration set given how thin the
*actually in hand* data still is.

**Explicit decision NOT made yet**: exact boundary years. This is
intentional — Section 6 of the master prompt says decide this *after*
investigating the data, and Section 1 above shows that investigation is
still incomplete for the multi-year files.
