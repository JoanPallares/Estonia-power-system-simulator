"""
storage.py
==========
Phase 26 (MASTER PROMPT Section 13): generic battery storage.

Estonia has no significant real utility-scale storage today (see
docs/system_definition.md, Section 3 — explicitly out of scope for the
CURRENT system). This module exists to run "what if Estonia added X GWh
of storage?" experiments (Section 13's own stated goal) — every
capacity/power figure used with it must be clearly labelled as a
SCENARIO input, never presented as real installed storage.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class BatteryConfig:
    energy_capacity_mwh: float
    power_capacity_mw: float
    min_soc_fraction: float = 0.05
    max_soc_fraction: float = 0.95
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95


@dataclass
class BatteryState:
    soc_mwh: float

    def soc_fraction(self, config: BatteryConfig) -> float:
        return self.soc_mwh / config.energy_capacity_mwh


class Battery:
    """
    Physically consistent SOC model (Section 13's own requirement).
    One call to step() per timestep.
    """

    def __init__(self, config: BatteryConfig, initial_soc_fraction: float = 0.5):
        self.config = config
        self.state = BatteryState(soc_mwh=config.energy_capacity_mwh * initial_soc_fraction)

    def step(self, requested_power_mw: float, duration_hours: float) -> float:
        """
        requested_power_mw: positive = charge request, negative = discharge request.
        Returns the ACTUAL power delivered/absorbed (may be less than
        requested if power or SOC limits bind) — the caller (dispatch
        logic) must reconcile this against demand/curtailment itself;
        this function only enforces the battery's own physical limits.
        """
        c = self.config
        min_soc_mwh = c.energy_capacity_mwh * c.min_soc_fraction
        max_soc_mwh = c.energy_capacity_mwh * c.max_soc_fraction

        requested_power_mw = max(-c.power_capacity_mw, min(c.power_capacity_mw, requested_power_mw))

        if requested_power_mw >= 0:
            # Charging: energy INTO the battery is reduced by charge_efficiency
            max_chargeable_mwh = max_soc_mwh - self.state.soc_mwh
            energy_in_mwh = min(requested_power_mw * duration_hours * c.charge_efficiency, max_chargeable_mwh)
            actual_power_mw = energy_in_mwh / (duration_hours * c.charge_efficiency) if duration_hours > 0 else 0.0
            self.state.soc_mwh += energy_in_mwh
            return actual_power_mw
        else:
            # Discharging: energy OUT of storage must be inflated by discharge_efficiency
            # to know how much SOC is actually consumed to deliver the requested power.
            max_dischargeable_mwh = self.state.soc_mwh - min_soc_mwh
            requested_out_mwh = -requested_power_mw * duration_hours
            energy_out_of_soc_mwh = min(requested_out_mwh / c.discharge_efficiency, max_dischargeable_mwh)
            delivered_mwh = energy_out_of_soc_mwh * c.discharge_efficiency
            actual_power_mw = -delivered_mwh / duration_hours if duration_hours > 0 else 0.0
            self.state.soc_mwh -= energy_out_of_soc_mwh
            return actual_power_mw
