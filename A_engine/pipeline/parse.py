"""
parse.py — Phase 7, stage 2: READ -> PARSE

Converts the all-string DataFrame from read.py into proper dtypes,
using an explicit schema. Uses errors='raise' semantics throughout —
an unparseable value is a bug to surface, not something to silently
turn into NaN (pandas' default `errors='coerce'` is exactly the kind
of silent behaviour this project avoids per MASTER PROMPT Phase 10).
"""

from __future__ import annotations
import pandas as pd


def parse_types(
    df: pd.DataFrame,
    numeric_columns: list[str] | None = None,
    date_columns: list[str] | None = None,
    bool_columns: list[str] | None = None,
) -> pd.DataFrame:
    df = df.copy()

    for col in (numeric_columns or []):
        if col not in df.columns:
            raise KeyError(f"parse_types: expected numeric column '{col}' not found")
        try:
            df[col] = pd.to_numeric(df[col], errors="raise")
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Column '{col}' contains a value that isn't numeric — "
                f"fix the raw data or the schema, don't silently coerce it. ({e})"
            )

    for col in (date_columns or []):
        if col not in df.columns:
            raise KeyError(f"parse_types: expected date column '{col}' not found")
        df[col] = pd.to_datetime(df[col], errors="raise")

    for col in (bool_columns or []):
        if col not in df.columns:
            raise KeyError(f"parse_types: expected bool column '{col}' not found")
        # Explicit map, not bool(str) (which is True for any non-empty string,
        # including the string "false" — a classic silent bug).
        mapping = {"true": True, "false": False, "TRUE": True, "FALSE": False,
                   "True": True, "False": False}
        unmapped = set(df[col].dropna().unique()) - set(mapping.keys())
        if unmapped:
            raise ValueError(f"Column '{col}' has unrecognised boolean-like values: {unmapped}")
        df[col] = df[col].map(mapping)

    return df
