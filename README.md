# Next-day readiness forecasting in elite women's football

**Release preparation version:** `v1.1.0`  
**Author:** Haoyang Cheng, Wuhan Sport University  
**ORCID:** 0009-0009-4123-2610

## Study purpose

This repository contains the manuscript source, figures, tables, analysis code, and reproducibility materials for:

> *Incremental Value of Daily Workload and Wellness Monitoring Beyond a Personalised Readiness-History Baseline for Next-Calendar-Day Readiness in Elite Women's Football*

The study tests whether a daily workload--wellness panel improves next-calendar-day self-reported readiness forecasts beyond a strong player-specific readiness-history baseline.

## v1.1.0 refinements

This release preparation updates the analysis and manuscript by:

1. aligning primary eligibility with the 7-day workload history actually used by the primary model;
2. tuning each comparator using the **complete deployed pipeline** in three expanding chronological source-team 2020 folds, including reset sequential residual adaptation within each validation block;
3. clarifying that the cross-team design is a two-team transportability assessment under sequential player-specific adaptation;
4. adding a main-text eligibility flow, decile calibration curves, player-level heterogeneity plots, clearer uncertainty statements, and repository-level reporting documentation; and
5. providing a repository-relative, one-command reproduction workflow with numerical verification.

## Source data and attribution

The original SoccerMon `subjective.zip` archive is **not redistributed** here. Obtain it from the official Zenodo record and comply with its licence and citation requirements:

- SoccerMon source data: https://doi.org/10.5281/zenodo.10033832

This repository contains researcher-generated code, manuscript files, figures, tables, and non-identifying summary reference outputs only.

## Quick reproduction

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python code\run_all.py --data-zip "C:\path\to\subjective.zip"
```

### macOS/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python code/run_all.py --data-zip /path/to/subjective.zip
```

A full run uses 2,000 player-cluster bootstrap resamples and verifies the generated summary outputs against the archived reference tables. Expected outputs are written to `outputs/analysis/` and are ignored by Git.

For a faster smoke test only, add `--bootstrap-resamples 200 --skip-verification`. This does not reproduce the manuscript confidence intervals.

## Overleaf

This package can also be uploaded to Overleaf. Use `main.tex` as the root document and compile with **pdfLaTeX + Biber**.

## Zenodo release status

This is the pre-archive package for GitHub release `v1.1.0`. After Zenodo creates a specific version DOI, insert it in `sections/05_declarations.tex`, update `CITATION.cff` if desired, and recompile the manuscript before submission.

## Licence

The code and researcher-generated reproducibility materials are released under the MIT Licence. This licence does not override the terms of the original SoccerMon data source.
