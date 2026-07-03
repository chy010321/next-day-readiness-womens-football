# Pre-submission checklist - v1.1.2

## GitHub and Zenodo release

- [ ] Confirm `figures/liuchengtu.png` is the canonical Figure 1 asset and is referenced in `sections/02_methods.tex`.
- [ ] Create and publish GitHub tag `v1.1.2`.
- [ ] Use `docs/GITHUB_RELEASE_BODY_v1.1.2.md` as the GitHub release description.
- [ ] Confirm Zenodo mints the v1.1.2 version DOI.
- [ ] Do not rewrite the published v1.1.2 tag after DOI minting.

## Post-archive submission copy

- [ ] Insert the minted DOI only in the separate post-archive submission copy, following `docs/AFTER_ZENODO_DOI_v1.1.2.md`.
- [ ] Compile `main.tex` and `supplementary.tex` with pdfLaTeX + Biber.
- [ ] Render and inspect the main PDF, especially Figure 1, caption, and Code availability statement.
- [ ] Confirm that the code-archive version and manuscript Code availability text agree.
- [ ] Retain the scope/limitations wording: two-team transportability, report-complete days, self-reported readiness target, calendar-day timing, and no formal practical-equivalence claim.
- [ ] Retain the content boundary: v1.1.2 changes Figure 1 and documentation only; it does not introduce new numerical analyses.
