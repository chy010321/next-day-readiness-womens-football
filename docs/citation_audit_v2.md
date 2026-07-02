# Citation and bibliography audit v2.0

## Scope
This audit reviewed the manuscript's in-text citation keys, bibliography metadata, claim-to-source alignment, and final Biber/PDF compilation status. It is a focused citation audit for an original longitudinal forecasting article, not a systematic-review search.

## Corrections applied

1. **SoccerMon Zenodo record**: corrected the release year from 2024 to **2022** and added the release date (5 September 2022), version (`v1`), DOI, and URL.
2. **Campbell et al. (2020)**: added volume, issue, and pages (20(10):1395--1404).
3. **Wiik et al. (2019)**: replaced placeholder authors with the eight named conference authors and used the title spelling printed by the source record (“Peek”).
4. **Kulakou et al. (2022)**: replaced placeholder authors with the full seven-author list and completed issue/page metadata.
5. **Additional sources**: added Saw et al. (subjective monitoring), Thorpe et al. (soccer fatigue monitoring), Bergmeir et al. (time-series validation), Roberts et al. (temporal/hierarchical cross-validation), Janssen et al. (model updating), Debray et al. (clustered prediction-model reporting), and Shmueli (prediction versus explanation).
6. **Claim refinement**: replaced broad claims that women’s football is “underrepresented” and that open longitudinal datasets are “rare” with more defensible, source-aligned statements about population-specific context and SoccerMon’s openly available repeated monitoring structure.

## Citation-to-claim map

| Manuscript claim or methodological decision | Main supporting sources |
|---|---|
| Subjective wellness and internal-load monitoring are used in athlete monitoring | Halson 2014; Saw et al. 2016; Thorpe et al. 2015; Rago et al. 2020 |
| Wellness responses can exhibit dose-response and context dependence | Campbell et al. 2020; Campbell et al. 2021 |
| Individual variability should be considered in football monitoring | Oliva-Lozano et al. 2021 |
| Women’s football findings require population-specific interpretation | Baptista et al. 2022; Pettersen et al. 2022 |
| SoccerMon provenance, repeated subjective/objective data, and open dataset release | Midoglu et al. 2024; SoccerMon Zenodo v1 (2022) |
| Prior readiness forecasting on related SoccerMon/PmSys data | Wiik et al. 2019; Kulakou et al. 2022 |
| Temporal and participant-aware validation | Bergmeir et al. 2018; Roberts et al. 2017; Debray et al. 2023 |
| Calibration and transparent prediction reporting | Van Calster et al. 2019; Collins et al. 2024 |
| Updating/personalisation framing | Janssen et al. 2008 |
| Forecasting versus causal explanation | Shmueli 2010 |

## Interpretation safeguards retained in the manuscript

- The study is described as a **forecasting** analysis, not a causal analysis.
- The cross-team analyses are described as a **two-team transportability assessment**, not broad external validation.
- The result is not interpreted as showing that workload or wellness are unimportant; it is limited to incremental prediction beyond the specified personalised autoregressive baseline.
- The online residual adjustment is described as a light-touch operational updating strategy, not as a universally optimal updating procedure.

## Compilation checks to reproduce

```text
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

A final audit must confirm: (1) zero undefined citation warnings; (2) zero missing bibliography keys; (3) zero uncited bibliography entries; and (4) a non-empty reference list.
