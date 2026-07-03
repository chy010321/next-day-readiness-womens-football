# Release steps - v1.1.2

1. Replace the repository contents with this v1.1.2 package on the default branch.
2. Confirm `figures/liuchengtu.png` and `docs/FIGURE1_ARTWORK_V1.1.2.md` are present.
3. Commit with:

   `Prepare v1.1.2 Figure 1 artwork and reproducibility revision`

4. Create the GitHub release:
   - Tag: `v1.1.2`
   - Target: `main`
   - Title: `v1.1.2 - Figure 1 artwork and reproducibility revision`
   - Description: copy `docs/GITHUB_RELEASE_BODY_v1.1.2.md`
   - Do not mark as pre-release or draft.
5. Wait for Zenodo to archive the GitHub release and mint the version DOI.
6. Do not modify the published `v1.1.2` tag after DOI minting. Use `docs/AFTER_ZENODO_DOI_v1.1.2.md` for the post-archive submission copy.
