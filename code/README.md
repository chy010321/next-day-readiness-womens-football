# Analysis code

Run the complete reproduction from the repository root:

```bash
python code/run_all.py --data-zip /path/to/subjective.zip
```

The scripts use repository-relative paths. `run_all.py` creates `outputs/phase1/` and `outputs/analysis/` locally, then calls `verify_outputs.py` to compare non-identifying summary tables against the archived reference values.

- `build_soccermon_nextday_dataset.py`: converts official SoccerMon subjective files into a player-day panel and defines the primary 7-day-history cohort.
- `final_analysis.py`: full-pipeline chronological tuning, primary evaluation, eligibility flow, calibration curves, missingness summaries, and missingness-aware sensitivity analysis.
- `run_all.py`: one-command orchestrator.
- `verify_outputs.py`: checks key numerical outputs from a full 2,000-resample run.
