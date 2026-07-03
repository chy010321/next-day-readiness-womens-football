# After Zenodo mints the v1.1.1 DOI

The immutable GitHub tag cannot contain a DOI that did not yet exist. This is expected.

1. Copy the version-specific DOI minted for `v1.1.1` by Zenodo.
2. On the GitHub default branch, update the `Code availability` paragraph in `sections/05_declarations.tex` to cite `version v1.1.1, DOI: ...`.
3. Optionally add the DOI and release date to `CITATION.cff` on the default branch.
4. Recompile the manuscript and supplementary PDFs for journal submission.
5. Do not re-tag the release and do not claim byte-for-byte identity between the immutable pre-mint archive and the submission PDF. The only intended difference is insertion of the self-referential version DOI.
