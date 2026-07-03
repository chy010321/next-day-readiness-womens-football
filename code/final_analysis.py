#!/usr/bin/env python3
"""Final reproducible analysis for next-calendar-day readiness forecasting.

This program separately tunes P0, P1 and P2 with expanding chronological
source-team 2020 folds, evaluates the four prespecified 2021 settings, and runs
a missingness-aware sensitivity analysis. It never uses 2021 outcome data to tune
population-model penalties.
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

WELLNESS = ["fatigue", "mood", "sleep_duration", "sleep_quality", "soreness", "stress"]
CALENDAR = ["day_of_week_num", "month"]
ALPHAS = [0.0, 0.0001, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]
WINDOWS = [14, 28, 56]
PRIMARY_WINDOW = 28
SEED = 20260702
SCENARIOS = [
    ("Within Team A: 2020→2021", "Within_TeamA_2020_to_2021", "TeamA", "TeamA"),
    ("Within Team B: 2020→2021", "Within_TeamB_2020_to_2021", "TeamB", "TeamB"),
    ("Cross-team: Team A 2020→Team B 2021", "Cross_TeamA2020_to_TeamB2021", "TeamA", "TeamB"),
    ("Cross-team: Team B 2020→Team A 2021", "Cross_TeamB2020_to_TeamA2021", "TeamB", "TeamA"),
]
PRIMARY_FEATURES = {
    "P0": ["readiness"],
    "P1": ["readiness", "daily_load", "load_mean_7d", "training_days_7d"]
          + WELLNESS + ["wellness_report_rate_3d", "wellness_report_rate_7d"] + CALENDAR,
    "P2": ["readiness", "daily_load", "fatigue", "soreness", "sleep_duration", "sleep_quality"]
          + CALENDAR,
}
MISSINGNESS_FEATURES = {
    "P0": ["readiness"],
    "P1m": ["readiness", "daily_load", "load_mean_7d", "training_days_7d"]
           + WELLNESS + [f"{name}_missing" for name in WELLNESS]
           + ["wellness_report_rate_3d", "wellness_report_rate_7d"] + CALENDAR,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path,
                        help="Directory produced by build_soccermon_nextday_dataset.py.")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Directory for generated analysis outputs.")
    parser.add_argument("--bootstrap-resamples", type=int, default=2000,
                        help="Player-cluster bootstrap resamples (default: 2000).")
    return parser.parse_args()


def transform(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    values = frame.loc[:, features].copy()
    for column in values.columns:
        if column == "daily_load" or column.startswith("load_mean_") or column.startswith("load_sum_"):
            values[column] = np.log1p(pd.to_numeric(values[column], errors="coerce"))
    return values


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str], alpha: float) -> np.ndarray:
    model = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=float(alpha))),
    ])
    model.fit(transform(train, features), train["readiness_t1"].astype(float))
    return model.predict(transform(test, features))


def sequential_calibrate(test: pd.DataFrame, base_prediction: np.ndarray, window: int) -> pd.DataFrame:
    """Add a past-only player-specific residual mean to each base prediction.

    The implementation uses array positions and a running residual sum so it can
    efficiently process the full 2021 target period without repeatedly modifying a
    pandas DataFrame inside the player-day loop.
    """
    data = test[["player_id", "date", "readiness_t1"]].copy().reset_index(drop=True)
    base = np.asarray(base_prediction, dtype=float)
    observed = data["readiness_t1"].to_numpy(dtype=float)
    predictions = np.empty(len(data), dtype=float)
    history_counts = np.zeros(len(data), dtype=int)

    for _, group in data.groupby("player_id", sort=False):
        positions = group.sort_values("date").index.to_numpy()
        history: deque[float] = deque()
        residual_sum = 0.0
        for position in positions:
            history_length = len(history)
            predictions[position] = base[position] + (residual_sum / history_length if history_length else 0.0)
            history_counts[position] = history_length
            residual = observed[position] - base[position]
            if history_length == window:
                residual_sum -= history.popleft()
            history.append(float(residual))
            residual_sum += float(residual)

    data["base_prediction"] = base
    data["prediction"] = predictions
    data["n_residuals"] = history_counts
    return data


def expanding_folds(frame: pd.DataFrame) -> list[tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]]:
    dates = np.array(sorted(frame["date"].drop_duplicates().tolist()))
    starts = [int(np.floor(len(dates) * proportion)) for proportion in (0.55, 0.70, 0.85)]
    ends = starts[1:] + [len(dates)]
    folds = []
    for start, end in zip(starts, ends):
        validation_start = pd.Timestamp(dates[start])
        validation_end = pd.Timestamp(dates[end - 1])
        train = frame.loc[frame["date"] < validation_start].copy()
        validation = frame.loc[
            (frame["date"] >= validation_start) & (frame["date"] <= validation_end)
        ].copy()
        folds.append((train, validation, validation_start, validation_end))
    return folds


def tune_deployment_pipeline(
    source_2020: pd.DataFrame, features: list[str], source_team: str,
    model_code: str, cohort: str, residual_window: int = PRIMARY_WINDOW,
) -> tuple[float, pd.DataFrame, pd.DataFrame]:
    """Tune each comparator using the full prospectively deployed pipeline.

    For every expanding validation block, the population model is fitted on earlier
    source-team dates and then evaluated with the same past-only sequential residual
    adaptation used in 2021 testing. Residual history is reset at the start of each
    validation block to emulate the target-period cold-start condition.
    """
    rows = []
    for fold_number, (train, validation, start, end) in enumerate(expanding_folds(source_2020), start=1):
        validation = validation.sort_values(["player_id", "date"]).reset_index(drop=True)
        for alpha in ALPHAS:
            base_prediction = fit_predict(train, validation, features, alpha)
            deployed = sequential_calibrate(validation, base_prediction, residual_window)
            prediction = deployed["prediction"].to_numpy(dtype=float)
            rows.append({
                "cohort": cohort,
                "source_team": source_team,
                "model_code": model_code,
                "fold": fold_number,
                "alpha": alpha,
                "train_rows": len(train),
                "validation_rows": len(validation),
                "validation_start": str(start.date()),
                "validation_end": str(end.date()),
                "residual_window_observations": residual_window,
                "tuning_pipeline": "population prediction plus reset sequential residual adaptation",
                "MAE": mean_absolute_error(validation["readiness_t1"], prediction),
                "RMSE": mean_squared_error(validation["readiness_t1"], prediction) ** 0.5,
            })
    detail = pd.DataFrame(rows)
    summary_rows = []
    for alpha, group in detail.groupby("alpha", sort=True):
        weights = group["validation_rows"].to_numpy(dtype=float)
        summary_rows.append({
            "alpha": alpha,
            "weighted_MAE": float(np.average(group["MAE"], weights=weights)),
            "weighted_RMSE": float(np.average(group["RMSE"], weights=weights)),
            "validation_rows_total": int(weights.sum()),
            "residual_window_observations": residual_window,
        })
    summary = pd.DataFrame(summary_rows).sort_values(["weighted_MAE", "alpha"]).reset_index(drop=True)
    summary["cohort"] = cohort
    summary["source_team"] = source_team
    summary["model_code"] = model_code
    summary["tuning_pipeline"] = "population prediction plus reset sequential residual adaptation"
    summary["selected"] = False
    summary.loc[0, "selected"] = True
    return float(summary.loc[0, "alpha"]), detail, summary


def metrics(observed: pd.Series, predicted: np.ndarray) -> dict[str, float | int]:
    y = np.asarray(observed, dtype=float)
    prediction = np.asarray(predicted, dtype=float)
    slope, intercept = np.polyfit(prediction, y, 1) if len(y) > 1 and np.std(prediction) > 1e-12 else (np.nan, np.nan)
    return {
        "n": int(len(y)),
        "MAE": float(mean_absolute_error(y, prediction)),
        "RMSE": float(mean_squared_error(y, prediction) ** 0.5),
        "bias": float(np.mean(prediction - y)),
        "R2": float(r2_score(y, prediction)),
        "linear_calibration_intercept": float(intercept),
        "linear_calibration_slope": float(slope),
        "within_1_point": float(np.mean(np.abs(y - prediction) <= 1.0)),
    }


def cluster_bootstrap_difference(
    frame: pd.DataFrame, candidate: str, baseline: str, seed: int, n_bootstrap: int,
) -> dict[str, float | int]:
    grouped = []
    for _, subgroup in frame.groupby("player_id", sort=False):
        grouped.append({
            "n": len(subgroup),
            "candidate_ae": np.abs(subgroup["readiness_t1"] - subgroup[candidate]).sum(),
            "baseline_ae": np.abs(subgroup["readiness_t1"] - subgroup[baseline]).sum(),
        })
    aggregate = pd.DataFrame(grouped)
    point = (
        aggregate["candidate_ae"].sum() / aggregate["n"].sum()
        - aggregate["baseline_ae"].sum() / aggregate["n"].sum()
    )
    rng = np.random.default_rng(seed)
    counts = aggregate["n"].to_numpy(dtype=float)
    candidate_errors = aggregate["candidate_ae"].to_numpy(dtype=float)
    baseline_errors = aggregate["baseline_ae"].to_numpy(dtype=float)
    values = []
    batch = 500
    for start in range(0, n_bootstrap, batch):
        indices = rng.integers(0, len(aggregate), size=(min(batch, n_bootstrap - start), len(aggregate)))
        values.append(
            candidate_errors[indices].sum(axis=1) / counts[indices].sum(axis=1)
            - baseline_errors[indices].sum(axis=1) / counts[indices].sum(axis=1)
        )
    samples = np.concatenate(values)
    return {
        "MAE_difference": float(point),
        "CI_low": float(np.quantile(samples, 0.025)),
        "CI_high": float(np.quantile(samples, 0.975)),
        "bootstrap_resamples": int(n_bootstrap),
    }


def add_missingness_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for variable in WELLNESS:
        result[f"{variable}_missing"] = result[variable].isna().astype(int)
    return result


def write_flow_and_missingness(full: pd.DataFrame, supplementary: Path) -> None:
    criteria = [
        ("Full calendar player-day panel", pd.Series(True, index=full.index)),
        ("Observed next-day readiness", full["readiness_t1"].notna()),
        ("Observed current-day and next-day readiness", full["readiness"].notna() & full["readiness_t1"].notna()),
        ("Plus available 7-day load history", full["readiness"].notna() & full["readiness_t1"].notna() & full["load_mean_7d"].notna() & full["training_days_7d"].notna()),
        ("Plus complete current-day wellness", full["readiness_t1"].notna() & full["wellness_complete_t"].eq(1) & full["load_mean_7d"].notna() & full["training_days_7d"].notna()),
        ("Primary complete-case analytic cohort (7-day history)", full["analysis_eligible_primary"].eq(1)),
    ]
    flow_rows = []
    for step, mask in criteria:
        subset = full.loc[mask]
        row = {"Step": step, "Overall player-days": len(subset), "Overall players": subset["player_id"].nunique()}
        for team in ("TeamA", "TeamB"):
            team_subset = subset.loc[subset["team"] == team]
            row[f"{team} player-days"] = len(team_subset)
            row[f"{team} players"] = team_subset["player_id"].nunique()
        flow_rows.append(row)
    flow = pd.DataFrame(flow_rows)
    flow.to_csv(supplementary / "TableS4_eligibility_flow.csv", index=False)

    missingness_rows = []
    for team in ("All", "TeamA", "TeamB"):
        for year in ("All", 2020, 2021):
            subset = full.copy()
            if team != "All":
                subset = subset.loc[subset["team"] == team]
            if year != "All":
                subset = subset.loc[subset["year"] == year]
            for variable in ["readiness", *WELLNESS, "readiness_t1"]:
                missingness_rows.append({
                    "Team": team,
                    "Year": year,
                    "Variable": variable,
                    "Rows": len(subset),
                    "Missing n": int(subset[variable].isna().sum()),
                    "Missing %": float(100 * subset[variable].isna().mean()),
                })
    pd.DataFrame(missingness_rows).to_csv(supplementary / "TableS5_missingness_by_team_year.csv", index=False)
    return flow


def plot_primary_incremental(differences: pd.DataFrame, figure_dir: Path) -> None:
    selected = differences.loc[
        differences["comparison"].eq("P1 full monitoring − P0 readiness-history baseline")
        & differences["residual_window_observations"].eq(PRIMARY_WINDOW)
    ].set_index("scenario").loc[[scenario[0] for scenario in SCENARIOS]].reset_index()
    figure, axis = plt.subplots(figsize=(10, 6.0))
    positions = np.arange(len(selected))[::-1]
    axis.axvline(0, color="black", linestyle="--", linewidth=1)
    for position, (_, row) in zip(positions, selected.iterrows()):
        axis.errorbar(
            row["MAE_difference"], position,
            xerr=[[max(0.0, row["MAE_difference"] - row["CI_low"])], [max(0.0, row["CI_high"] - row["MAE_difference"])]],
            fmt="o", capsize=4,
        )
        axis.text(row["CI_high"] + 0.004, position,
                  f"{row['MAE_difference']:+.3f} ({row['CI_low']:+.3f}, {row['CI_high']:+.3f})",
                  va="center", fontsize=9)
    axis.set_yticks(positions)
    axis.set_yticklabels(selected["scenario"])
    axis.set_xlabel("MAE difference: full monitoring − readiness-history baseline (readiness points)")
    axis.set_title("Incremental forecasting value after full-pipeline chronological tuning")
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(figure_dir / "Figure3_primary_incremental_value.pdf", bbox_inches="tight")
    figure.savefig(figure_dir / "Figure3_primary_incremental_value.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_flow(flow: pd.DataFrame, figure_dir: Path) -> None:
    figure, axis = plt.subplots(figsize=(10, 8))
    axis.axis("off")
    positions = np.linspace(0.88, 0.12, len(flow))
    for position, (_, row) in zip(positions, flow.iterrows()):
        axis.text(
            0.5, position,
            f"{row['Step']}\nOverall: {int(row['Overall player-days']):,}; Team A: {int(row['TeamA player-days']):,}; Team B: {int(row['TeamB player-days']):,}",
            ha="center", va="center", bbox={"boxstyle": "round,pad=.45", "facecolor": "white", "edgecolor": "black"}, fontsize=10,
        )
    for upper, lower in zip(positions[:-1], positions[1:]):
        axis.annotate("", xy=(0.5, lower + 0.05), xytext=(0.5, upper - 0.05), arrowprops={"arrowstyle": "->"})
    axis.set_title("Flow of player-days into the primary complete-case cohort", pad=20)
    figure.tight_layout()
    figure.savefig(figure_dir / "FigureS1_eligibility_flow.pdf", bbox_inches="tight")
    figure.savefig(figure_dir / "FigureS1_eligibility_flow.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_missingness_incremental(differences: pd.DataFrame, figure_dir: Path) -> None:
    selected = differences.set_index("scenario").loc[[scenario[0] for scenario in SCENARIOS]].reset_index()
    figure, axis = plt.subplots(figsize=(10, 6.0))
    positions = np.arange(len(selected))[::-1]
    axis.axvline(0, color="black", linestyle="--", linewidth=1)
    for position, (_, row) in zip(positions, selected.iterrows()):
        axis.errorbar(
            row["MAE_difference"], position,
            xerr=[[max(0.0, row["MAE_difference"] - row["CI_low"])], [max(0.0, row["CI_high"] - row["MAE_difference"])]],
            fmt="o", capsize=4,
        )
        axis.text(row["CI_high"] + 0.004, position,
                  f"{row['MAE_difference']:+.3f} ({row['CI_low']:+.3f}, {row['CI_high']:+.3f})",
                  va="center", fontsize=9)
    axis.set_yticks(positions)
    axis.set_yticklabels(selected["scenario"])
    axis.set_xlabel("MAE difference: missingness-aware full model − readiness-history baseline")
    axis.set_title("Missingness-aware sensitivity analysis")
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(figure_dir / "FigureS2_missingness_aware_incremental_value.pdf", bbox_inches="tight")
    figure.savefig(figure_dir / "FigureS2_missingness_aware_incremental_value.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_window_sensitivity(differences: pd.DataFrame, figure_dir: Path) -> None:
    """Plot P1-P0 MAE differences across residual-history windows."""
    selected = differences.loc[differences["comparison"].eq("P1 full monitoring − P0 readiness-history baseline")].copy()
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 6.8), constrained_layout=True)
    for axis, (display, slug, _, _) in zip(axes.flat, SCENARIOS):
        work = selected.loc[selected["scenario_slug"] == slug].sort_values("residual_window_observations")
        axis.axhline(0, linestyle="--", linewidth=1)
        axis.errorbar(
            work["residual_window_observations"], work["MAE_difference"],
            yerr=[work["MAE_difference"] - work["CI_low"], work["CI_high"] - work["MAE_difference"]],
            fmt="o-", capsize=3,
        )
        axis.set_title(display.replace("Cross-team: ", ""), fontsize=9)
        axis.set_xlabel("Residual-history window (observations)")
        axis.set_ylabel("P1 − P0 MAE")
        axis.set_xticks(WINDOWS)
        axis.grid(alpha=0.25)
    fig.savefig(figure_dir / "Figure4_residual_window_sensitivity.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_player_level_incremental(predictions: pd.DataFrame, figure_dir: Path) -> None:
    """Plot player-level differences in MAE for P1 versus P0."""
    rows = []
    for display, slug, _, _ in SCENARIOS:
        frame = predictions.loc[predictions["scenario_slug"] == slug].copy()
        for player, group in frame.groupby("player_id", sort=False):
            p1_mae = mean_absolute_error(group["readiness_t1"], group["P1_pred_w28"])
            p0_mae = mean_absolute_error(group["readiness_t1"], group["P0_pred_w28"])
            rows.append({"scenario": display.replace("Cross-team: ", ""), "player_id": player, "difference": p1_mae - p0_mae})
    work = pd.DataFrame(rows)
    scenario_labels = [display.replace("Cross-team: ", "") for display, _, _, _ in SCENARIOS]
    figure, axis = plt.subplots(figsize=(10, 5.5))
    positions = np.arange(len(scenario_labels))
    series = [work.loc[work["scenario"].eq(label), "difference"].to_numpy() for label in scenario_labels]
    axis.boxplot(series, positions=positions, widths=0.55, showfliers=False)
    rng = np.random.default_rng(SEED)
    for position, values in zip(positions, series):
        jitter = rng.uniform(-0.10, 0.10, size=len(values))
        axis.scatter(np.full(len(values), position) + jitter, values, s=18, alpha=0.65)
    axis.axhline(0, linestyle="--", linewidth=1)
    axis.set_xticks(positions)
    axis.set_xticklabels(scenario_labels, rotation=18, ha="right")
    axis.set_ylabel("Player-level P1 − P0 MAE")
    axis.set_title("Heterogeneity in the incremental error of full monitoring")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(figure_dir / "FigureS4_player_level_incremental_error.pdf", bbox_inches="tight")
    plt.close(figure)


def plot_analytic_sample(primary: pd.DataFrame, figure_dir: Path) -> None:
    """Plot eligible player-day counts by team and year for the supplement."""
    grouped = primary.groupby(["team", "year"], as_index=False).agg(n=("player_id", "size"), players=("player_id", "nunique"))
    order = [("TeamA", 2020), ("TeamA", 2021), ("TeamB", 2020), ("TeamB", 2021)]
    grouped["order"] = grouped.apply(lambda row: order.index((row["team"], int(row["year"]))), axis=1)
    grouped = grouped.sort_values("order")
    labels = [f"{row.team.replace('Team', 'Team ')}\n{int(row.year)}" for row in grouped.itertuples()]
    figure, axis = plt.subplots(figsize=(8.5, 4.5))
    bars = axis.bar(labels, grouped["n"])
    for bar, row in zip(bars, grouped.itertuples()):
        axis.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{int(row.n):,}\n({int(row.players)} players)", ha="center", va="bottom", fontsize=9)
    axis.set_ylabel("Eligible player-day pairs")
    axis.set_title("Primary analytic sample by team and year")
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    figure.savefig(figure_dir / "FigureS1_analytic_sample.pdf", bbox_inches="tight")
    plt.close(figure)


def plot_calibration_curves(predictions: pd.DataFrame, figure_dir: Path) -> None:
    """Create target-team calibration curves for P0 and P1 at the primary window."""
    scenario_order = [slug for _, slug, _, _ in SCENARIOS]
    labels = {slug: display.replace("Cross-team: ", "") for display, slug, _, _ in SCENARIOS}
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 7.8))
    for axis, slug in zip(axes.flat, scenario_order):
        frame = predictions.loc[predictions["scenario_slug"] == slug].copy()
        observed = frame["readiness_t1"].to_numpy(float)
        low = min(float(np.nanmin(observed)), float(np.nanmin(frame[["P0_pred_w28", "P1_pred_w28"]].to_numpy(float))))
        high = max(float(np.nanmax(observed)), float(np.nanmax(frame[["P0_pred_w28", "P1_pred_w28"]].to_numpy(float))))
        axis.plot([low, high], [low, high], linestyle="--", linewidth=1, label="Ideal")
        for model_code, column, label in [("P0", "P0_pred_w28", "P0 readiness-history"), ("P1", "P1_pred_w28", "P1 full monitoring")]:
            work = frame[["readiness_t1", column]].dropna().copy()
            # Bins are based on prediction ranks; duplicates are handled gracefully.
            try:
                work["bin"] = pd.qcut(work[column], q=10, duplicates="drop")
                grouped = work.groupby("bin", observed=True).agg(pred=(column, "mean"), obs=("readiness_t1", "mean"))
                axis.plot(grouped["pred"], grouped["obs"], marker="o", linewidth=1.5, label=label)
            except ValueError:
                axis.scatter(work[column], work["readiness_t1"], s=5, alpha=0.25, label=label)
        axis.set_title(labels[slug], fontsize=9)
        axis.set_xlabel("Mean predicted readiness")
        axis.set_ylabel("Mean observed readiness")
        axis.set_xlim(low, high)
        axis.set_ylim(low, high)
        axis.grid(alpha=0.25)
    handles, labels_ = axes.flat[0].get_legend_handles_labels()
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.legend(handles, labels_, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.012))
    fig.savefig(figure_dir / "FigureS3_calibration_curves.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    figure_dir = output_dir / "figures"
    supplementary_dir = output_dir / "supplementary"
    for directory in (output_dir, figure_dir, supplementary_dir):
        directory.mkdir(parents=True, exist_ok=True)

    primary = pd.read_csv(input_dir / "soccermon_next_day_readiness_primary_pairs.csv", parse_dates=["date"])
    full = pd.read_csv(input_dir / "soccermon_next_day_readiness_full_panel.csv", parse_dates=["date"])

    # Population component tuning: P0, P1, P2 each tuned separately in source 2020 data.
    primary_alpha: dict[tuple[str, str], float] = {}
    primary_detail, primary_summary = [], []
    for team in ("TeamA", "TeamB"):
        source = primary.loc[(primary["team"] == team) & (primary["year"] == 2020)].copy()
        for model_code, features in PRIMARY_FEATURES.items():
            alpha, detail, summary = tune_deployment_pipeline(source, features, team, model_code, "Primary complete-case cohort")
            primary_alpha[(team, model_code)] = alpha
            primary_detail.append(detail)
            primary_summary.append(summary)
    primary_detail_frame = pd.concat(primary_detail, ignore_index=True)
    primary_summary_frame = pd.concat(primary_summary, ignore_index=True)
    primary_detail_frame.to_csv(output_dir / "TableS1_inner_time_tuning_detail_primary.csv", index=False)
    primary_summary_frame.to_csv(output_dir / "TableS1_inner_time_tuning_summary_primary.csv", index=False)

    performance_rows, difference_rows, prediction_frames = [], [], []
    for scenario_index, (display, slug, source_team, target_team) in enumerate(SCENARIOS):
        train = primary.loc[(primary["team"] == source_team) & (primary["year"] == 2020)].copy()
        test = primary.loc[(primary["team"] == target_team) & (primary["year"] == 2021)].copy().sort_values(["player_id", "date"]).reset_index(drop=True)
        output = test[["player_id", "team", "date", "readiness_t1"]].copy()
        output["scenario"] = display
        output["scenario_slug"] = slug
        for model_code, features in PRIMARY_FEATURES.items():
            base = fit_predict(train, test, features, primary_alpha[(source_team, model_code)])
            output[f"{model_code}_base"] = base
            for window in WINDOWS:
                adjusted = sequential_calibrate(test, base, window)
                output[f"{model_code}_pred_w{window}"] = adjusted["prediction"].to_numpy()
                output[f"{model_code}_nresid_w{window}"] = adjusted["n_residuals"].to_numpy()
                if window == PRIMARY_WINDOW:
                    performance_rows.append({
                        "scenario": display, "scenario_slug": slug, "source_team": source_team,
                        "target_team": target_team, "model_code": model_code,
                        "alpha": primary_alpha[(source_team, model_code)],
                        "residual_window_observations": window,
                        **metrics(test["readiness_t1"], adjusted["prediction"]),
                    })
        for window in WINDOWS:
            difference_rows.append({
                "scenario": display, "scenario_slug": slug,
                "comparison": "P1 full monitoring − P0 readiness-history baseline",
                "source_team": source_team, "target_team": target_team,
                "residual_window_observations": window,
                "alpha_P0": primary_alpha[(source_team, "P0")],
                "alpha_P1": primary_alpha[(source_team, "P1")],
                **cluster_bootstrap_difference(output, f"P1_pred_w{window}", f"P0_pred_w{window}", SEED + scenario_index * 100 + window, args.bootstrap_resamples),
            })
        difference_rows.append({
            "scenario": display, "scenario_slug": slug,
            "comparison": "P2 reduced monitoring − P0 readiness-history baseline",
            "source_team": source_team, "target_team": target_team,
            "residual_window_observations": PRIMARY_WINDOW,
            "alpha_P0": primary_alpha[(source_team, "P0")],
            "alpha_P2": primary_alpha[(source_team, "P2")],
            **cluster_bootstrap_difference(output, "P2_pred_w28", "P0_pred_w28", SEED + 400 + scenario_index, args.bootstrap_resamples),
        })
        prediction_frames.append(output)

    performance = pd.DataFrame(performance_rows)
    differences = pd.DataFrame(difference_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    performance.to_csv(output_dir / "Table3_primary_tuned_performance.csv", index=False)
    differences.to_csv(output_dir / "TableS2_incremental_differences_tuned.csv", index=False)
    predictions.to_csv(output_dir / "primary_tuned_predictions.csv", index=False)

    flow = write_flow_and_missingness(full, supplementary_dir)

    # Missingness-aware sensitivity analysis.
    available = full.loc[
        full["readiness"].notna() & full["readiness_t1"].notna()
        & full["load_mean_7d"].notna() & full["training_days_7d"].notna()
    ].copy()
    available = add_missingness_indicators(available)
    missing_alpha: dict[tuple[str, str], float] = {}
    missing_detail, missing_summary = [], []
    for team in ("TeamA", "TeamB"):
        source = available.loc[(available["team"] == team) & (available["year"] == 2020)].copy()
        for model_code, features in MISSINGNESS_FEATURES.items():
            alpha, detail, summary = tune_deployment_pipeline(source, features, team, model_code, "Missingness-aware cohort")
            missing_alpha[(team, model_code)] = alpha
            missing_detail.append(detail)
            missing_summary.append(summary)
    missing_detail_frame = pd.concat(missing_detail, ignore_index=True)
    missing_summary_frame = pd.concat(missing_summary, ignore_index=True)
    missing_detail_frame.to_csv(output_dir / "TableS6_inner_time_tuning_detail_missingness_aware.csv", index=False)
    missing_summary_frame.to_csv(output_dir / "TableS6_inner_time_tuning_summary_missingness_aware.csv", index=False)

    missing_performance_rows, missing_difference_rows, missing_prediction_frames = [], [], []
    for scenario_index, (display, slug, source_team, target_team) in enumerate(SCENARIOS):
        train = available.loc[(available["team"] == source_team) & (available["year"] == 2020)].copy()
        test = available.loc[(available["team"] == target_team) & (available["year"] == 2021)].copy().sort_values(["player_id", "date"]).reset_index(drop=True)
        output = test[["player_id", "team", "date", "readiness_t1"]].copy()
        for model_code, features in MISSINGNESS_FEATURES.items():
            base = fit_predict(train, test, features, missing_alpha[(source_team, model_code)])
            adjusted = sequential_calibrate(test, base, PRIMARY_WINDOW)
            output[f"{model_code}_pred"] = adjusted["prediction"].to_numpy()
            missing_performance_rows.append({
                "scenario": display, "scenario_slug": slug, "source_team": source_team,
                "target_team": target_team, "model_code": model_code,
                "alpha": missing_alpha[(source_team, model_code)],
                "residual_window_observations": PRIMARY_WINDOW,
                **metrics(test["readiness_t1"], adjusted["prediction"]),
            })
        missing_difference_rows.append({
            "scenario": display, "scenario_slug": slug,
            "comparison": "P1m imputed full monitoring + missingness indicators − P0 readiness-history baseline",
            "source_team": source_team, "target_team": target_team,
            "residual_window_observations": PRIMARY_WINDOW,
            "alpha_P0": missing_alpha[(source_team, "P0")],
            "alpha_P1m": missing_alpha[(source_team, "P1m")],
            **cluster_bootstrap_difference(output, "P1m_pred", "P0_pred", SEED + 600 + scenario_index, args.bootstrap_resamples),
        })
        missing_prediction_frames.append(output)

    missing_performance = pd.DataFrame(missing_performance_rows)
    missing_differences = pd.DataFrame(missing_difference_rows)
    missing_predictions = pd.concat(missing_prediction_frames, ignore_index=True)
    missing_performance.to_csv(output_dir / "TableS7_missingness_aware_performance.csv", index=False)
    missing_differences.to_csv(output_dir / "TableS8_missingness_aware_incremental_differences.csv", index=False)
    missing_predictions.to_csv(output_dir / "missingness_aware_predictions.csv", index=False)

    plot_primary_incremental(differences, figure_dir)
    plot_flow(flow, figure_dir)
    plot_missingness_incremental(missing_differences, figure_dir)
    plot_window_sensitivity(differences, figure_dir)
    plot_player_level_incremental(predictions, figure_dir)
    plot_analytic_sample(primary, figure_dir)
    plot_calibration_curves(predictions, figure_dir)

    audit = {
        "analysis_version": "1.1.0",
        "primary_cohort_n": int(len(primary)),
        "full_calendar_panel_n": int(len(full)),
        "missingness_aware_n": int(len(available)),
        "candidate_alphas": ALPHAS,
        "deployment_pipeline_tuning": "Three expanding chronological source-team 2020 folds; weighted validation MAE after reset sequential residual adaptation",
        "online_calibration_window": PRIMARY_WINDOW,
        "bootstrap_resamples": int(args.bootstrap_resamples),
    }
    with (output_dir / "phase6_audit.json").open("w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2)

    print("Final analysis completed.")
    print(f"Primary cohort rows: {len(primary):,}")
    print(f"Missingness-aware cohort rows: {len(available):,}")
    print(f"Outputs written to: {output_dir}")


if __name__ == "__main__":
    main()
