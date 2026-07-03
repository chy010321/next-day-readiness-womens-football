# Expected summary outputs

This folder contains non-identifying aggregate outputs used by `code/verify_outputs.py` to validate an end-to-end run. It does not include the original SoccerMon archive, raw player-day data, or individual predictions.

Version 1.1.1 checks all positive-alpha numerical reference rows exactly. Because alpha=0 is correctly reimplemented as ordinary least squares in this release, alpha=0 tuning rows are checked for finite, plausible values rather than against the v1.1.0 `Ridge(alpha=0)` reference values. The audited release confirms that all selected penalties and manuscript-facing results are unchanged.
