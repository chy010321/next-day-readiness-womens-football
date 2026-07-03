# Audit and corrections - v1.1.1

## Scope

This release consolidates a pre-release audit of manuscript source, supplementary source, code, reproducibility package, metadata, documentation, and a clean end-to-end reproduction based on the official SoccerMon `subjective.zip` archive.

## Verified outcomes

The audit reproduced 36,550 calendar player-days, 14,582 primary eligible player-day pairs, 14,631 player-days in the item-level wellness-missingness cohort, and all reported primary/missingness-sensitivity estimates. The four primary P1-P0 MAE differences and their 2,000-resample player-cluster bootstrap intervals were unchanged.

## Corrected defect

The implementation previously treated `alpha=0` as `Ridge(alpha=0)`. Version 1.1.1 correctly uses `LinearRegression()` for the unpenalised linear-model limit. The correction changes only non-selected alpha=0 inner-tuning rows; selected alpha values remained 1000 across all source-team/model combinations and manuscript-facing numerical results were unchanged.

## Additional corrections

- Renamed wellness-reporting-rate variables to readiness-reporting-rate variables.
- Corrected Table 1 reporting-rate summaries and non-zero-load label.
- Clarified complete current-day readiness/wellness eligibility.
- Simplified Figure 2/Supplementary Table S4 eligibility flow.
- Added next-day readiness missingness to Supplementary Table S5.
- Added source fingerprint checking, broader verifier coverage, clean Zenodo/CFF metadata, canonical Figure 1 generation, and Type 42 font configuration.

## Boundary conditions retained

This study remains a calendar-day forecasting analysis of self-reported next-day readiness among two teams, not a causal analysis, injury/clinical prediction study, broad external validation, new-player cold-start evaluation, or formal practical-equivalence/decision-utility analysis.
