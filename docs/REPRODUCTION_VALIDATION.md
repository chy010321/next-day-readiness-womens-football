# Reproduction validation

The v1.1.1 package validates generated non-identifying aggregate outputs with `code/verify_outputs.py`.

- Exact numerical checks cover all positive-alpha inner-tuning rows, primary performance, incremental differences, eligibility flow, missingness, missingness-sensitivity performance, and the audit JSON.
- Alpha=0 rows are deliberately checked for finite/plausible values rather than against v1.1.0 numerical reference values because v1.1.1 correctly substitutes ordinary least squares for `Ridge(alpha=0)`.
- The archived audit documented that the correction did not alter selected alphas or reported primary/sensitivity estimates.

Run the full workflow with `--bootstrap-resamples 2000` and omit `--skip-verification`.
