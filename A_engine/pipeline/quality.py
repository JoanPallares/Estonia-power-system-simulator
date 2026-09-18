"""
quality.py
==========
Phase 10: data quality checks.

Every function here REPORTS problems. None of them fix anything
automatically — MASTER PROMPT Phase 10 is explicit: never silently do
`NaN = 0`. If a value needs to be imputed, that is a separate, visible,
justified decision made by a human (or a clearly-logged, named
imputation function) downstream of this report, never hidden inside a
"cleaning" step.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from ..models.time_handling import validate_hourly_continuity


@dataclass
class QualityReport:
    dataset_name: str
    missing_values: dict = field(default_factory=dict)       # column -> count
    duplicate_rows: int = 0
    negative_value_rows: dict = field(default_factory=dict)  # column -> list of indices
    out_of_range_rows: dict = field(default_factory=dict)    # column -> list of indices
    outlier_rows: dict = field(default_factory=dict)         # column -> list of indices
    timestamp_issues: dict | None = None

    def is_clean(self) -> bool:
        return (
            not any(self.missing_values.values())
            and self.duplicate_rows == 0
            and not any(self.negative_value_rows.values())
            and not any(self.out_of_range_rows.values())
            and not any(self.outlier_rows.values())
            and (self.timestamp_issues is None or (
                not self.timestamp_issues.get("gaps")
                and not self.timestamp_issues.get("duplicates")
            ))
        )

    def summary(self) -> str:
        lines = [f"Quality report: {self.dataset_name}"]
        lines.append(f"  Missing values: {self.missing_values or 'none'}")
        lines.append(f"  Duplicate rows: {self.duplicate_rows}")
        lines.append(f"  Negative-value rows (in columns that should be >=0): {self.negative_value_rows or 'none'}")
        lines.append(f"  Out-of-range rows: {self.out_of_range_rows or 'none'}")
        lines.append(f"  Outlier rows: {self.outlier_rows or 'none'}")
        if self.timestamp_issues is not None:
            lines.append(f"  Timestamp gaps: {len(self.timestamp_issues.get('gaps', []))}")
            lines.append(f"  Timestamp duplicates: {len(self.timestamp_issues.get('duplicates', []))}")
        lines.append(f"  Clean: {self.is_clean()}")
        return "\n".join(lines)


def check_missing(df: pd.DataFrame, columns: list[str]) -> dict:
    return {col: int(df[col].isna().sum()) for col in columns if df[col].isna().sum() > 0}


def check_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> int:
    return int(df.duplicated(subset=subset).sum())


def check_negative(df: pd.DataFrame, nonnegative_columns: list[str]) -> dict:
    """Flags rows where a column that is physically defined as >= 0
    (e.g. generation_mwh, capacity_mw) is negative."""
    result = {}
    for col in nonnegative_columns:
        if col not in df.columns:
            continue
        bad = df.index[df[col] < 0].tolist()
        if bad:
            result[col] = bad
    return result


def check_impossible(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> list:
    """Generic range check for a column with a known physical bound
    (e.g. a capacity factor must be within [0, 1.05] — allowing a small
    margin over 1.0 for metering tolerance, not silently clipping)."""
    if column not in df.columns:
        return []
    return df.index[(df[column] < min_val) | (df[column] > max_val)].tolist()


def check_outliers(df: pd.DataFrame, column: str, z_threshold: float = 3.0) -> list:
    """
    Simple z-score outlier flag. Deliberately simple (Section 3:
    "avoid introducing ... complex ... merely because it sounds
    impressive") — flags for human review, does not remove anything.
    """
    if column not in df.columns or df[column].std(ddof=0) == 0 or df[column].isna().all():
        return []
    z = (df[column] - df[column].mean()) / df[column].std(ddof=0)
    return df.index[z.abs() > z_threshold].tolist()


def run_quality_report(
    df: pd.DataFrame,
    dataset_name: str,
    missing_check_columns: list[str],
    nonnegative_columns: list[str] | None = None,
    range_checks: dict[str, tuple[float, float]] | None = None,
    outlier_columns: list[str] | None = None,
    timestamp_index: pd.DatetimeIndex | None = None,
) -> QualityReport:
    """Runs the standard battery of Phase 10 checks and returns a report."""
    report = QualityReport(dataset_name=dataset_name)

    report.missing_values = check_missing(df, missing_check_columns)
    report.duplicate_rows = check_duplicates(df)

    if nonnegative_columns:
        report.negative_value_rows = check_negative(df, nonnegative_columns)

    if range_checks:
        report.out_of_range_rows = {
            col: check_impossible(df, col, lo, hi)
            for col, (lo, hi) in range_checks.items()
            if check_impossible(df, col, lo, hi)
        }

    if outlier_columns:
        report.outlier_rows = {
            col: check_outliers(df, col)
            for col in outlier_columns
            if check_outliers(df, col)
        }

    if timestamp_index is not None:
        report.timestamp_issues = validate_hourly_continuity(timestamp_index)

    return report
