# Next-day readiness forecasting in elite women's football

**Release preparation version:** `v1.1.2`  
**Author:** Haoyang Cheng, Wuhan Sport University  
**ORCID:** 0009-0009-4123-2610

## Study purpose

This repository contains the manuscript source, figures, tables, analysis code, and reproducibility materials for:

> *Incremental Value of Daily Workload and Wellness Monitoring Beyond a Personalised Readiness-History Baseline for Next-Calendar-Day Readiness in Elite Women's Football*

The study tests whether a daily workload-wellness panel improves next-calendar-day self-reported readiness forecasts beyond a strong player-specific readiness-history baseline.

## v1.1.2 Figure 1 artwork and reproducibility release

This release replaces the manuscript Figure 1 with a content-rich methodological pipeline that makes the calendar-day forecasting task, source-team development, P0/P1 comparator structure, model-specific past-only residual personalisation, transportability assessment, and incremental-value estimand explicit. It does not introduce a new numerical analysis or alter the audited primary or wellness-item-missingness estimates.

The Figure 1 artwork is stored as `figures/liuchengtu.png`. Its methods-to-graphic mapping and review status are recorded in `docs/FIGURE1_ARTWORK_V1.1.2.md`. The previous compact scripted schematic is retained only as a legacy analytical artifact; it is no longer the manuscript Figure 1.

## Source data and attribution

The original SoccerMon `subjective.zip` archive is **not redistributed** here. Obtain it from the official Zenodo record and comply with its licence and citation requirements:

- SoccerMon source data: <https://doi.org/10.5281/zenodo.10033832>

This repository contains researcher-generated code, manuscript files, figures, tables, and non-identifying summary reference outputs only.

## Quick reproduction

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python code/run_all.py --data-zip "C:\path\to\subjective.zip" --verify-source-hash
```

### macOS/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python code/run_all.py --data-zip /path/to/subjective.zip --verify-source-hash
```

A full run uses 2,000 player-cluster bootstrap resamples and verifies generated non-identifying summary outputs against the archived reference tables. Expected outputs are written to `outputs/analysis/` and are ignored by Git.

For a faster smoke test only, add `--bootstrap-resamples 200 --skip-verification`. This does not reproduce manuscript confidence intervals.

## Overleaf

Upload the repository or its LaTeX files to Overleaf. Use `main.tex` as the root document and compile with **pdfLaTeX + Biber**. Compile `supplementary.tex` separately for the supplementary material.

## Zenodo and GitHub release status

This is the pre-archive package for GitHub release `v1.1.2`. Creating that GitHub Release will allow the linked Zenodo integration to mint a version-specific DOI. The tagged archive intentionally does not contain its own DOI; follow `docs/AFTER_ZENODO_DOI_v1.1.2.md` to insert the minted DOI only in the post-archive submission copy or default branch.

## Licence

The code and researcher-generated reproducibility materials are released under the MIT Licence. This licence does not override the terms of the original SoccerMon data source.


## Manuscript full-text revision included in this package

The v1.1.1 multi-pass editorial and reporting revision is retained in this v1.1.2 package. It clarifies the calendar-day prediction time point, paired complete-case estimand, target-team residual updating, bootstrap interpretation, missingness scope, continuous prediction range, and the limitations of numeric calendar encodings. It does **not** introduce new numerical analyses. The v1.1.2 release replaces the Figure 1 workflow graphic; see `docs/FIGURE1_ARTWORK_V1.1.2.md`.
