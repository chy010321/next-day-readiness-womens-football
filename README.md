# Next-day readiness forecasting in elite women's football

**Release preparation version:** `v1.1.1`  
**Author:** Haoyang Cheng, Wuhan Sport University  
**ORCID:** 0009-0009-4123-2610

## Study purpose

This repository contains the manuscript source, figures, tables, analysis code, and reproducibility materials for:

> *Incremental Value of Daily Workload and Wellness Monitoring Beyond a Personalised Readiness-History Baseline for Next-Calendar-Day Readiness in Elite Women's Football*

The study tests whether a daily workload-wellness panel improves next-calendar-day self-reported readiness forecasts beyond a strong player-specific readiness-history baseline.

## v1.1.1 correction release

This is a maintenance/correction release, not a new substantive reanalysis. It:

1. implements `alpha=0` as ordinary least squares (`LinearRegression`) rather than `Ridge(alpha=0)`;
2. renames the implemented 3-/7-day feature to **readiness-reporting rate**, correcting prior wellness-reporting terminology;
3. improves verification of tuning, performance, eligibility, missingness, and audit outputs;
4. corrects manuscript, table, figure, metadata, and release-documentation inconsistencies; and
5. regenerates canonical study-design and eligibility-flow figures using editable/vector-friendly Type 42 font embedding.

A clean rerun documented in `docs/AUDIT_AND_CORRECTIONS_v1.1.1.md` confirmed that all selected penalties and all reported primary and wellness-item-missingness sensitivity estimates remain unchanged. The code revision changes only the non-selected unpenalised candidate rows in the inner-tuning output.

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

This is the pre-archive package for GitHub release `v1.1.1`. Creating that GitHub Release will allow the linked Zenodo integration to mint a version-specific DOI. The tagged archive intentionally does not contain its own DOI; follow `docs/AFTER_ZENODO_DOI_v1.1.1.md` to insert the minted DOI only in the post-archive submission copy or default branch.

## Licence

The code and researcher-generated reproducibility materials are released under the MIT Licence. This licence does not override the terms of the original SoccerMon data source.
