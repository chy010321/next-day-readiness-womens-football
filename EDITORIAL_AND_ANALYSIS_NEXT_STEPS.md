# Before final journal submission: required analysis upgrades

This reporting revision corrects manuscript claims that can be resolved from the archived v1.1.0 outputs. The following improvements require a full re-run of the source code on the original SoccerMon data and must not be represented as completed until new archived outputs are produced.

1. Re-encode weekday and month as categorical one-hot features or prespecified cyclical features; retune P1 and P2 within each source-team chronology.
2. Add benchmark models: naïve persistence (`y_t`), population-only P0, population-only P1, and a player-history/rolling-mean comparator.
3. Report cold-start performance stratified by the number of previously accumulated target-period residuals (0, 1--7, 8--27, and 28).
4. Run a bounded-prediction sensitivity analysis that clips final predictions to the 1--10 readiness range, reporting whether P1--P0 MAE conclusions change.
5. Build an availability analysis that distinguishes (a) days on which P0 could be deployed, (b) days on which P1 could be deployed, and (c) days with subsequently observed `t+1` outcomes. Do not infer deployment coverage solely from the retrospective evaluation cohort.
6. Version and archive all re-run code, processed outputs, figures, tables, and manuscript text together as a new reproducibility release before changing any numerical result in the paper.

## Why these upgrades matter

They address the remaining Q2-review risks: calendar coding, the explanatory value of residual updating, cold-start generalisability, the bounded outcome scale, and realistic monitoring availability.
