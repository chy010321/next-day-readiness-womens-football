# Release notes for GitHub v1.1.1

Version 1.1.1 is a correction and reproducibility-maintenance release for the manuscript:

> *Incremental Value of Daily Workload and Wellness Monitoring Beyond a Personalised Readiness-History Baseline for Next-Calendar-Day Readiness in Elite Women's Football*

## Corrected implementation

- The candidate grid includes `alpha=0`, defined in the manuscript as the unpenalised linear-model limit. This version implements it with `LinearRegression()` rather than `Ridge(alpha=0)`.
- The correction affects only non-selected unpenalised candidate rows in inner-tuning files. In the audited full rerun, every selected alpha remained 1000 and all reported primary and wellness-item-missingness performance estimates were unchanged.

## Reporting and figure corrections

- Corrected the label/value of the reporting-rate feature to 3-/7-day readiness-reporting rate.
- Corrected Table 1 labels and readiness-reporting-rate summaries.
- Clarified primary eligibility as a complete current-day readiness and wellness profile.
- Simplified the eligibility flow and renamed it Figure 2.
- Added next-day readiness missingness to Supplementary Table S5.
- Made Supplementary Table S2 self-contained by naming the candidate model.
- Added a canonical Figure 1 script and Type 42 font embedding for newly generated Matplotlib figures.

## Reproducibility and metadata

- Expanded automated verification to all non-identifying aggregate tables and `phase6_audit.json`.
- Added optional strict validation of the official `subjective.zip` source fingerprint.
- Updated README, CFF, Zenodo metadata, environment name, manifest, and release guidance.

The original SoccerMon source data are not redistributed.
