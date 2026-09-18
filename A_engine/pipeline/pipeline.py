"""
pipeline.py — Phase 7: the full orchestrator

RAW -> READ -> PARSE -> CLEAN -> NORMALIZE -> VALIDATE -> PROCESSED

Each stage is independently testable (see the sibling modules and
tests/test_pipeline.py). This function just wires them together in
order and writes the result to B_data/<country>/processed/, alongside
a quality report so nothing about the run is silently lost.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd

from .read import read_raw_csv
from .parse import parse_types
from .clean import strip_whitespace, drop_exact_duplicate_rows, rename_columns
from .normalize import normalize_units
from .quality import run_quality_report, QualityReport


@dataclass
class PipelineConfig:
    numeric_columns: list[str] = field(default_factory=list)
    date_columns: list[str] = field(default_factory=list)
    bool_columns: list[str] = field(default_factory=list)
    rename_map: dict[str, str] = field(default_factory=dict)   # applied AFTER parse, BEFORE normalize
    column_units: dict[str, tuple[str, str]] = field(default_factory=dict)  # canonical (post-rename) column -> (quantity, raw_unit)
    missing_check_columns: list[str] = field(default_factory=list)
    nonnegative_columns: list[str] = field(default_factory=list)
    range_checks: dict[str, tuple[float, float]] = field(default_factory=dict)
    outlier_columns: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    processed_df: pd.DataFrame
    quality_report: QualityReport
    normalization_log: list[str]
    duplicate_rows_dropped: int
    output_path: Path | None


def run_pipeline(
    raw_path: str | Path,
    config: PipelineConfig,
    dataset_name: str,
    output_dir: str | Path | None = None,
) -> PipelineResult:
    raw_path = Path(raw_path)

    # RAW -> READ
    df = read_raw_csv(raw_path)

    # READ -> PARSE
    df = parse_types(
        df,
        numeric_columns=config.numeric_columns,
        date_columns=config.date_columns,
        bool_columns=config.bool_columns,
    )

    # PARSE -> CLEAN
    df = strip_whitespace(df)
    df, dropped = drop_exact_duplicate_rows(df)
    if config.rename_map:
        df = rename_columns(df, config.rename_map)

    # CLEAN -> NORMALIZE
    normalization_log = []
    if config.column_units:
        df, normalization_log = normalize_units(df, config.column_units)

    # NORMALIZE -> VALIDATE
    report = run_quality_report(
        df,
        dataset_name=dataset_name,
        missing_check_columns=config.missing_check_columns,
        nonnegative_columns=config.nonnegative_columns,
        range_checks=config.range_checks,
        outlier_columns=config.outlier_columns,
    )

    # -> PROCESSED
    output_path = None
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / raw_path.name
        df.to_csv(output_path, index=False)

    return PipelineResult(
        processed_df=df,
        quality_report=report,
        normalization_log=normalization_log,
        duplicate_rows_dropped=dropped,
        output_path=output_path,
    )
