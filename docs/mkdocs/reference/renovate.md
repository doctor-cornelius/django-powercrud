# Renovate for Dependency Updates

Renovate tracks all dependency surfaces in this repository (Python via `pyproject.toml`/`uv.lock`, npm, Dockerfiles, and GitHub Actions). The configuration lives in `renovate.json` on the default branch.

When Renovate notices changes it opens pull requests:

- The first PR is an onboarding PR confirming the config and activating scheduled runs.
- Subsequent PRs group updates by ecosystem (Python packages, npm packages, Docker images, GitHub Action versions).

Every Renovate PR triggers our shared `Run Test Matrix` workflow through `.github/workflows/pr_tests.yml`, ensuring Python/Django compatibility stays intact.

Patch and minor updates can automerge after a seven-day release-age delay and passing CI. Renovate uses PR automerge rather than branch automerge, and platform-native automerge is disabled so the cooldown and CI state stay under Renovate control.

Major updates are manual. Renovate labels them `major-upgrade` and requires dependency-dashboard approval before opening the PR.

Treat these updates as manual even when they are not major:

- Django, because it defines PowerCRUD's public compatibility matrix.
- Lockfile maintenance, because it can refresh transitive dependency versions without a direct manifest update.

The PR test workflows use explicit read-only `GITHUB_TOKEN` permissions. Do not add deploy, publish, or production secrets to dependency-update CI.

If Renovate stalls, check the [Mend portal](https://developer.mend.io/github/doctor-cornelius/django-powercrud) to confirm the app still has access to the `dr-cornelius` organization and resync repositories from the Mend dashboard.
