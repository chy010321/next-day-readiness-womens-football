# Reproducibility guide

## Requirements

- Python 3.11
- The official SoccerMon `subjective.zip` archive
- Packages listed in `requirements.txt`

## Full reproduction

```bash
python code/run_all.py --data-zip /path/to/subjective.zip --verify-source-hash
```

The command:

1. checks the source archive fingerprint when requested;
2. generates the canonical Figure 1;
3. builds the player-day calendar panel and primary paired complete-case cohort;
4. tunes P0, P1, P2, and P1m using expanding source-team 2020 folds;
5. evaluates 2021 within-team and bidirectional cross-team settings using past-only residual updates;
6. generates non-identifying tables/figures; and
7. verifies aggregate reference outputs when 2,000 bootstrap resamples are used.

The original data and individual prediction files are not committed. Locally generated output is written beneath `outputs/` and ignored by Git.
