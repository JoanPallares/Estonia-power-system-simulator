"""
curtailment.py
===============
Phase 30: Curtailment = AvailableRenewable - UsedRenewable

Country/technology-agnostic. "Available" and "used" are both passed in
— this module doesn't decide what COULD have been generated (that's
the renewable resource model's job, e.g. renewable_physical.py once
calibrated, or a capacity-scaling scenario like Phase 29's sweep).
"""

from __future__ import annotations
import pandas as pd


def compute_curtailment(available_renewable_mw: pd.Series, used_renewable_mw: pd.Series) -> pd.Series:
    """
    Returns curtailment (MW), never negative — if used > available
    (which shouldn't physically happen but real/messy data can show
    small negative residuals), curtailment is clipped to 0, and the
    caller should investigate why used exceeded available rather than
    have this function hide it.
    """
    curtailment = available_renewable_mw - used_renewable_mw
    return curtailment.clip(lower=0)


def curtailment_summary(available_renewable_mw: pd.Series, used_renewable_mw: pd.Series) -> dict:
    curtailment_mw = compute_curtailment(available_renewable_mw, used_renewable_mw)
    total_available = available_renewable_mw.sum()
    return {
        "total_curtailment_mwh": curtailment_mw.sum(),
        "total_available_mwh": total_available,
        "curtailment_pct_of_available": round(100 * curtailment_mw.sum() / total_available, 2) if total_available else None,
        "hours_with_curtailment": int((curtailment_mw > 0).sum()),
    }
