# How to create the v1.1.1 GitHub Release

1. Commit the contents of this package to the repository default branch.
2. Confirm that `README.md`, `.zenodo.json`, and `CITATION.cff` show version `1.1.1`.
3. In GitHub, open **Releases** and select **Draft a new release**.
4. Create tag `v1.1.1` from the commit containing this package.
5. Set the title to `v1.1.1 - reproducibility and reporting corrections`.
6. Paste the contents of `RELEASE_NOTES_v1.1.1.md` into the release body.
7. Publish the release.
8. Wait for Zenodo to create the version-specific DOI. Do not modify the published tag after the DOI is minted.
9. Update the default branch and journal-submission copy only as described in `AFTER_ZENODO_DOI_v1.1.1.md`.
