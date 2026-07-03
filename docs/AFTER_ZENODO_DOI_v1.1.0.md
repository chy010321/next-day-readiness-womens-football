# After Zenodo generates the v1.1.0 DOI

1. Copy the **specific version DOI** from Zenodo (not the concept DOI).
2. Open `sections/05_declarations.tex`.
3. Replace the v1.1.0 archive placeholder sentence with:

```latex
The analysis code, manuscript source, figures, tables, and non-identifying reproducibility materials for the final analysis are archived at Zenodo: \url{https://doi.org/10.5281/zenodo.XXXXXXXX}.
```

4. In `README.md`, replace the pre-archive note with the same DOI.
5. Optionally add the DOI to `CITATION.cff` as an identifier.
6. Recompile `main.tex` and `supplementary.tex` with **pdfLaTeX + Biber**.
7. Create a final DOI-linked Overleaf ZIP for journal submission.
