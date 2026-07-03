# Analysis code

Run the complete reproduction from the repository root:

```bash
python code/run_all.py --data-zip /path/to/subjective.zip --verify-source-hash
```

- `check_source_hash.py`: optionally verifies the validated official source archive fingerprint.
- `make_study_design_figure.py`: generates the canonical Figure 1 asset.
- `build_soccermon_nextday_dataset.py`: converts official SoccerMon subjective files into a player-day panel and primary 7-day-history cohort.
- `final_analysis.py`: complete-pipeline chronological tuning, primary evaluation, Figure 2 eligibility flow, calibration curves, missingness summaries, and wellness-item-missingness sensitivity analysis.
- `run_all.py`: one-command orchestrator.
- `verify_outputs.py`: checks non-identifying aggregate outputs against archived reference values.

The `alpha=0` candidate is implemented with `LinearRegression()` to match the stated unpenalised linear-model limit; positive-alpha candidates use ridge regression.

- `make_eligibility_flow_figure.py` creates the canonical Figure 2 eligibility-flow artwork from validated aggregate counts; the full analysis independently regenerates the same plot from the panel.
