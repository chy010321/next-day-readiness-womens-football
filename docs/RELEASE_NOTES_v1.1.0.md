# Release notes for GitHub v1.1.0

Version 1.1.0 archives the refined reproducibility materials for the manuscript:

> *Incremental Value of Daily Workload and Wellness Monitoring Beyond a Personalised Readiness-History Baseline for Next-Calendar-Day Readiness in Elite Women's Football*

## Changes from v1.0.2

- Aligned the primary complete-case cohort with the 7-day load history actually used by the primary model.
- Replaced population-component-only tuning with comparator-specific **full-pipeline chronological tuning**. Each candidate penalty was evaluated after the same reset sequential residual adaptation used for deployment.
- Expanded the penalty grid through 100,000 to check that selected penalties were not constrained by the original upper bound.
- Renamed the primary comparator from an ``autoregressive baseline'' to a more precise ``readiness-history baseline''.
- Added a main-text eligibility flow, updated residual-window sensitivity figure, decile calibration curves, and player-level incremental-error plots.
- Clarified that cross-team confidence intervals quantify uncertainty across players in the evaluated target team rather than across a population of teams.
- Updated primary, sensitivity, missingness-aware, table, figure, manuscript, and reproducibility outputs.
- Renamed the analysis scripts for a clean final release and retained a one-command reproducibility check.

This release contains code, manuscript source, figures, tables, and reproducibility documentation. It does not redistribute the original SoccerMon dataset. Users must obtain the original source archive from:

https://doi.org/10.5281/zenodo.10033832
