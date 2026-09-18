"""
generation.py
==============
Level 2 building block: per-technology generation representation
(MASTER PROMPT, Sections 7 and 8).

Distinguishes variable renewable technologies (solar, wind) from
dispatchable ones, and computes EMPIRICAL capacity factors from real
production data where available — this is preferred over assuming
"typical" industry capacity factors, because it is DERIVED from actual
measurements rather than ASSUMED (see Section 30's data-quality ladder).

Fully country-agnostic: takes technology name, capacity and generation
as plain inputs.
"""

from __future__ import annotations
from dataclasses import dataclass


VARIABLE_RENEWABLE_TECHNOLOGIES = {"solar", "wind"}

# Phase 12: the REAL technology taxonomy used by Elering / Statistics
# Estonia — NOT invented. This project has only partially populated
# generation data against this taxonomy so far (see notes below); the
# taxonomy itself is fixed regardless of how much is currently filled in.
TECHNOLOGY_TAXONOMY = [
    "oil_shale",
    "natural_gas",
    "wind",
    "solar",
    "hydro",
    "biomass",
    "waste",
    "other",
]

RENEWABLE_TECHNOLOGIES = {"wind", "solar", "hydro", "biomass", "waste"}
# "waste" classified renewable per common EU statistical convention
# (biodegradable fraction) — flagged here as a convention choice, not
# a universal physical fact; Statistics Estonia's own exact treatment
# of "waste" has not been independently re-confirmed in this project.


@dataclass
class TechnologyGeneration:
    technology: str
    capacity_mw: float | None
    generation_mwh: float
    period_hours: float
    renewable: bool | None = None

    @property
    def is_variable_renewable(self) -> bool:
        return self.technology.lower() in VARIABLE_RENEWABLE_TECHNOLOGIES

    @property
    def capacity_factor(self) -> float | None:
        """
        Empirical capacity factor = actual energy produced / energy that
        WOULD have been produced running at full nameplate capacity for
        the whole period. Returns None if capacity is unknown (never
        silently assume a capacity to force a number out).
        """
        if not self.capacity_mw or self.capacity_mw <= 0:
            return None
        max_possible_mwh = self.capacity_mw * self.period_hours
        if max_possible_mwh == 0:
            return None
        return self.generation_mwh / max_possible_mwh


@dataclass
class TechnologyProfile:
    """
    Phase 16: static parameters for a generation technology — NOT a
    timestep-varying quantity (that's TechnologyGeneration/generation
    output, already above). This is the "what kind of thing is this"
    description used by the dispatch/simulation layer.

    Any field left as None means "not yet sourced" — the simulation
    layer must handle that explicitly (e.g. skip cost-based dispatch
    ordering for a technology with unknown marginal_cost), never
    silently default it to 0.
    """
    technology: str
    capacity_mw: float | None
    availability: float | None       # 0-1, fraction of capacity typically available (planned+forced outages)
    min_output_mw: float | None
    max_output_mw: float | None
    ramp_rate_mw_per_min: float | None
    marginal_cost_eur_per_mwh: float | None
    emissions_factor_tco2_per_mwh: float | None
    renewable: bool | None
    variable: bool                    # True = weather-driven output (wind, solar); False = otherwise
    dispatchable: bool                # True = operator can choose output level within [min,max]


# Phase 17: Estonia's oil shale fleet — REAL figures where sourced,
# explicit None where not (see B_data/sources/oil_shale.md).
# This uses the CURRENT achievable aggregate (matches
# C_configs/estonia.yaml's other_dispatchable, 1568 MW), not the older,
# larger nameplate/design figures which overstate what's actually
# available after EU-directive-driven unit retirements.
ESTONIA_OIL_SHALE_PROFILE = TechnologyProfile(
    technology="oil_shale",
    capacity_mw=1568,          # matches C_configs/estonia.yaml other_dispatchable (bundles oil shale + a few smaller sources)
    availability=None,          # not sourced — real plants have planned maintenance + forced outages, not modelled yet
    min_output_mw=None,         # thermal plants of this type typically can't run near 0% without shutting down, but no confirmed Estonia-specific minimum found
    max_output_mw=1568,
    ramp_rate_mw_per_min=None,  # not sourced
    marginal_cost_eur_per_mwh=None,   # OPEN ITEM — see oil_shale.md, not fabricated
    emissions_factor_tco2_per_mwh=None,  # OPEN ITEM — see oil_shale.md, not fabricated
    renewable=False,
    variable=False,
    dispatchable=True,
)

# Phase 19: solar. REAL capacity (Elering, start 2025) — but note: 2019
# (this project's real hourly dataset year) had essentially negligible
# solar in Estonia (growth was mostly post-2020 — see
# B_data/sources/... and Wikipedia "Solar power in Estonia":
# <0.08% of generation in 2016, 15.21% by 2025). So this profile is
# real and current, but NOT applicable to the 2019 hourly replay.
ESTONIA_SOLAR_PROFILE = TechnologyProfile(
    technology="solar",
    capacity_mw=1210,           # Elering, start of 2025
    availability=None,          # weather-driven; "availability" in the outage sense isn't the limiting factor for solar
    min_output_mw=0,
    max_output_mw=1210,
    ramp_rate_mw_per_min=None,  # not sourced; also not very meaningful for aggregate solar (limited by irradiance, not equipment)
    marginal_cost_eur_per_mwh=0,  # zero fuel cost is a safe, standard assumption for solar PV, not a guess
    emissions_factor_tco2_per_mwh=0,  # zero direct emissions is standard for solar PV operation (excludes lifecycle/manufacturing)
    renewable=True,
    variable=True,
    dispatchable=False,
)

# Phase 20: hydro. Estonia's REAL domestic hydro capacity is genuinely
# tiny — confirmed 7 MW total in 2019 (Statista) — NOT a data gap, a
# real physical fact about Estonia's flat topography. The much larger
# 125 MW Narva Hydroelectric Station is on Russian territory, operated
# by Russia's TGC-1, and is explicitly NOT part of Estonia's domestic
# capacity (see B_data/sources/ and system_definition.md
# Section 3 boundary). Because it's so small, hydro is folded into
# "other_dispatchable" in C_configs/estonia.yaml rather than tracked
# separately — this profile exists for completeness/documentation.
ESTONIA_HYDRO_PROFILE = TechnologyProfile(
    technology="hydro",
    capacity_mw=7,               # Statista, 2019 figure — REAL, confirmed
    availability=None,
    min_output_mw=0,
    max_output_mw=7,
    ramp_rate_mw_per_min=None,
    marginal_cost_eur_per_mwh=0,   # standard assumption: no fuel cost for run-of-river hydro
    emissions_factor_tco2_per_mwh=0,
    renewable=True,
    variable=False,   # small-scale Estonian hydro is mostly run-of-river with limited storage — treated as steady, not weather-variable like wind/solar (a simplification, not a confirmed operational fact)
    dispatchable=True,
)


def summarize_fleet(technologies: list[TechnologyGeneration]) -> dict:
    """
    Aggregate KPIs across a generation fleet for one period:
    total generation, renewable share, and per-technology capacity factors.
    """
    total_generation = sum(t.generation_mwh for t in technologies)
    renewable_generation = sum(
        t.generation_mwh for t in technologies if t.renewable
    )

    capacity_factors = {
        t.technology: t.capacity_factor for t in technologies
    }

    return {
        "total_generation_mwh": total_generation,
        "renewable_generation_mwh": renewable_generation,
        "renewable_share_pct": (
            round(100 * renewable_generation / total_generation, 2)
            if total_generation else None
        ),
        "capacity_factors": capacity_factors,
    }
