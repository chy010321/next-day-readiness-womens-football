# After Zenodo mints the v1.1.2 DOI

Do not rewrite the published GitHub tag.

For the post-archive manuscript submission copy only:

1. Replace `[Zenodo version DOI for v1.1.2 to be inserted]` in `sections/05_declarations.tex` with the minted version DOI.
2. Update the citation text in `CITATION.cff` if a DOI field is desired for the submission copy.
3. Recompile `main.tex` and `supplementary.tex` with pdfLaTeX + Biber.
4. Render and inspect the PDFs to confirm the Figure 1 asset and Code availability text are readable.
5. Keep the final submission source/PDF archive separate from the immutable v1.1.2 GitHub release tag.
