#!/usr/bin/env python3
"""Verify key archived summary outputs against the archived reference values."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actual-dir", required=True, type=Path)
    parser.add_argument("--expected-dir", required=True, type=Path)
    parser.add_argument("--bootstrap-resamples", type=int, default=2000)
    return parser.parse_args()


def check_table(actual_path: Path, expected_path: Path, key_columns: list[str], numeric_columns: list[str], tolerance: float = 1e-7) -> None:
    actual = pd.read_csv(actual_path)
    expected = pd.read_csv(expected_path)
    merged = expected.merge(actual, on=key_columns, how="outer", suffixes=("_expected", "_actual"), indicator=True)
    if not (merged["_merge"] == "both").all():
        problem = merged.loc[merged["_merge"] != "both", key_columns + ["_merge"]]
        raise AssertionError(f"Key mismatch between {actual_path.name} and {expected_path.name}:\n{problem}")
    for column in numeric_columns:
        difference = np.abs(merged[f"{column}_expected"].to_numpy(float) - merged[f"{column}_actual"].to_numpy(float))
        maximum = float(np.nanmax(difference))
        if maximum > tolerance:
            raise AssertionError(
                f"{actual_path.name}: maximum difference for {column} was {maximum:.3g}, exceeding {tolerance}."
            )
    print(f"PASS: {actual_path.name}")


def main() -> None:
    args = parse_args()
    if args.bootstrap_resamples != 2000:
        raise ValueError("Reference verification is defined for --bootstrap-resamples 2000 only.")
    check_table(
        args.actual_dir / "Table3_primary_tuned_performance.csv",
        args.expected_dir / "Table3_primary_tuned_performance.csv",
        ["scenario_slug", "model_code"],
        ["alpha", "n", "MAE", "RMSE", "bias", "R2", "linear_calibration_intercept", "linear_calibration_slope"],
    )
    check_table(
        args.actual_dir / "TableS2_incremental_differences_tuned.csv",
        args.expected_dir / "TableS2_incremental_differences_tuned.csv",
        ["scenario_slug", "comparison", "residual_window_observations"],
        ["alpha_P0", "alpha_P1", "MAE_difference", "CI_low", "CI_high", "bootstrap_resamples"],
    )
    check_table(
        args.actual_dir / "TableS8_missingness_aware_incremental_differences.csv",
        args.expected_dir / "TableS8_missingness_aware_incremental_differences.csv",
        ["scenario_slug", "comparison"],
        ["alpha_P0", "alpha_P1m", "MAE_difference", "CI_low", "CI_high", "bootstrap_resamples"],
    )
    print("All archived numerical verification checks passed.")


if __name__ == "__main__":
    main()
