"""
renewable_physical.py
======================
Phases 18 & 19, second half: the "weather -> physical model -> generation"
architecture, for when real weather data is available.

*** READ THIS: NEITHER FUNCTION IS CALIBRATED TO ESTONIA ***
Both use standard, textbook physical formulas — not fitted to any real
Estonian turbine or PV installation. Estonia has no confirmed public
per-turbine power curve or per-installation PV specification in what
this project has sourced so far (see docs/data_discovery_estonia.md).
Using these functions to produce a number and presenting it as "Estonia's
wind/solar generation" without calibration would violate this project's
own data-honesty principle. They exist so the pipeline SHAPE is ready
the moment real turbine specs / irradiance data / calibration data are
available — not to produce trustworthy numbers today.
"""

from __future__ import annotations


def generic_wind_power_curve(wind_speed_m_s: float, rated_capacity_mw: float,
                              cut_in_m_s: float = 3.0, rated_m_s: float = 12.0,
                              cut_out_m_s: float = 25.0) -> float:
    """
    Textbook simplified turbine power curve (cubic ramp between cut-in
    and rated speed, flat at rated output, zero above cut-out). Default
    speed thresholds (3 / 12 / 25 m/s) are GENERIC INDUSTRY TYPICAL
    VALUES, not Estonia- or turbine-specific — replace with real
    manufacturer data before trusting the output.
    """
    if wind_speed_m_s < cut_in_m_s or wind_speed_m_s >= cut_out_m_s:
        return 0.0
    if wind_speed_m_s >= rated_m_s:
        return rated_capacity_mw
    fraction = ((wind_speed_m_s - cut_in_m_s) / (rated_m_s - cut_in_m_s)) ** 3
    return rated_capacity_mw * fraction


def generic_pv_model(irradiance_w_m2: float, capacity_mw: float,
                      performance_ratio: float = 0.80,
                      reference_irradiance_w_m2: float = 1000.0) -> float:
    """
    Standard linear PV model: output scales with irradiance relative to
    the reference (STC, 1000 W/m2), de-rated by a performance ratio
    (accounts for inverter losses, soiling, temperature — NOT modelled
    individually here). performance_ratio=0.80 is a common generic
    default (typical real-world range ~0.75-0.85), NOT fitted to any
    Estonian installation.
    """
    if irradiance_w_m2 <= 0:
        return 0.0
    return capacity_mw * performance_ratio * min(irradiance_w_m2 / reference_irradiance_w_m2, 1.0)
