#!/usr/bin/env python3
"""Create the canonical study-design figure used by the manuscript."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def box(ax, x, y, width, height, text, fontsize=8.7):
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.03,rounding_size=0.07",
        linewidth=1.15, edgecolor="black", facecolor="white",
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->", mutation_scale=13, linewidth=1.1, color="black"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    out = args.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6.6))
    ax.axis("off")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)

    box(ax, 0.30, 4.35, 2.25, 1.10, "SoccerMon subjective records\n50 elite women footballers\nTwo teams; 2020-2021", 9.2)
    box(ax, 3.15, 4.35, 2.55, 1.10, "Primary paired complete-case cohort\n14,582 player-day pairs\nDay t predictors -> readiness at t+1", 8.8)
    box(ax, 6.30, 4.35, 2.25, 1.10, "2020 source data\nPopulation linear/ridge model\nTraining-only preprocessing", 8.6)
    box(ax, 9.15, 4.35, 2.35, 1.10, "2021 target data\nSequential personalised residual update\nEarlier forecast dates only", 8.4)
    arrow(ax, 2.55, 4.90, 3.15, 4.90)
    arrow(ax, 5.70, 4.90, 6.30, 4.90)
    arrow(ax, 8.55, 4.90, 9.15, 4.90)

    box(ax, 2.05, 1.50, 2.85, 1.36, "P0\nPersonalised readiness-history baseline\nCurrent readiness + prior residuals", 8.6)
    box(ax, 5.25, 1.50, 3.05, 1.36, "P1\nPersonalised full-monitoring model\nLoad + wellness + calendar + readiness-reporting rates\n+ same residual update", 8.1)
    box(ax, 9.00, 1.50, 2.35, 1.36, "Four evaluations\nWithin Team A\nWithin Team B\nTeam A -> Team B\nTeam B -> Team A", 8.3)
    arrow(ax, 7.15, 4.35, 3.50, 2.86)
    arrow(ax, 7.35, 4.35, 6.78, 2.86)
    arrow(ax, 10.15, 4.35, 10.15, 2.86)

    ax.text(6.0, 0.53, "Primary estimand: Delta MAE = MAE(P1) - MAE(P0); positive values indicate higher error for the full monitoring model.", ha="center", va="center", fontsize=8.7)
    fig.tight_layout(pad=0.25)
    fig.savefig(out / "Figure1_study_design.pdf", bbox_inches="tight")
    fig.savefig(out / "Figure1_study_design.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
