"""
ingest_weather_era5.py
========================
Ingests the REAL ERA5-based (Open-Meteo) weather data for Estonia,
2015-2025, uploaded by the project owner (this sandbox couldn't reach
Open-Meteo's API directly — see run_demand_model_analysis.py's earlier
honesty note, now resolved).

File format (Open-Meteo's multi-location CSV export):
  - Rows 0-5: metadata for 6 grid points (location_id, lat, lon, elevation, timezone)
  - Row 6: blank separator
  - Row 7: real column headers for the data block
  - Rows 8+: hourly data, ALL 6 locations concatenated (8760 rows x 6 = 52,560/year)

6 grid points span Estonia: near Tallinn (59.5,24.75), Tartu area
(58.5,26.75), south-central, northeast/Narva (59.5,28.25), southwest/
coast (58.25,22.5), central-south (58.5,25.5).

Classification (docs/data_taxonomy.md): ERA5 reanalysis is DERIVED/
ESTIMATED (a physics-model reconstruction constrained by real
observations), NOT a direct ground-station measurement — never
presented as "measured" in this project.
"""
from pathlib import Path
import pandas as pd


ROOT = Path(__file__).parent

TALLINN_LOCATION_ID = 0


COLUMN_RENAME = {
    "temperature_2m (°C)": "temperature_c",
    "wind_speed_100m (m/s)": "wind_speed_100m_ms",
    "wind_direction_100m (°)": "wind_direction_deg",
    "shortwave_radiation (W/m²)": "shortwave_radiation_wm2",
    "direct_radiation (W/m²)": "direct_radiation_wm2",
    "diffuse_radiation (W/m²)": "diffuse_radiation_wm2",
    "direct_normal_irradiance (W/m²)": "dni_wm2",
    "precipitation (mm)": "precipitation_mm",
    "snowfall (cm)": "snowfall_cm",
    "snow_depth (m)": "snow_depth_m",
}


def read_one_year(path: Path) -> pd.DataFrame:
    """
    Read one Open-Meteo ERA5 CSV export.

    Supports UTF-8-SIG and Latin-1 encodings and normalizes
    common encoding artifacts in column names.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Weather file not found: {path}"
        )

    # ============================================================
    # 1. READ CSV
    # ============================================================

    try:
        raw = pd.read_csv(
            path,
            sep=";",
            encoding="utf-8-sig",
        )
    except UnicodeDecodeError:
        raw = pd.read_csv(
            path,
            sep=";",
            encoding="latin1",
        )

    # ============================================================
    # 2. FIND REAL HEADER
    # ============================================================

    location_column = None

    for column in raw.columns:
        cleaned = (
            str(column)
            .strip()
            .replace("\ufeff", "")
        )

        if cleaned == "location_id":
            location_column = column
            break

    if location_column is None:
        raise KeyError(
            "Could not find 'location_id' in the CSV. "
            f"Columns found: {list(raw.columns)}"
        )

    header_matches = raw.index[
        raw[location_column]
        .astype(str)
        .str.strip()
        == "location_id"
    ]

    if len(header_matches) == 0:
        raise KeyError(
            f"Could not locate the real data header in {path}"
        )

    header_row_idx = header_matches[0]

    # ============================================================
    # 3. REBUILD DATAFRAME
    # ============================================================

    headers = [
        str(value)
        .strip()
        .replace("\ufeff", "")
        for value in raw.iloc[header_row_idx].values
    ]

    data = raw.iloc[
        header_row_idx + 1:
    ].copy()

    data.columns = headers

    # ============================================================
    # 4. NORMALIZE ENCODING ARTIFACTS
    # ============================================================

    normalized_columns = {}

    for column in data.columns:

        normalized = (
            str(column)
            .strip()
            .replace("\ufeff", "")
            .replace("Â°", "°")
            .replace("Â", "")
        )

        normalized_columns[column] = normalized

    data = data.rename(
        columns=normalized_columns
    )

    # ============================================================
    # 5. APPLY PROJECT SCHEMA
    # ============================================================

    data = data.rename(
        columns=COLUMN_RENAME
    )

    # ============================================================
    # 6. CHECK REQUIRED COLUMNS
    # ============================================================

    required_columns = [
        "location_id",
        "time",
        *COLUMN_RENAME.values(),
    ]

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:
        raise KeyError(
            f"Missing required weather columns in "
            f"{path.name}: {missing}\n"
            f"Available columns: {list(data.columns)}"
        )

    # ============================================================
    # 7. NUMERIC CONVERSION
    # ============================================================

    numeric_cols = list(
        COLUMN_RENAME.values()
    )

    for col in numeric_cols:

        data[col] = pd.to_numeric(
            data[col],
            errors="raise",
        )

    data["location_id"] = (
        pd.to_numeric(
            data["location_id"],
            errors="raise",
        )
        .astype(int)
    )

    data["time"] = pd.to_datetime(
        data["time"],
        errors="raise",
    )

    # ============================================================
    # 8. RETURN CLEAN DATA
    # ============================================================

    return data[
        ["location_id", "time"] + numeric_cols
    ].reset_index(drop=True)


def national_average(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Simple unweighted average across the six grid points.
    """

    return (
        data
        .groupby("time")
        .mean(numeric_only=True)
        .drop(columns=["location_id"])
        .reset_index()
    )


def main():

    years = range(2015, 2026)

    all_data = []

    for year in years:

        path = (
            ROOT.parent.parent
            / "mnt"
            / "user-data"
            / "uploads"
            / f"estonia_weather_era5_{year}.csv"
        )

        if not path.exists():

            path = (
                ROOT
                / "B_data"
                / "raw"
                / "weather"
                / f"estonia_weather_era5_{year}.csv"
            )

        data = read_one_year(path)

        all_data.append(data)

        print(
            f"{year}: "
            f"{len(data)} rows "
            f"({data['location_id'].nunique()} locations)"
        )

    # ============================================================
    # COMBINE YEARS
    # ============================================================

    combined = pd.concat(
        all_data,
        ignore_index=True,
    )

    # ============================================================
    # NATIONAL AVERAGE
    # ============================================================

    national = national_average(
        combined
    )

    # ============================================================
    # TALLINN SERIES
    # ============================================================

    tallinn = (
        combined[
            combined["location_id"]
            == TALLINN_LOCATION_ID
        ]
        .drop(columns=["location_id"])
        .reset_index(drop=True)
    )

    # ============================================================
    # WRITE OUTPUTS
    # ============================================================

    out_dir = (
        ROOT
        / "B_data"
        / "processed"
    )

    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    national.to_csv(
        out_dir
        / "weather_national_average_2015_2025.csv",
        index=False,
    )

    tallinn.to_csv(
        out_dir
        / "weather_tallinn_2015_2025.csv",
        index=False,
    )

    print(
        f"\nTotal rows combined "
        f"(all locations, all years): "
        f"{len(combined)}"
    )

    print(
        f"National average series: "
        f"{len(national)} hourly rows"
    )

    print(
        f"Tallinn-only series: "
        f"{len(tallinn)} hourly rows"
    )

    print(
        f"Written to {out_dir}"
    )


if __name__ == "__main__":
    main()