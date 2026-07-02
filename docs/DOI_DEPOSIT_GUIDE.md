# Create a permanent DOI for the final code archive

This guide creates a versioned DOI for the exact code and reproducibility materials used for submission. It does **not** upload or redistribute the original SoccerMon `subjective.zip` data file.

## What to upload

Create a GitHub repository containing this project, including:

- `code/`
- `docs/`
- `figures/`, `tables/`, and manuscript source files
- `README.md`
- `.zenodo.json`
- `CITATION.cff`
- `LICENSE`

Do not include:

- the original `subjective.zip` file;
- any raw SoccerMon data downloaded from Zenodo;
- private credentials, personal tokens, or local machine paths;
- LaTeX build artifacts such as `.aux`, `.log`, `.bbl`, or compiled PDFs.

## Step 1: Create a GitHub repository

1. Sign in to GitHub and choose **New repository**.
2. Suggested repository name: `next-day-readiness-womens-football`.
3. Select **Public** unless you have a reason to restrict code during review.
4. Do not initialise the repository with a README if you are uploading this folder as-is.
5. Upload the project files or push them using Git.

## Step 2: Check repository metadata

Before the first release, open and verify:

- `.zenodo.json`: title, version, creator name, ORCID, affiliation, source-data DOI, and license;
- `CITATION.cff`: GitHub citation information;
- `LICENSE`: MIT license for the code;
- `code/README_reproducibility.md`: run order and source-data instructions.

Edit the version number from `1.0.0` only if you deliberately use a different release tag.

## Step 3: Link GitHub to Zenodo

1. Sign in to Zenodo using your preferred account.
2. In Zenodo, open the profile menu and select **GitHub**.
3. Select **Sync now** if the repository is not listed.
4. Find `next-day-readiness-womens-football` and enable it with the repository toggle.

## Step 4: Create the archival release

1. Return to the repository on GitHub.
2. Open **Releases** and choose **Create a new release**.
3. Create tag `v1.0.0`.
4. Set release title to: `Next-day readiness forecasting code and reproducibility materials v1.0.0`.
5. Use the following release notes:

```text
Version 1.0.0 accompanies the manuscript:
"Does Daily Workload and Wellness Monitoring Add Incremental Value Beyond a Personalised Autoregressive Baseline for Next-Day Readiness? A Two-Team Temporal Study in Elite Women's Football".

This release contains the manuscript source, data-construction scripts, analysis scripts, tables, figures, and reproducibility documentation. It does not redistribute the original SoccerMon dataset; users must obtain it from https://doi.org/10.5281/zenodo.10033832.
```

6. Publish the release.

Zenodo should archive the GitHub release automatically. Wait until the new Zenodo record appears and verify that its files and metadata are correct.

## Step 5: Copy the DOI and update the manuscript

1. Open the Zenodo record created for `v1.0.0`.
2. Copy the DOI for that specific released version, not a draft link.
3. Replace `[INSERT-ZENODO-DOI]` in `sections/05_declarations.tex`.
4. Recompile `main.tex` in Overleaf.

Example:

```tex
\url{https://doi.org/10.5281/zenodo.12345678}
```

## Step 6: Pre-submission check

Confirm that:

- the Zenodo record is public and resolves;
- the archived release matches the submitted analysis code;
- the author is listed as Haoyang Cheng with the correct ORCID;
- the original SoccerMon data DOI is cited and linked;
- no raw SoccerMon files or personal credentials were uploaded;
- the DOI in the manuscript matches the versioned release.

## Optional alternative: reserve DOI before uploading

If you want the DOI before the GitHub release is published, Zenodo also allows you to create a draft upload and reserve a DOI. This is useful only when you need to insert the DOI into files before publication. For this project, the GitHub-release method is simpler.
