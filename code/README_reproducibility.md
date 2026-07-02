# Reproducibility notes

This folder contains the Python source files used during project development.

## Source data

The original SoccerMon `subjective.zip` file is not redistributed in this archive. Download it from the source Zenodo record cited in the manuscript:

```text
https://doi.org/10.5281/zenodo.10033832
```

Use of the source data remains subject to the original data licence and citation requirements.

## Suggested environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run order

1. Download `subjective.zip` separately.
2. Run `build_soccermon_nextday_dataset.py` to create the derived player-day analysis data.
3. Run the phase 3 scripts for robustness and sensitivity analyses.
4. Run `phase4_final_analysis.py` to generate final tables and figures.
5. Compare generated outputs with the manuscript tables and figures before release.

## Important implementation note

The frozen analysis scripts retain project-path variables from the analysis environment. Before public release, update those paths to local project directories and verify that the scripts reproduce the final outputs using the stated package versions. Do not claim complete end-to-end reproducibility until this verification has been performed.
