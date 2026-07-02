#!/usr/bin/env python3
"""
Build an analysis-ready athlete-day dataset for next-calendar-day readiness forecasting
from the official SoccerMon subjective.zip archive.

Unit of analysis: player i on date t.
Prediction target: Readiness of player i on calendar date t+1.

This script intentionally does NOT compute player-level means or transformations that
could leak information from test data. Those must be estimated inside each validation
fold during modelling.
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
    """Read a SoccerMon daily wide CSV and return a player-date long table."""
    df = pd.read_csv(path)
    if df.shape[1] < 2:
        raise ValueError(f"{path} does not have a date column and player columns.")
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    if df["date"].isna().any():
        raise ValueError(f"Failed to parse at least one date in {path}.")
    long_df = df.melt(
        id_vars="date", var_name="player_id", value_name=variable
    )
    long_df[variable] = pd.to_numeric(long_df[variable], errors="coerce")
    return long_df


def find_subjective_root(extract_root: Path) -> Path:
    """Locate the subjective directory after extracting the archive."""
    candidates = list(extract_root.rglob("subjective"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"Expected exactly one 'subjective' directory inside {extract_root}; "
            f"found {len(candidates)}."
        )
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--zip",
        required=True,
        type=Path,
        help="Path to the official SoccerMon subjective.zip archive.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Directory in which to save the analysis-ready CSV files.",
    )
    args = parser.parse_args()

    if not args.zip.is_file():
        raise FileNotFoundError(f"Archive not found: {args.zip}")

    args.output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(args.zip) as archive:
            archive.extractall(temp_root)

        source = find_subjective_root(temp_root)
        daily = wide_to_long(
            source / "training-load" / "daily_load.csv", "daily_load"
        )
        if daily["daily_load"].isna().any():
            raise ValueError("Unexpected missing values in official daily_load.csv.")

        panel = daily.copy()
        for variable in WELLNESS_VARS:
            wellness = wide_to_long(
                source / "wellness" / f"{variable}.csv", variable
            )
            panel = panel.merge(
                wellness,
                on=["date", "player_id"],
                how="left",
                validate="one_to_one",
            )

    panel["team"] = panel["player_id"].str.extract(r"^(Team[A-Z])", expand=False)
    if panel["team"].isna().any():
        raise ValueError("Unable to infer team for one or more anonymized player IDs.")

    panel = panel.sort_values(["player_id", "date"]).reset_index(drop=True)

    # Calendar-day target alignment: data at t predict readiness at t+1.
    target = panel[["player_id", "date", "readiness"]].copy()
    target["date"] = target["date"] - pd.Timedelta(days=1)
    target = target.rename(columns={"readiness": "readiness_t1"})
    panel = panel.merge(
        target, on=["player_id", "date"], how="left", validate="one_to_one"
    )

    # Causal training-load history including day t and prior calendar days.
    panel["training_day"] = (panel["daily_load"] > 0).astype(int)
    for window in (3, 7, 14, 28):
        panel[f"load_sum_{window}d"] = panel.groupby("player_id")["daily_load"].transform(
            lambda x: x.rolling(window, min_periods=window).sum()
        )
        panel[f"load_mean_{window}d"] = panel.groupby("player_id")["daily_load"].transform(
            lambda x: x.rolling(window, min_periods=window).mean()
        )
        if window in (3, 7, 14):
            panel[f"training_days_{window}d"] = panel.groupby("player_id")["training_day"].transform(
                lambda x: x.rolling(window, min_periods=window).sum()
            )

    # Past reporting density—available at t and potentially informative.
    panel["wellness_reported"] = panel["readiness"].notna().astype(int)
    for window in (3, 7):
        panel[f"wellness_report_rate_{window}d"] = panel.groupby(
            "player_id"
        )["wellness_reported"].transform(
            lambda x: x.rolling(window, min_periods=window).mean()
        )

    panel["day_of_week"] = panel["date"].dt.day_name()
    panel["day_of_week_num"] = panel["date"].dt.dayofweek
    panel["month"] = panel["date"].dt.month
    panel["year"] = panel["date"].dt.year
    panel["is_weekend"] = panel["day_of_week_num"].isin([5, 6]).astype(int)

    # Historical response count. Do not estimate personal baselines here;
    # calculate them separately inside each training/validation split.
    panel["prior_readiness_reports"] = panel.groupby("player_id")["readiness"].transform(
        lambda x: x.notna().cumsum().shift(1, fill_value=0)
    )

    panel["wellness_complete_t"] = panel[WELLNESS_VARS].notna().all(axis=1).astype(int)
    panel["analysis_eligible_primary"] = (
        (panel["wellness_complete_t"] == 1)
        & panel["readiness_t1"].notna()
        & panel["load_sum_14d"].notna()
    ).astype(int)

    columns = [
        "player_id", "team", "date", "year", "month",
        "day_of_week", "day_of_week_num", "is_weekend",
        "readiness", "readiness_t1", "daily_load", "training_day",
        "load_sum_3d", "load_mean_3d", "training_days_3d",
        "load_sum_7d", "load_mean_7d", "training_days_7d",
        "load_sum_14d", "load_mean_14d", "training_days_14d",
        "load_sum_28d", "load_mean_28d",
        "fatigue", "mood", "sleep_duration", "sleep_quality",
        "soreness", "stress",
        "wellness_report_rate_3d", "wellness_report_rate_7d",
        "prior_readiness_reports", "wellness_complete_t",
        "analysis_eligible_primary",
    ]
    full_panel = panel.loc[:, columns].copy()
    primary_pairs = full_panel.loc[
        full_panel["analysis_eligible_primary"] == 1
    ].sort_values(["team", "player_id", "date"])

    full_panel.to_csv(
        args.output / "soccermon_next_day_readiness_full_panel_v1.csv",
        index=False,
    )
    primary_pairs.to_csv(
        args.output / "soccermon_next_day_readiness_primary_pairs_v1.csv",
        index=False,
    )

    print(f"Saved {len(full_panel):,} athlete-day rows to the full panel.")
    print(f"Saved {len(primary_pairs):,} eligible next-day pairs to the primary dataset.")


if __name__ == "__main__":
    main()
