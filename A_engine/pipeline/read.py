"""
read.py — Phase 7, stage 1: RAW -> READ

Deliberately dumb: opens a file and returns exactly what's in it, no
interpretation, no type coercion, no renaming. Every other stage
assumes this one did nothing clever.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd


def read_raw_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raw file not found: {path}")
    # dtype=str: read everything as text at this stage. Type interpretation
    # is PARSE's job, not READ's — keeps this stage trivially correct.
    return pd.read_csv(path, dtype=str)
