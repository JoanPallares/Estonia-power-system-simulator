"""
run_pipeline_demo.py
=====================
Demonstrates the Phase 7-10 pipeline (RAW -> READ -> PARSE -> CLEAN ->
NORMALIZE -> VALIDATE -> PROCESSED) end to end, using REAL data already
in hand: B_data/raw/elering/generation_by_technology_quarterly.csv
(Q3 2025 wind/solar/biomass generation).

This is a genuine test case, not a toy: the biomass row is missing
installed_capacity_mw for real (Elering's press release didn't state
it) — watch the quality report catch that instead of silently treating
it as zero.
"""

from pathlib import Path

from A_engine.pipeline.pipeline import run_pipeline, PipelineConfig

ROOT = Path(__file__).parent


def main():
    config = PipelineConfig(
        numeric_columns=["generation_mwh", "installed_capacity_mw"],
        bool_columns=["renewable"],
        missing_check_columns=["generation_mwh", "installed_capacity_mw", "renewable"],
        nonnegative_columns=["generation_mwh", "installed_capacity_mw"],
        outlier_columns=["generation_mwh"],
    )

    result = run_pipeline(
        raw_path=ROOT / "B_data" / "raw" / "elering" / "generation_by_technology_quarterly.csv",
        config=config,
        dataset_name="Estonia Q3 2025 generation by technology",
        output_dir=ROOT / "B_data" / "processed",
    )

    print("=== PROCESSED data ===")
    print(result.processed_df.to_string(index=False))
    print()
    print("=== Normalization log ===")
    for line in result.normalization_log:
        print(f"  {line}")
    print()
    print(f"Duplicate rows dropped: {result.duplicate_rows_dropped}")
    print()
    print(result.quality_report.summary())
    print()
    print(f"Written to: {result.output_path}")
    print()
    print(
        "Note: the missing installed_capacity_mw for biomass_biogas_waste is "
        "EXPECTED and correctly flagged above — Elering's source press release "
        "genuinely didn't publish that number (see data_catalogue.csv). This "
        "pipeline reports it as missing; it does NOT fill it with 0. Any future "
        "use of this row for a capacity-factor calculation must handle that "
        "None explicitly (generation.py's capacity_factor already does — it "
        "returns None rather than dividing by an assumed capacity)."
    )


if __name__ == "__main__":
    main()
