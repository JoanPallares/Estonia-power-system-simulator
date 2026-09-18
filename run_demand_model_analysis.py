"""
run_demand_model_analysis.py
==============================
Phase 21 (demand vs calendar features) + Phase 22 (demand vs weather),
using the REAL 8760-hour 2019 dataset.

Phase 22 honesty note: this project tried to fetch real Tallinn 2019
temperature data from Open-Meteo's historical archive API to do this
properly (a real regression of demand against temperature). That
failed — the web_fetch tool in this environment only allows URLs that
already appeared in a prior search result, and no search surfaced a
literal, parameterized archive-api.open-meteo.com URL for this
location/date range. Rather than fabricate temperature numbers, this
script uses SEASON (a calendar fact, not weather data) as an honest,
weaker proxy: Estonia's winters are reliably cold and summers reliably
mild, so a strong winter-vs-summer demand gap is suggestive of
heating-driven demand, even without a real temperature regression.
This is evidence, not proof — a real temperature dataset would let a
future pass fit an actual heating-degree-day model.
"""

from pathlib import Path
import pandas as pd

from A_engine.models.demand import add_calendar_features, demand_profile_summary, ESTONIA_PUBLIC_HOLIDAYS_2019

ROOT = Path(__file__).parent


def main():
    raw = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])

    df = add_calendar_features(raw, "timestamp_utc", holidays=ESTONIA_PUBLIC_HOLIDAYS_2019)
    summary = demand_profile_summary(df, "demand_mw")

    print("=== Phase 21: Demand(t) by calendar feature (REAL 2019 hourly data) ===\n")

    print("Average demand by hour of day (MW):")
    for h, v in summary["by_hour"].items():
        bar = "#" * int(v / 20)
        print(f"  {h:02d}:00  {v:7.1f}  {bar}")
    print()

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    print("Average demand by day of week (MW):")
    for d, v in summary["by_day_of_week"].items():
        print(f"  {day_names[d]}: {v:.1f}")
    print()

    print("Weekday vs weekend average demand (MW):")
    for k, v in summary["weekday_vs_weekend"].items():
        label = "Weekend" if k else "Weekday"
        print(f"  {label}: {v:.1f}")
    weekday_avg = summary["weekday_vs_weekend"][False]
    weekend_avg = summary["weekday_vs_weekend"][True]
    print(f"  -> Weekend demand is {100*(weekend_avg-weekday_avg)/weekday_avg:.1f}% {'lower' if weekend_avg < weekday_avg else 'higher'} than weekday")
    print()

    print("Holiday vs normal-day average demand (MW):")
    for k, v in summary["holiday_vs_normal"].items():
        label = "Holiday" if k else "Normal day"
        print(f"  {label}: {v:.1f}")
    print()

    print("=== Phase 22: Season as an honest proxy for temperature (NOT a real regression) ===\n")
    print("Average demand by season (MW):")
    for s in ["winter", "spring", "summer", "autumn"]:
        print(f"  {s.capitalize():<8} {summary['by_season'][s]:.1f}")

    winter = summary["by_season"]["winter"]
    summer = summary["by_season"]["summer"]
    print(f"\nWinter demand is {100*(winter-summer)/summer:.1f}% higher than summer demand.")
    print(
        "This is consistent with 'cold winter -> heating demand -> peak load' "
        "(MASTER PROMPT Phase 22), but it is a SEASONAL correlation, not a "
        "temperature regression. A real heating-degree-day model needs actual "
        "temperature data, which this project could not fetch in this "
        "environment (see module docstring). Treat this finding as suggestive, "
        "not quantitatively calibrated."
    )


if __name__ == "__main__":
    main()
