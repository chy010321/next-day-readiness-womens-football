# Release-package validation

This v1.1.0 package was validated before release packaging using the official SoccerMon `subjective.zip` archive obtained separately from the source Zenodo record.

Validation command:

```bash
python code/run_all.py --data-zip /path/to/subjective.zip --bootstrap-resamples 2000
```

Validation outcome:

- full calendar panel: 36,550 player-days;
- primary complete-case analytic cohort: 14,582 eligible player-day pairs;
- missingness-aware analytic cohort: 14,631 pairs;
- numerical verification passed for `Table3_primary_tuned_performance.csv`, `TableS2_incremental_differences_tuned.csv`, and `TableS8_missingness_aware_incremental_differences.csv`.

The automated runner uses repository-relative paths only. It does not redistribute the original SoccerMon archive or write participant-level source data into the repository.
