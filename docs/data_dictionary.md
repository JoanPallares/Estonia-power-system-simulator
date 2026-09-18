# Data dictionary — Estonia

Defines every variable name used across `B_data/`, `C_configs/estonia.yaml`
and the engine, in one place, so a name always means the same thing.

| Variable | Definition | Unit | Canonical in |
|---|---|---|---|
| `demand_mwh` | Total national electricity demand for the period, including network losses | MWh | Level 1 balance schema (`A_engine/models/schema.py`) |
| `domestic_generation_mwh` | Total electricity generated within Estonia for the period, all technologies combined | MWh | Level 1 balance schema |
| `imports_mwh` | Electricity imported across all interconnections combined (not yet split by Finland/Latvia at this resolution) | MWh | Level 1 balance schema |
| `exports_mwh` | Electricity exported across all interconnections combined | MWh | Level 1 balance schema |
| `losses_mwh` | Transmission + distribution losses for the period | MWh | Level 1 balance schema |
| `data_quality` | One of the six categories in `docs/data_taxonomy.md` | categorical | Level 1 balance schema |
| `capacity_mw` | Installed nameplate capacity for one technology | MW | `C_configs/estonia.yaml`, `A_engine/models/generation.py` |
| `generation_mwh` (per technology) | Energy actually produced by one technology over a stated period | MWh | `generation_by_technology_quarterly.csv`, `generation.py` |
| `capacity_factor` | `generation_mwh / (capacity_mw * period_hours)` — empirical, not assumed | dimensionless (0-1) | `generation.py` |
| `reserve_margin_pct` | `100 * (available_capacity - demand) / demand` | % | `system_status.py` |
| `import_capacity_mw` / `export_capacity_mw` | Maximum interconnection transfer capacity, one direction each | MW | `C_configs/estonia.yaml` |
| `peak_demand_mw` | Single highest recorded instantaneous demand | MW | `C_configs/estonia.yaml` |

## Hourly real-data variables (2019 archive, `estonia_hourly_2019.csv`)

| Variable | Definition | Unit | Notes |
|---|---|---|---|
| `demand_mw` | Real hourly SCADA-measured consumption | MW | Measured |
| `generation_mw` | Real hourly SCADA-measured total domestic generation | MW | Measured |
| `wind_generation_mw` | Real hourly wind generation (only technology disaggregated in this file) | MW | Measured |
| `imports_mw` / `exports_mw` | Netted from 3 real physical flow columns (EE-FI/RU/LV) | MW | Derived |
| `timestamp_utc` | Always UTC past the ingestion stage — see `time_handling.py` | ISO8601 | Never naive |

## Weather variables (ERA5/Open-Meteo, `weather_*_2015_2025.csv`)

| Variable | Definition | Unit | Data quality |
|---|---|---|---|
| `temperature_c` | 2m air temperature | °C | DERIVED/ESTIMATED (reanalysis, not station measurement) |
| `wind_speed_100m_ms` | Wind speed at 100m (turbine hub height) | m/s | DERIVED/ESTIMATED |
| `shortwave_radiation_wm2` / `direct_radiation_wm2` / `diffuse_radiation_wm2` / `dni_wm2` | Solar irradiance components | W/m² | DERIVED/ESTIMATED |
| `precipitation_mm` / `snowfall_cm` / `snow_depth_m` | Hydrological variables | mm / cm / m | DERIVED/ESTIMATED |

## Network variables (OSM-derived, `A_engine/models/network.py`)

| Variable | Definition | Unit | Data quality |
|---|---|---|---|
| `voltage_kv` | Bus or line voltage class | kV | Real (OSM tag) or ASSUMED (110kV default for untagged lines in the CREDIBLE version only) |
| `length_km` | Real line length (real files) or great-circle synthetic distance (CREDIBLE-only synthetic connections) | km | See `connection_type` |
| `connection_type` | `"osm_derived"` or `"synthetic_nearest_neighbor"` — CREDIBLE network only | categorical | Always check this before treating a line as real |
| `thermal_limit_mw` / line reactance (`X_pu`) | Assumed from generic textbook values by voltage class | MW / p.u. | ASSUMED — see `dc_power_flow.py` |

## Reliability variables (`A_engine/analysis/reliability.py`)

| Variable | Definition | Unit |
|---|---|---|
| `LOLP` | Loss of Load Probability — fraction of (iteration, hour) pairs with unserved energy | dimensionless (0-1) |
| `LOLE_hours_per_year` | Expected hours per year with unserved energy | hours |
| `EENS_mwh_per_year` | Expected Energy Not Served per year | MWh |
| `unserved_energy_mw` | Demand that could not be met at a given timestep | MW |
| `curtailment_mw` | Renewable output available but not used | MW |

## Naming conventions

- All energy totals: `<name>_mwh`. All power/capacity: `<name>_mw`. Never
  mix the two without the unit in the name — this is enforced in
  `A_engine/models/units.py` (Phase 8).
- Per-technology data always carries an explicit `technology` column/key
  (e.g. `"wind"`, `"solar"`, `"other_dispatchable"`) — never a
  positional convention (e.g. "column 3 is always wind").
- Timestamps: see `A_engine/models/time_handling.py` (Phase 9) for the
  canonical timezone-handling rules. No variable in this project stores
  a naive (timezone-unaware) timestamp once past the raw-ingestion stage.
