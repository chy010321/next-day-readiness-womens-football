# Expected summary outputs

This folder contains non-identifying, summary-level numerical outputs used by `code/verify_outputs.py` to confirm an end-to-end run. It does **not** include the original SoccerMon archive, raw player-day data, or individual predictions.

The verification command compares generated tables against these archived reference values. The release uses a fixed random seed and 2,000 player-cluster bootstrap resamples.
