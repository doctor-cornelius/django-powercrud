# Renovate for Dependency Updates

Renovate tracks all dependency surfaces in this repository (Python via `pyproject.toml`/`uv.lock`, npm, Dockerfiles, and GitHub Actions). The configuration lives in `renovate.json` on the default branch.

When Renovate notices changes it opens pull requests:

- The first PR is an onboarding PR confirming the config and activating scheduled runs.
- Subsequent PRs group updates by ecosystem (Python packages, npm packages, Docker images, GitHub Action versions).

Every Renovate PR triggers our shared `Run Test Matrix` workflow through `.github/workflows/pr_tests.yml`, ensuring Python/Django compatibility stays intact. Merge PRs once the checks pass; major updates get a `major-upgrade` label for extra attention.

If Renovate stalls, check the [Mend portal](https://developer.mend.io/github/doctor-cornelius/django-powercrud) to confirm the app still has access to the `dr-cornelius` organization and resync repositories from the Mend dashboard.

