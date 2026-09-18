"""
run_weather_correlation_analysis.py
=====================================
Phase 22 (demand vs temperature) and Phase 18 (wind speed vs wind
generation), done PROPERLY now with real ERA5 data — closing the gap
flagged in run_demand_model_analysis.py (which used season as a weak
proxy because this data wasn't available yet).

Timezone note: the ERA5 weather export shows NO DST transition days
(every day has exactly 24 hours) — unlike the real Elering archive,
which does. This means the weather 'time' column is UTC, not
DST-aware Tallinn local time (despite the file's metadata mentioning
Europe/Tallinn — that describes the grid point's location, not
necessarily the timestamp convention used for the export). Merged
directly against Elering's timestamp_utc on that basis.
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent


def main():
    elering = pd.read_csv(ROOT / "B_data" / "processed" / "estonia_hourly_2019.csv", parse_dates=["timestamp_utc"])
    weather_tallinn = pd.read_csv(ROOT / "B_data" / "processed" / "weather_tallinn_2015_2025.csv", parse_dates=["time"])
    weather_national = pd.read_csv(ROOT / "B_data" / "processed" / "weather_national_average_2015_2025.csv", parse_dates=["time"])

    weather_tallinn_2019 = weather_tallinn[weather_tallinn["time"].dt.year == 2019].copy()
    weather_national_2019 = weather_national[weather_national["time"].dt.year == 2019].copy()
    weather_tallinn_2019["time"] = weather_tallinn_2019["time"].dt.tz_localize("UTC")
    weather_national_2019["time"] = weather_national_2019["time"].dt.tz_localize("UTC")

    df = elering.merge(weather_tallinn_2019, left_on="timestamp_utc", right_on="time", how="inner")
    df = df.merge(weather_national_2019[["time", "wind_speed_100m_ms"]].rename(columns={"wind_speed_100m_ms": "wind_speed_national_ms"}),
                  on="time", how="inner")

    print(f"Merged rows: {len(df)} / 8760 real 2019 hours")

    # === Phase 22: demand vs temperature ===
    print("\n=== Phase 22: Demand vs Temperature (REAL ERA5 data, 2019) ===")
    corr = df["demand_mw"].corr(df["temperature_c"])
    print(f"Correlation (demand_mw, temperature_c): {corr:.3f}")

    slope, intercept = np.polyfit(df["temperature_c"], df["demand_mw"], 1)
    print(f"Linear fit: demand_mw = {slope:.2f} * temperature_c + {intercept:.1f}")
    print(f"-> Each 1°C colder is associated with {-slope:.1f} MW MORE demand on average (real 2019 data).")

    # Heating-degree-day style check: demand at very cold vs very mild hours
    cold = df[df["temperature_c"] < -10]
    mild = df[df["temperature_c"] > 15]
    print(f"\nAvg demand when temperature < -10°C (n={len(cold)}): {cold['demand_mw'].mean():.1f} MW")
    print(f"Avg demand when temperature > 15°C (n={len(mild)}): {mild['demand_mw'].mean():.1f} MW")
    print(f"-> {100*(cold['demand_mw'].mean()-mild['demand_mw'].mean())/mild['demand_mw'].mean():.1f}% higher demand in cold vs mild hours — "
          f"a REAL temperature regression now, not just the seasonal proxy used before.")

    # === Phase 18: wind speed vs wind generation ===
    print("\n=== Phase 18: Wind speed (100m, national avg) vs Wind generation (REAL, 2019) ===")
    corr_wind = df["wind_generation_mw"].corr(df["wind_speed_national_ms"])
    print(f"Correlation (wind_generation_mw, wind_speed_100m_ms): {corr_wind:.3f}")

    # Empirical power curve: bin real wind speed, show real average generation per bin
    bins = [0, 3, 5, 7, 9, 11, 13, 15, 20, 30]
    df["wind_speed_bin"] = pd.cut(df["wind_speed_national_ms"], bins=bins)
    curve = df.groupby("wind_speed_bin", observed=True)["wind_generation_mw"].agg(["mean", "count"])
    print("\nEmpirical power curve (real wind speed bin -> real average generation):")
    print(curve.to_string())

    print(
        "\nThis is a REAL empirical relationship derived from actual 2019 Estonia "
        "data — not the generic textbook curve in renewable_physical.py. It could "
        "now be used to calibrate that module's cut-in/rated speed parameters for "
        "Estonia specifically, though note this reflects Estonia's AGGREGATE wind "
        "fleet (many turbines with mixed specs/locations), not one turbine's curve."
    )

    print("\n=== Phase 19: Solar — still not calibrated ===")
    print(
        "Real shortwave/direct/diffuse irradiance IS now available (see "
        "weather_national_average_2015_2025.csv), but 2019 had ~0 real solar "
        "generation in Estonia (Phase 19 finding), so there is still no real "
        "generation series to calibrate the PV model against for that year. "
        "A future pass could attempt this against 2023-2025 if hourly (not "
        "just quarterly) solar generation is ever obtained."
    )


if __name__ == "__main__":
    main()
