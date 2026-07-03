# Final quality-assurance record: v1.1.0 pre-archive package

## Scope

This document records the final pre-archive checks for the manuscript and reproducibility package:

> *Incremental Value of Daily Workload and Wellness Monitoring Beyond a Personalised Readiness-History Baseline for Next-Calendar-Day Readiness in Elite Women's Football*

## Scientific and reporting refinements completed

- Primary complete-case eligibility was aligned with the 7-day workload-history feature used in the primary model.
- The primary cohort contains 14,582 eligible player-day pairs from 50 players.
- P0, P1, P2, and the missingness-aware P1m comparator were tuned separately with three expanding chronological source-team 2020 folds.
- Tuning evaluated the complete deployed pipeline, including reset sequential player-specific residual calibration within each internal validation block.
- The primary comparator is termed a **readiness-history baseline**, not an autoregressive model.
- Cross-team analyses are described as a two-team transportability assessment under sequential player-specific adaptation.
- The manuscript reports an eligibility flow, team-year missingness, missingness-aware sensitivity analyses, residual-window sensitivity analyses, calibration diagnostics, and player-level heterogeneity.
- No smallest practically important MAE difference was prespecified; the manuscript therefore does not claim formal equivalence or clinical utility.

## Reproducibility verification

The full workflow was run from a clean output directory using the official SoccerMon `subjective.zip` archive obtained separately from its source record:

```bash
python code/run_all.py --data-zip /path/to/subjective.zip --bootstrap-resamples 2000
```

The workflow rebuilt the 36,550-row calendar panel, the 14,582-pair primary cohort, all tuning/sensitivity analyses, and generated figures/tables. `code/verify_outputs.py` confirmed exact agreement for the archived key outputs:

- `Table3_primary_tuned_performance.csv`
- `TableS2_incremental_differences_tuned.csv`
- `TableS8_missingness_aware_incremental_differences.csv`

The final command output was:

```text
All archived numerical verification checks passed.
```

## LaTeX and visual verification

- `main.tex` compiled successfully with `pdfLaTeX + Biber`.
- `supplementary.tex` compiled successfully.
- Final main-text PDF: 14 pages.
- Final supplementary PDF: 5 pages.
- No unresolved citations, cross-references, bibliography errors, clipped tables, or figure-label overlaps were found in the final compilation and rendered-page review.

## Archive boundary

This package does not redistribute the original SoccerMon `subjective.zip` archive, raw player-day data, individual predictions, or local generated outputs. It contains code, manuscript source, figures, tables, non-identifying reference outputs, fixed software dependencies, and documentation.

## Remaining archival action

This is a pre-archive `v1.1.0` package. After the GitHub Release and Zenodo archive are published, insert the resulting **specific version DOI** into `sections/05_declarations.tex`, update `README.md` and `CITATION.cff` if desired, recompile the manuscript, and prepare the DOI-linked submission package.
