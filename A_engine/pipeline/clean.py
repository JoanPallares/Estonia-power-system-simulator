"""
clean.py — Phase 7, stage 3: PARSE -> CLEAN

Structural cleaning ONLY: whitespace, exact-duplicate row removal,
column renaming. Deliberately does NOT touch missing values, outliers,
or anything that requires a judgement call — that's quality.py's job to
report and a human's job to decide on. This keeps CLEAN safe to run
unattended; anything riskier is a separate, visible step.
"""

from __future__ import annotations
import pandas as pd


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].str.strip()
    return df


def drop_exact_duplicate_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Only drops rows that are FULLY identical across every column —
    never a partial/fuzzy dedupe, which would be a judgement call."""
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    return df, dropped


def rename_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Renames raw column names to this project's canonical names
    (see docs/data_dictionary.md). Raises if a
    column the mapping expects isn't present — silently ignoring a
    missing column is exactly the kind of thing this project avoids."""
    missing = set(mapping.keys()) - set(df.columns)
    if missing:
        raise KeyError(f"rename_columns: expected source columns not found: {missing}")
    return df.rename(columns=mapping)
