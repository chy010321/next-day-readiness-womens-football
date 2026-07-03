#!/usr/bin/env python3
"""Create the canonical eligibility-flow figure used by the manuscript.

The counts are deterministic aggregate outputs from the validated v1.1.1
analysis. The full analysis workflow regenerates the same figure from the
analysis-ready panel in final_analysis.py.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt


FLOW = [
    ("Full calendar player-day panel", "Overall: 36,550; Team A: 19,737; Team B: 16,813"),
    ("Observed next-day readiness", "Overall: 16,997; Team A: 11,022; Team B: 5,975"),
    ("Observed current- and next-day readiness\nplus 7-day load history", "Overall: 14,631; Team A: 9,722; Team B: 4,909"),
    ("Plus complete current-day readiness\nand wellness profile", "Overall: 14,582; Team A: 9,693; Team B: 4,889"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(10, 7.25))
    axis.axis("off")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    positions = [0.86, 0.64, 0.40, 0.15]

    for position, (title, counts) in zip(positions, FLOW):
        axis.text(
            0.5,
            position,
            f"{title}\n{counts}",
            ha="center",
            va="center",
            fontsize=10.5,
            bbox={"boxstyle": "round,pad=0.55", "facecolor": "white", "edgecolor": "black", "linewidth": 1.15},
        )
    for top, bottom in zip(positions[:-1], positions[1:]):
        axis.annotate(
            "",
            xy=(0.5, bottom + 0.075),
            xytext=(0.5, top - 0.075),
            arrowprops={"arrowstyle": "->", "linewidth": 1.15},
        )
    axis.set_title("Flow of player-days into the primary paired complete-case cohort", fontsize=13, pad=18)
    figure.tight_layout(pad=0.6)
    figure.savefig(output_dir / "Figure2_eligibility_flow.pdf", bbox_inches="tight")
    figure.savefig(output_dir / "Figure2_eligibility_flow.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


if __name__ == "__main__":
    main()
