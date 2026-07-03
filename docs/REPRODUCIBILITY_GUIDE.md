# Reproducibility guide

## Scope

This release reproduces the final analyses using the original SoccerMon `subjective.zip` archive. The original archive is not included because it is governed by the source dataset's licence and attribution requirements.

## Required local inputs

- Python 3.11
- The official SoccerMon `subjective.zip` archive downloaded separately from https://doi.org/10.5281/zenodo.10033832

## Install and run

Use either `requirements.txt` with a virtual environment or `environment.yml` with conda. Then run:

```bash
python code/run_all.py --data-zip /path/to/subjective.zip
```

The command:

1. builds the full athlete-day panel and the primary 7-day-history complete-case cohort;
2. runs full-pipeline chronological tuning, primary evaluation, flow/missingness reporting, calibration figures, and missingness-aware sensitivity analysis;
3. compares generated summary results to `reproducibility/expected_outputs/`.

## Expected runtime

A full analysis uses 2,000 player-cluster bootstrap resamples and may require several minutes depending on hardware. The command uses a fixed random seed and should reproduce the archived summary values to numerical tolerance.

## Generated files

The default output directory is `outputs/`:

```text
outputs/
├── phase1/
│   ├── soccermon_next_day_readiness_full_panel.csv
│   └── soccermon_next_day_readiness_primary_pairs.csv
└── analysis/
    ├── Table3_primary_tuned_performance.csv
    ├── TableS1_inner_time_tuning_summary_primary.csv
    ├── TableS2_incremental_differences_tuned.csv
    ├── TableS7_missingness_aware_performance.csv
    ├── TableS8_missingness_aware_incremental_differences.csv
    ├── figures/
    └── supplementary/
```

The generated files remain local and are ignored by Git.
