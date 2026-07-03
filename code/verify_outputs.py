#!/usr/bin/env python3
"""Verify non-identifying aggregate outputs for the v1.1.1 workflow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actual-dir", required=True, type=Path)
    parser.add_argument("--expected-dir", required=True, type=Path)
    parser.add_argument("--bootstrap-resamples", type=int, default=2000)
    return parser.parse_args()


def check_table(actual_path: Path, expected_path: Path, key_columns: list[str], numeric_columns: list[str], tolerance: float = 1e-7, filter_expression: str | None = None) -> None:
    actual = pd.read_csv(actual_path)
    expected = pd.read_csv(expected_path)
    if filter_expression:
        actual = actual.query(filter_expression).copy()
        expected = expected.query(filter_expression).copy()
    merged = expected.merge(actual, on=key_columns, how="outer", suffixes=("_expected", "_actual"), indicator=True)
    if not (merged["_merge"] == "both").all():
        problem = merged.loc[merged["_merge"] != "both", key_columns + ["_merge"]]
        raise AssertionError(f"Key mismatch between {actual_path.name} and {expected_path.name}:\n{problem}")
    for column in numeric_columns:
        difference = np.abs(merged[f"{column}_expected"].to_numpy(float) - merged[f"{column}_actual"].to_numpy(float))
        maximum = float(np.nanmax(difference)) if len(difference) else 0.0
        if maximum > tolerance:
            raise AssertionError(f"{actual_path.name}: maximum difference for {column} was {maximum:.3g}, exceeding {tolerance}.")
    print(f"PASS: {actual_path.name}")


def check_alpha_zero_sanity(path: Path) -> None:
    frame = pd.read_csv(path)
    zero = frame.loc[frame["alpha"].eq(0.0)].copy()
    if zero.empty:
        raise AssertionError(f"{path.name}: missing alpha=0 rows.")
    if not np.isfinite(zero[["MAE", "RMSE"]].to_numpy(float)).all():
        raise AssertionError(f"{path.name}: non-finite alpha=0 tuning values.")
    if (zero[["MAE", "RMSE"]].to_numpy(float) >= 5.0).any():
        raise AssertionError(f"{path.name}: implausibly large alpha=0 tuning values; check the LinearRegression implementation.")
    print(f"PASS: alpha=0 sanity in {path.name}")


def main() -> None:
    args = parse_args()
    if args.bootstrap_resamples != 2000:
        raise ValueError("Reference verification is defined for --bootstrap-resamples 2000 only.")
    actual, expected = args.actual_dir, args.expected_dir
    # Alpha>0 rows are exact numerical references. Alpha=0 is intentionally implemented by LinearRegression in v1.1.1 and is tested for finite, plausible values.
    check_table(actual / "TableS1_inner_time_tuning_detail_primary.csv", expected / "TableS1_inner_time_tuning_detail_primary.csv", ["cohort", "source_team", "model_code", "fold", "alpha"], ["MAE", "RMSE"], filter_expression="alpha > 0")
    check_table(actual / "TableS1_inner_time_tuning_summary_primary.csv", expected / "TableS1_inner_time_tuning_summary_primary.csv", ["cohort", "source_team", "model_code", "alpha"], ["weighted_MAE", "weighted_RMSE", "validation_rows_total"], filter_expression="alpha > 0")
    check_alpha_zero_sanity(actual / "TableS1_inner_time_tuning_detail_primary.csv")
    check_table(actual / "Table3_primary_tuned_performance.csv", expected / "Table3_primary_tuned_performance.csv", ["scenario_slug", "model_code"], ["alpha", "n", "MAE", "RMSE", "bias", "R2", "linear_calibration_intercept", "linear_calibration_slope"])
    check_table(actual / "TableS2_incremental_differences_tuned.csv", expected / "TableS2_incremental_differences_tuned.csv", ["scenario_slug", "comparison", "residual_window_observations"], ["alpha_P0", "alpha_P1", "MAE_difference", "CI_low", "CI_high", "bootstrap_resamples"], tolerance=1e-7)
    check_table(actual / "supplementary" / "TableS4_eligibility_flow.csv", expected / "TableS4_eligibility_flow.csv", ["Step"], ["Overall player-days", "Overall players", "TeamA player-days", "TeamA players", "TeamB player-days", "TeamB players"], tolerance=0.0)
    check_table(actual / "supplementary" / "TableS5_missingness_by_team_year.csv", expected / "TableS5_missingness_by_team_year.csv", ["Team", "Year", "Variable"], ["Rows", "Missing n", "Missing %"], tolerance=1e-10)
    check_table(actual / "TableS6_inner_time_tuning_detail_missingness_aware.csv", expected / "TableS6_inner_time_tuning_detail_missingness_aware.csv", ["cohort", "source_team", "model_code", "fold", "alpha"], ["MAE", "RMSE"], filter_expression="alpha > 0")
    check_table(actual / "TableS6_inner_time_tuning_summary_missingness_aware.csv", expected / "TableS6_inner_time_tuning_summary_missingness_aware.csv", ["cohort", "source_team", "model_code", "alpha"], ["weighted_MAE", "weighted_RMSE", "validation_rows_total"], filter_expression="alpha > 0")
    check_alpha_zero_sanity(actual / "TableS6_inner_time_tuning_detail_missingness_aware.csv")
    check_table(actual / "TableS7_missingness_aware_performance.csv", expected / "TableS7_missingness_aware_performance.csv", ["scenario_slug", "model_code"], ["alpha", "n", "MAE", "RMSE", "bias", "R2", "linear_calibration_intercept", "linear_calibration_slope"])
    check_table(actual / "TableS8_missingness_aware_incremental_differences.csv", expected / "TableS8_missingness_aware_incremental_differences.csv", ["scenario_slug", "comparison"], ["alpha_P0", "alpha_P1m", "MAE_difference", "CI_low", "CI_high", "bootstrap_resamples"], tolerance=1e-7)
    audit = json.loads((actual / "phase6_audit.json").read_text(encoding="utf-8"))
    expected_audit = {"primary_cohort_n": 14582, "full_calendar_panel_n": 36550, "missingness_aware_n": 14631, "online_calibration_window": 28, "bootstrap_resamples": 2000}
    for key, value in expected_audit.items():
        if audit.get(key) != value:
            raise AssertionError(f"phase6_audit.json: {key}={audit.get(key)!r}, expected {value!r}")
    print("PASS: phase6_audit.json")
    print("All archived numerical verification checks passed.")


if __name__ == "__main__":
    main()
