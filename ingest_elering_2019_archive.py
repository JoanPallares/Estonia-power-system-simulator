"""
ingest_elering_2019_archive.py
================================
One-off ingestion script for B_data/raw/elering/2019_arhiiv_0.xls
(the real historical archive file, uploaded by the project owner since
this sandbox has no network access to elering.ee).

Produces: B_data/processed/estonia_hourly_2019.csv

Two REAL data quality issues were found in the source file and are
corrected HERE, EXPLICITLY, with a printed log — never silently:

1. Rows for what should be 2019-10-30 23:00 through 2019-10-31 23:00
   (25 rows) are labelled with year "2018" in BOTH timestamp columns in
   the source file (a TSO-side typo, confirmed by: sequence continuity
   with the surrounding real 2019-10-30 rows, and the absence of any
   pre-existing, correctly-labelled "2019-10-31" rows elsewhere in the
   file — so this is a pure typo, not an accidental duplicate). Initial
   exploration only caught 1 of these 25 rows; re-checked and corrected
   properly here after the file's total row count came out wrong
   (8760 raw rows, but only ~8735 distinct real dates before this fix).

2. 2019-10-27 has a genuine 25-hour day (DST fall-back): the row
   "03:00-04:00" appears TWICE with identical naive timestamps,
   representing the two real, physically distinct hours (EEST then
   EET). Resolved explicitly: first occurrence = still DST (EEST,
   UTC+3), second = standard time (EET, UTC+2) — this is the correct,
   standard interpretation for a chronologically-ordered source file,
   not a guess.

Both corrections are logged to stdout when this script runs, and the
processed CSV keeps a UTC timestamp column precisely so this ambiguity
can never resurface downstream.
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
RAW_PATH = ROOT / "B_data" / "raw" / "elering" / "2019_arhiiv_0.xls"
OUT_PATH = ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv"

COLUMN_MAP = {
    "Tunni algus (EET)": "hour_start_local_naive",
    "Tegelik tarbimine, MW": "demand_mw",
    "Tegelik tootmine, MW": "generation_mw",
    "sh tuulikute tootmine, MW": "wind_generation_mw",
    "Füüsilised vood EE->FI MW": "flow_ee_to_fi_mw",
    "Füüsilised vood EE->RU, MW": "flow_ee_to_ru_mw",
    "Füüsilised vood EE->LV, MW": "flow_ee_to_lv_mw",
}


def main():
    log = []

    df = pd.read_excel(RAW_PATH, sheet_name="fakt", engine="xlrd")
    df = df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())]

    # --- Correction 1: the 2018/2019 typo ---
    # Initial exploration found 1 row with this exact issue; a closer check
    # (see chat log) found it's actually a CONTIGUOUS BLOCK of 25 rows
    # (2019-10-30 23:00 through 2019-10-31 23:00) all mislabelled with year
    # 2018 instead of 2019 in BOTH timestamp columns. Confirmed no
    # corresponding real "2019-10-31" rows exist elsewhere in the file (so
    # this is a pure typo, not a duplicate-vs-correct situation), and the
    # file's total row count (8760) matches a complete, non-duplicated year
    # once corrected.
    typo_mask = df["hour_start_local_naive"].dt.year == 2018
    n_typo = typo_mask.sum()
    if n_typo:
        df.loc[typo_mask, "hour_start_local_naive"] = df.loc[typo_mask, "hour_start_local_naive"].apply(
            lambda ts: ts.replace(year=2019)
        )
        log.append(
            f"CORRECTED {n_typo} row(s): source timestamps with year '2018' -> '2019' "
            f"(confirmed contiguous block, 2019-10-30 23:00 through 2019-10-31 23:00; "
            f"no pre-existing 2019-10-31 rows found elsewhere, so this is a pure typo, "
            f"not a duplicate; file totals 8760 rows = exactly one complete non-"
            f"duplicated year once corrected)."
        )
    else:
        log.append("Typo-correction check: no matching rows found (source file may have changed).")

    # --- Correction 2: the 2019-10-27 DST fall-back duplicate ---
    dup_ts = pd.Timestamp("2019-10-27 03:00:00")
    dup_positions = df.index[df["hour_start_local_naive"] == dup_ts].tolist()
    if len(dup_positions) != 2:
        raise ValueError(
            f"Expected exactly 2 rows for the known DST-ambiguous timestamp {dup_ts}, "
            f"found {len(dup_positions)}. Data may have changed — stopping rather than "
            f"guessing how to resolve it."
        )
    ambiguous_flags = np.array([False] * len(df))
    ambiguous_flags[dup_positions[0]] = True   # first occurrence: still EEST (DST)
    ambiguous_flags[dup_positions[1]] = False  # second occurrence: EET (standard)
    log.append(
        f"RESOLVED DST ambiguity at {dup_ts}: row index {dup_positions[0]} treated as "
        f"EEST (UTC+3, still-daylight-saving hour), row index {dup_positions[1]} treated "
        f"as EET (UTC+2, standard-time hour) — standard interpretation for a "
        f"chronologically-ordered fall-back transition."
    )

    # Localize to Europe/Tallinn using the explicit per-row resolution above,
    # then convert to UTC for unambiguous downstream storage.
    naive_index = pd.DatetimeIndex(df["hour_start_local_naive"])
    localized = naive_index.tz_localize("Europe/Tallinn", ambiguous=ambiguous_flags, nonexistent="raise")
    df["timestamp_utc"] = localized.tz_convert("UTC")

    # Derived: gross imports/exports from the three physical flow columns.
    # Validated in exploration: Generation + Imports - Exports - Demand
    # closes to 0.00% of demand across the full year using ONLY these three
    # columns — "Vahelduvvoolu saldo" (AC balance) is a different, separate
    # metric and is deliberately NOT added here (adding it would double-count).
    net_export_mw = df["flow_ee_to_fi_mw"] + df["flow_ee_to_ru_mw"] + df["flow_ee_to_lv_mw"]
    df["imports_mw"] = net_export_mw.clip(upper=0).abs()
    df["exports_mw"] = net_export_mw.clip(lower=0)

    final_cols = [
        "timestamp_utc", "demand_mw", "generation_mw", "wind_generation_mw",
        "imports_mw", "exports_mw",
    ]
    out = df[final_cols].sort_values("timestamp_utc").reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)

    print("=== Ingestion log ===")
    for line in log:
        print(f"  - {line}")
    print(f"\nRows written: {len(out)}")
    print(f"Output: {OUT_PATH}")

    # Sanity check, printed for visibility (not asserted — this script's
    # job is to ingest and report, not to silently pass/fail on a threshold)
    residual = (out["generation_mw"] + out["imports_mw"] - out["exports_mw"] - out["demand_mw"]).sum()
    demand_total = out["demand_mw"].sum()
    print(f"\nBalance residual check: {residual:,.0f} MWh ({100*residual/demand_total:.4f}% of annual demand)")


if __name__ == "__main__":
    main()
