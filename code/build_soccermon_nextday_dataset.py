#!/usr/bin/env python3
"""Build analysis-ready SoccerMon player-day datasets for the final manuscript analysis.

The original SoccerMon ``subjective.zip`` archive is deliberately not distributed
with this repository. Download it from the official Zenodo record and supply its
local path via ``--zip``.
"""
from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

WELLNESS_VARS = [
    "readiness", "fatigue", "mood", "sleep_duration",
    "sleep_quality", "soreness", "stress",
]


def wide_to_long(path: Path, variable: str) -> pd.DataFrame:
    """Convert a SoccerMon daily wide file to a long player-day data frame."""
    frame = pd.read_csv(path)
    if frame.shape[1] < 2:
        raise ValueError(f"Expected a date column and player columns in {path}.")
    frame = frame.rename(columns={frame.columns[0]: "date"})
    frame["date"] = pd.to_datetime(frame["date"], dayfirst=True, errors="coerce")
    if frame["date"].isna().any():
        raise ValueError(f"Could not parse every date in {path}.")
    long_frame = frame.melt(id_vars="date", var_name="player_id", value_name=variable)
    long_frame[variable] = pd.to_numeric(long_frame[variable], errors="coerce")
    return long_frame


def find_subjective_root(extract_root: Path) -> Path:
    candidates = list(extract_root.rglob("subjective"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected exactly one directory named 'subjective'; found {len(candidates)}."
        )
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, type=Path,
                        help="Path to the official SoccerMon subjective.zip archive.")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Directory for generated Phase 1 player-day CSV files.")
    args = parser.parse_args()

    if not args.zip.is_file():
        raise FileNotFoundError(f"Source archive not found: {args.zip}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(args.zip) as archive:
            archive.extractall(temp_root)
        source = find_subjective_root(temp_root)

        daily = wide_to_long(source / "training-load" / "daily_load.csv", "daily_load")
        if daily["daily_load"].isna().any():
            raise ValueError("Official daily_load.csv unexpectedly contains missing values.")

        panel = daily.copy()
        for variable in WELLNESS_VARS:
            wellness = wide_to_long(source / "wellness" / f"{variable}.csv", variable)
            panel = panel.merge(
                wellness, on=["date", "player_id"], how="left", validate="one_to_one"
            )

    panel["team"] = panel["player_id"].str.extract(r"^(Team[A-Z])", expand=False)
    if panel["team"].isna().any():
        raise ValueError("Could not infer team from one or more anonymised player identifiers.")
    panel = panel.sort_values(["player_id", "date"]).reset_index(drop=True)

    # Calendar-day target alignment: predictors at t forecast readiness at t+1.
    target = panel[["player_id", "date", "readiness"]].copy()
    target["date"] = target["date"] - pd.Timedelta(days=1)
    target = target.rename(columns={"readiness": "readiness_t1"})
    panel = panel.merge(target, on=["player_id", "date"], how="left", validate="one_to_one")

    panel["training_day"] = (panel["daily_load"] > 0).astype(int)
    for window in (3, 7, 14, 28):
        panel[f"load_sum_{window}d"] = panel.groupby("player_id")["daily_load"].transform(
            lambda values: values.rolling(window, min_periods=window).sum()
        )
        panel[f"load_mean_{window}d"] = panel.groupby("player_id")["daily_load"].transform(
            lambda values: values.rolling(window, min_periods=window).mean()
        )
        if window in (3, 7, 14):
            panel[f"training_days_{window}d"] = panel.groupby("player_id")["training_day"].transform(
                lambda values: values.rolling(window, min_periods=window).sum()
            )

    panel["readiness_reported"] = panel["readiness"].notna().astype(int)
    for window in (3, 7):
        panel[f"readiness_report_rate_{window}d"] = panel.groupby("player_id")["readiness_reported"].transform(
            lambda values: values.rolling(window, min_periods=window).mean()
        )

    panel["day_of_week"] = panel["date"].dt.day_name()
    panel["day_of_week_num"] = panel["date"].dt.dayofweek
    panel["month"] = panel["date"].dt.month
    panel["year"] = panel["date"].dt.year
    panel["is_weekend"] = panel["day_of_week_num"].isin([5, 6]).astype(int)
    panel["prior_readiness_reports"] = panel.groupby("player_id")["readiness"].transform(
        lambda values: values.notna().cumsum().shift(1, fill_value=0)
    )

    panel["wellness_complete_t"] = panel[WELLNESS_VARS].notna().all(axis=1).astype(int)
    # Primary models use 7-day workload features, so primary eligibility requires
    # only the same 7-day history actually used by those models.
    panel["analysis_eligible_primary"] = (
        (panel["wellness_complete_t"] == 1)
        & panel["readiness_t1"].notna()
        & panel["load_mean_7d"].notna()
        & panel["training_days_7d"].notna()
    ).astype(int)

    columns = [
        "player_id", "team", "date", "year", "month", "day_of_week", "day_of_week_num",
        "is_weekend", "readiness", "readiness_t1", "daily_load", "training_day",
        "load_sum_3d", "load_mean_3d", "training_days_3d",
        "load_sum_7d", "load_mean_7d", "training_days_7d",
        "load_sum_14d", "load_mean_14d", "training_days_14d",
        "load_sum_28d", "load_mean_28d", "fatigue", "mood", "sleep_duration",
        "sleep_quality", "soreness", "stress", "readiness_report_rate_3d",
        "readiness_report_rate_7d", "prior_readiness_reports", "wellness_complete_t",
        "analysis_eligible_primary",
    ]
    full_panel = panel.loc[:, columns].copy()
    primary_pairs = full_panel.loc[full_panel["analysis_eligible_primary"] == 1].sort_values(
        ["team", "player_id", "date"]
    )

    full_path = args.output_dir / "soccermon_next_day_readiness_full_panel.csv"
    pairs_path = args.output_dir / "soccermon_next_day_readiness_primary_pairs.csv"
    full_panel.to_csv(full_path, index=False)
    primary_pairs.to_csv(pairs_path, index=False)
    print(f"Saved {len(full_panel):,} player-days: {full_path}")
    print(f"Saved {len(primary_pairs):,} primary eligible pairs: {pairs_path}")


if __name__ == "__main__":
    main()
