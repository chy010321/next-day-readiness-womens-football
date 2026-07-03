# Manuscript refinement report: v1.1.0

## Purpose

This update addresses remaining methodological and reporting issues identified during pre-submission review.

## Completed refinements

1. **Eligibility-model alignment:** Primary eligibility now requires the 7-day workload history used by P1, rather than an unused 14-day history.
2. **Fairer tuning:** Penalties are selected using the full deployed pipeline in internal expanding time folds, including reset sequential residual adaptation.
3. **Comparator terminology:** P0 is labelled a readiness-history baseline rather than an autoregressive model.
4. **Transportability scope:** The manuscript now distinguishes player-level uncertainty from team-population external validation.
5. **Practical interpretation:** The manuscript explicitly states that no smallest practically important MAE threshold was prespecified and therefore does not claim formal equivalence.
6. **Missingness transparency:** A main-text eligibility flow, team-year missingness table, and broader missingness-aware sensitivity analysis are included.
7. **Visual reporting:** Redundant sample-count content was moved to the supplement; the main text now prioritises eligibility flow, primary incremental error, and residual-window sensitivity. Calibration curves and player-level heterogeneity appear in the supplement.
8. **Reproducibility:** The repository now uses clean script names, repository-relative paths, a one-command runner, expected-output verification, and a release-specific metadata package.
9. **Reporting transparency:** `docs/REPORTING_TRANSPARENCY_MAP.md` maps the study design, outcome timing, tuning, uncertainty, missingness, transportability, and reproducibility details to their locations in the manuscript and archive.

## Main numerical finding

Across four within-team/cross-team 2021 settings, P1 minus P0 MAE differences under the primary 28-observation residual window were +0.007, +0.018, +0.022, and +0.004 readiness points, with all player-cluster bootstrap 95% confidence intervals crossing zero. The full panel therefore did not demonstrate stable incremental MAE improvement beyond the readiness-history baseline.
