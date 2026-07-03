# GitHub → Zenodo v1.1.0 release steps

1. Upload or replace the package contents at the repository root.
2. Confirm that `.zenodo.json` is visible at the repository root and its `version` is `1.1.0`.
3. Confirm that the repository does not contain `subjective.zip`, derived player-day files, individual predictions, local outputs, or build artefacts.
4. Commit with:

   ```text
   Release-ready v1.1.0 full-pipeline tuning and manuscript refinement
   ```

5. In Zenodo, open the GitHub integration page, click **Sync now**, and ensure the repository remains enabled.
6. In GitHub, open **Releases** → **Draft a new release**.
7. Create tag `v1.1.0` from the commit containing this package.
8. Use release title:

   ```text
   Next-day readiness forecasting code and reproducibility materials v1.1.0
   ```

9. Paste `docs/RELEASE_NOTES_v1.1.0.md` as the release notes and publish.
10. Wait for Zenodo to create a specific version DOI.
11. Verify version, author, affiliation, ORCID, MIT licence, source-data attribution, and absence of original SoccerMon files.
12. Copy the specific v1.1.0 DOI and use `docs/AFTER_ZENODO_DOI_v1.1.0.md` to update the manuscript.

Do not modify analysis code, generated figures, tables, or numerical results after publishing this version. Substantive future changes require a new GitHub release and a new Zenodo version DOI.
