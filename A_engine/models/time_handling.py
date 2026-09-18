"""
time_handling.py
=================
Phase 9: timezone handling.

Estonia's canonical timezone is Europe/Tallinn (EET/UTC+2 standard,
EEST/UTC+3 daylight saving). This module is the ONLY place in the
project that should call `tz_localize` / `tz_convert` — every other
module receives already-localized, unambiguous timestamps.

Never assume a raw file's timestamps are naive-local-time-safe. Always
route them through here, and let the DST edge cases fail loudly rather
than silently dropping or duplicating an hour.
"""

from __future__ import annotations
import pandas as pd

CANONICAL_TIMEZONE = "Europe/Tallinn"


def localize_naive_index(index: pd.DatetimeIndex, tz: str = CANONICAL_TIMEZONE) -> pd.DatetimeIndex:
    """
    Localizes a naive (timezone-unaware) DatetimeIndex to `tz`.

    Raises on ambiguous times (the repeated hour when clocks fall back)
    and nonexistent times (the skipped hour when clocks spring forward)
    rather than silently guessing — MASTER PROMPT Section 9 explicitly
    warns this can break an hourly dataset if not handled correctly.
    Caller must resolve ambiguity explicitly (e.g. by checking against
    a secondary source) rather than this function picking one silently.
    """
    if index.tz is not None:
        raise ValueError(
            "Index is already timezone-aware. Use tz_convert(), not "
            "localize_naive_index(), or you'll get a confusing pandas error."
        )
    return index.tz_localize(tz, ambiguous="raise", nonexistent="raise")


def to_utc(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Converts an already-localized index to UTC — the recommended
    storage format for any processed (non-display) data, since UTC has
    no DST ambiguity at all."""
    if index.tz is None:
        raise ValueError("Index must already be timezone-aware before converting to UTC.")
    return index.tz_convert("UTC")


def detect_dst_transition_days(index: pd.DatetimeIndex) -> dict[str, list]:
    """
    For an hourly, Europe/Tallinn-localized index, identifies the two
    kinds of irregular days the master prompt calls out explicitly:
      - 23-hour days (spring forward, one hour skipped)
      - 25-hour days (fall back, one hour repeated)

    Returns a dict with 'short_days' and 'long_days' (lists of dates).
    This is diagnostic, not corrective — it tells you where to look,
    it does not silently patch anything.
    """
    if index.tz is None:
        raise ValueError("Index must be timezone-aware (Europe/Tallinn) to detect DST transitions.")

    counts = pd.Series(1, index=index).groupby(index.date).sum()
    short_days = counts[counts == 23].index.tolist()
    long_days = counts[counts == 25].index.tolist()
    return {"short_days": short_days, "long_days": long_days}


def validate_hourly_continuity(index: pd.DatetimeIndex) -> dict:
    """
    Phase 10 quality check, timestamp-specific: looks for gaps and
    duplicates in an hourly series, WITHOUT flagging legitimate 23/25
    hour DST days as errors.

    Returns a dict: {gaps: [...], duplicates: [...], dst_days: {...}}.
    Never auto-fills a gap — that decision belongs to a human or an
    explicitly-justified, separately-logged imputation step.
    """
    if index.tz is None:
        raise ValueError("Index must be timezone-aware before validating continuity.")

    dst_days = detect_dst_transition_days(index)
    duplicates = index[index.duplicated()].tolist()

    sorted_index = index.sort_values()
    expected = pd.date_range(sorted_index[0], sorted_index[-1], freq="h", tz=index.tz)
    # Remove the expected hour on short days and don't flag it as missing
    missing = expected.difference(sorted_index)
    short_day_dates = set(dst_days["short_days"])
    gaps = [ts for ts in missing if ts.date() not in short_day_dates]

    return {"gaps": gaps, "duplicates": duplicates, "dst_days": dst_days}
