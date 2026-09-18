"""
demand.py
=========
Phase 21: Demand(t) as a function of calendar features — hour, day,
month, weekday, season, holidays. Deliberately NOT including
temperature here (that's Phase 22, and needs weather data this project
could not fetch in this environment — see run_demand_model_analysis.py
for the honest explanation).

Country-agnostic: holiday lists are injected, not hard-coded here.
"""

from __future__ import annotations
import pandas as pd


def add_calendar_features(df: pd.DataFrame, timestamp_col: str, holidays: set[pd.Timestamp] | None = None) -> pd.DataFrame:
    """
    Adds hour, day_of_week, month, is_weekend, season, is_holiday
    columns. `holidays` should be a set of dates (normalized to
    midnight) — see ESTONIA_PUBLIC_HOLIDAYS_2019 below for a real
    example.
    """
    df = df.copy()
    ts = pd.to_datetime(df[timestamp_col])

    df["hour"] = ts.dt.hour
    df["day_of_week"] = ts.dt.dayofweek  # 0=Monday
    df["month"] = ts.dt.month
    df["is_weekend"] = df["day_of_week"] >= 5

    def _season(month: int) -> str:
        if month in (12, 1, 2):
            return "winter"
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        return "autumn"

    df["season"] = df["month"].apply(_season)

    if holidays:
        holiday_dates = {pd.Timestamp(h).normalize() for h in holidays}
        # BUGFIX (caught by inspecting output — "Holiday" bucket was always
        # empty): comparing a tz-aware UTC timestamp's normalized date
        # against naive local calendar dates silently matches nothing in
        # pandas (no error). Must convert to LOCAL calendar date first,
        # since holidays are defined in local (Europe/Tallinn) dates.
        if ts.dt.tz is not None:
            local_dates = ts.dt.tz_convert("Europe/Tallinn").dt.normalize().dt.tz_localize(None)
        else:
            local_dates = ts.dt.normalize()
        df["is_holiday"] = local_dates.isin(holiday_dates)
    else:
        df["is_holiday"] = False

    return df


# Estonia's public holidays, 2019 — general public knowledge (national
# holiday calendar), not derived from any of this project's data
# sources. Included here because Phase 21 explicitly asks for holiday
# effects, and Estonia's holiday dates are fixed/well known facts, not
# something requiring the same sourcing rigor as e.g. generation figures.
ESTONIA_PUBLIC_HOLIDAYS_2019 = {
    pd.Timestamp("2019-01-01"),  # New Year's Day
    pd.Timestamp("2019-02-24"),  # Independence Day
    pd.Timestamp("2019-04-19"),  # Good Friday
    pd.Timestamp("2019-04-21"),  # Easter Sunday
    pd.Timestamp("2019-05-01"),  # Spring Day
    pd.Timestamp("2019-06-09"),  # Whit Sunday
    pd.Timestamp("2019-06-23"),  # Victory Day
    pd.Timestamp("2019-06-24"),  # Midsummer Day (Jaanipäev)
    pd.Timestamp("2019-08-20"),  # Day of Restoration of Independence
    pd.Timestamp("2019-12-24"),  # Christmas Eve
    pd.Timestamp("2019-12-25"),  # Christmas Day
    pd.Timestamp("2019-12-26"),  # Boxing Day
}


def demand_profile_summary(df: pd.DataFrame, demand_col: str) -> dict:
    """Average demand by hour-of-day, day-of-week, month, and
    holiday/non-holiday — the core Phase 21 deliverable."""
    return {
        "by_hour": df.groupby("hour")[demand_col].mean().to_dict(),
        "by_day_of_week": df.groupby("day_of_week")[demand_col].mean().to_dict(),
        "by_month": df.groupby("month")[demand_col].mean().to_dict(),
        "by_season": df.groupby("season")[demand_col].mean().to_dict(),
        "weekday_vs_weekend": df.groupby("is_weekend")[demand_col].mean().to_dict(),
        "holiday_vs_normal": df.groupby("is_holiday")[demand_col].mean().to_dict(),
    }
