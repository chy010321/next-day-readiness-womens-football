# Multi-pass full-text audit and revision record — v1.1.1

## Scope

This document records a source-level, code-to-manuscript, table/figure-caption, and editorial audit of the v1.1.1 pre-archive package. It does **not** rerun the complete SoccerMon workflow or alter numerical outputs. The principal analyses and figures remain those produced by the archived workflow; Figure 1 is intentionally not redesigned in this package.

## Pass 1 — Numerical and internal-consistency audit

Checked across the manuscript, supplementary material, table sources, figure captions, code constants, and expected aggregate outputs:

- primary paired cohort: 14,582 player-day pairs from 50 players;
- full calendar panel: 36,550 player-days;
- conditional wellness-item-missingness cohort: 14,631 player-days;
- additional player-days introduced by item-level wellness imputation: 49;
- primary residual-history window: 28 earlier eligible forecast dates;
- bootstrap repetitions: 2,000;
- selected primary penalties: alpha = 1000 for all source-team/model combinations;
- daily-load overall IQR: 12–600 session-RPE units;
- four primary P1–P0 MAE contrasts and confidence intervals.

The revised narrative uses these values consistently. No numeric result was changed.

## Pass 2 — Prediction-protocol and leakage audit

Clarified that:

- the target is readiness on the next **calendar** day, not the next available record;
- candidate inputs are defined as available by the end of day t;
- load-history features cover day t plus the preceding six calendar days;
- validation is chronological and source-training preprocessing is estimated only from the applicable source training partition;
- residual history is reset at each internal validation block and at the target-period cold start;
- target-team residual updating uses only earlier eligible target-period outcomes;
- cross-team analyses are not zero-shot external validation.

## Pass 3 — Statistical-reporting audit

Strengthened the reporting of:

- MAE as the prespecified primary metric and the status of RMSE and calibration as secondary diagnostics;
- the pooled player-cluster bootstrap construction and percentile confidence intervals;
- the interpretation of these intervals as player-level, within-target-team uncertainty;
- the absence of a prespecified practical-equivalence, non-inferiority, or decision-utility threshold;
- the distinction between no stable evidence of benefit and proof of no practical value;
- continuous, unrounded, untruncated prediction output.

## Pass 4 — Scope, missingness, and external-validity audit

Clarified that:

- the primary estimand concerns report-complete, outcome-observed player-days;
- retrospective eligibility counts are not prospective deployment-availability rates;
- the sensitivity analysis addresses item-level wellness missingness only, not absent questionnaires;
- the sensitivity cohort adds 49 player-days and should not be described as a broad all-calendar-day missingness solution;
- the study concerns two teams in one league and is not a causal, injury, clinical, or universal external-validation study;
- target-team residual updating does not establish new-player cold-start performance.

## Pass 5 — Narrative, clarity, and submission-readiness audit

Edited the title/abstract, introduction, methods, results, discussion, conclusion, practical applications, declarations, and captions to:

- state the conditional incremental-value question consistently;
- remove wording that could imply causal irrelevance of workload or wellness;
- distinguish transportability under adaptation from zero-shot external validation;
- align all limitations with the implementation;
- make the code-availability placeholder explicit until Zenodo has archived the immutable v1.1.1 GitHub release;
- add Supplementary Table S9, which concisely maps the implemented evaluation to its interpretation boundaries.

## Remaining work deliberately deferred to v1.1.2 or later

1. Replace Figure 1 after a content-rich workflow graphic has been supplied.
2. Insert the version-specific Zenodo DOI after the GitHub v1.1.1 release is archived.
3. Re-run the complete analysis if implementing substantive upgrades, including alternative calendar encoding, naive/population-only baselines, explicit cold-start analyses, range-handling sensitivity analyses, or prospective deployment-coverage modelling.
4. Adapt the generative-AI disclosure and manuscript formatting to the final target journal's author instructions.
