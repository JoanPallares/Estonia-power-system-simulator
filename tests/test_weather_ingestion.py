"""
Tests for ingest_weather_era5.py
"""
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest_weather_era5 import read_one_year, national_average, COLUMN_RENAME


def make_fake_era5_csv(tmp_path) -> Path:
    lines = [
        "location_id;latitude;longitude;elevation;utc_offset_seconds;timezone;timezone_abbreviation;;;;;",
        "0;59.5;24.75;10.0;10800;Europe/Tallinn;GMT+3;;;;;",
        "1;58.5;26.75;36.0;10800;Europe/Tallinn;GMT+3;;;;;",
        "",
        "location_id;time;temperature_2m (°C);wind_speed_100m (m/s);wind_direction_100m (°);shortwave_radiation (W/m²);direct_radiation (W/m²);diffuse_radiation (W/m²);direct_normal_irradiance (W/m²);precipitation (mm);snowfall (cm);snow_depth (m)",
        "0;2019-01-01T00:00;0.6;15.1;196;0.0;0.0;0.0;0.0;0.40;0.28;",
        "0;2019-01-01T01:00;0.7;13.4;201;0.0;0.0;0.0;0.0;0.60;0.42;",
        "1;2019-01-01T00:00;-1.0;10.0;180;0.0;0.0;0.0;0.0;0.0;0.0;",
        "1;2019-01-01T01:00;-1.5;9.5;180;0.0;0.0;0.0;0.0;0.0;0.0;",
    ]
    path = tmp_path / "fake_era5.csv"
    path.write_text("\n".join(lines))
    return path


def test_read_one_year_parses_correctly(tmp_path):
    path = make_fake_era5_csv(tmp_path)
    df = read_one_year(path)
    assert len(df) == 4
    assert set(df["location_id"].unique()) == {0, 1}
    assert "temperature_c" in df.columns
    assert df.loc[df["location_id"] == 0, "temperature_c"].iloc[0] == 0.6


def test_read_one_year_all_renamed_columns_present(tmp_path):
    path = make_fake_era5_csv(tmp_path)
    df = read_one_year(path)
    for renamed_col in COLUMN_RENAME.values():
        assert renamed_col in df.columns


def test_national_average_averages_across_locations(tmp_path):
    path = make_fake_era5_csv(tmp_path)
    df = read_one_year(path)
    avg = national_average(df)
    # At 2019-01-01 00:00: location 0 = 0.6°C, location 1 = -1.0°C -> avg -0.2
    row = avg[avg["time"] == pd.Timestamp("2019-01-01T00:00")]
    assert row["temperature_c"].iloc[0] == pytest.approx(-0.2)


def test_national_average_drops_location_id_column(tmp_path):
    path = make_fake_era5_csv(tmp_path)
    df = read_one_year(path)
    avg = national_average(df)
    assert "location_id" not in avg.columns
