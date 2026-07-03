# GitHub Release body - v1.1.1

## v1.1.1 - correction and reproducibility maintenance release

This release provides the reproducibility package for:

> *Incremental Value of Daily Workload and Wellness Monitoring Beyond a Personalised Readiness-History Baseline for Next-Calendar-Day Readiness in Elite Women's Football*

### What changed

- Corrected the `alpha=0` candidate implementation: ordinary least squares (`LinearRegression`) is now used instead of `Ridge(alpha=0)`.
- Renamed the implemented 3-/7-day predictor as a **readiness-reporting rate**, correcting prior wellness-reporting terminology.
- Corrected eligibility, reporting-rate, missingness, table, figure, and manuscript wording.
- Expanded automated verification for non-identifying aggregate tuning, performance, eligibility, missingness, and audit outputs.
- Added source-archive fingerprint validation, cleaned Zenodo/CFF metadata, and refreshed release documentation.

### Effect on reported findings

A clean rerun confirmed that the corrected implementation changes only non-selected unpenalised candidate rows in the inner tuning outputs. All selected penalties remained 1000, and all reported primary and wellness-item-missingness estimates were unchanged.

### Data availability

The original SoccerMon source data are not redistributed in this release. The repository contains code, manuscript source, figures, tables, and non-identifying aggregate reference outputs only.
