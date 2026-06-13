# Renovate for Dependency Updates

Renovate tracks all dependency surfaces in this repository (Python via `pyproject.toml`/`uv.lock`, npm, Dockerfiles, and GitHub Actions). The configuration lives in `renovate.json` on the default branch.

## Operating Goal

Use Renovate aggressively enough to keep dependency work routine, but not so aggressively that PowerCRUD silently absorbs breaking changes or very fresh compromised package releases.

PowerCRUD is a Python package. Downstream projects do not inherit this repository's npm dependencies as npm transitive dependencies. The npm risk is still real because npm packages run during PowerCRUD's build and test workflow. A malicious npm dependency could affect CI, generated static assets, or the release artifact that downstream projects install from PyPI.

The policy is therefore:

- Automate low-risk dependency maintenance after a cooling-off period.
- Keep framework compatibility and breaking-change decisions manual.
- Keep dependency-update CI low-privilege.
- Avoid broad secret exposure in ordinary dependency PR workflows.

## Update Flow

When Renovate notices changes it opens pull requests:

- The first PR is an onboarding PR confirming the config and activating scheduled runs.
- Subsequent PRs group updates by ecosystem (Python packages, npm packages, Docker images, GitHub Action versions).

Every Renovate PR triggers our shared `Run Test Matrix` workflow through `.github/workflows/pr_tests.yml`, ensuring Python/Django compatibility stays intact.

## Automerge Policy

Patch and minor updates can automerge when all of these are true:

- The released version is at least seven days old.
- Renovate's internal release-age check has passed.
- The PR test matrix passes.
- The dependency is not covered by a manual-review exception.

Renovate uses PR automerge rather than branch automerge. Platform-native automerge is disabled so Renovate controls the cooldown, CI state, and merge decision.

Major updates are manual. Renovate labels them `major-upgrade` and requires dependency-dashboard approval before opening the PR.

## Manual Review Exceptions

Treat these updates as manual even when they are not major:

- Django, because it defines PowerCRUD's public compatibility matrix.
- Lockfile maintenance, because it can refresh transitive dependency versions without a direct manifest update.

For major updates, a human should identify the package role, skim release notes for breaking changes, wait for CI, and decide whether local or staging-style validation is needed before merging.

## Supply-Chain Risk Controls

The main supply-chain risk is a newly published package version that is malicious or compromised. This matters most for npm because dependency lifecycle scripts can run during install, before PowerCRUD code starts.

PowerCRUD manages that risk with:

- `minimumReleaseAge: "7 days"` for patch and minor automerge candidates.
- `internalChecksFilter: "strict"` so updates do not get branches or PRs before the release-age check passes.
- `npm ci` in CI, so installs use the committed lockfile rather than resolving loosely.
- Manual lockfile maintenance, so transitive churn is visible before merge.

## CI Permissions and Secrets

Dependency PR CI should test and build, not deploy or publish.

The PR test workflows use explicit read-only `GITHUB_TOKEN` permissions. The reusable test matrix receives only the Codecov token instead of inheriting every repository secret.

Do not add deploy, publish, cloud, SSH, PyPI, npm, or production secrets to ordinary dependency-update CI.

## Operations

If Renovate stalls, check the [Mend portal](https://developer.mend.io/github/doctor-cornelius/django-powercrud) to confirm the app still has access to the `dr-cornelius` organization and resync repositories from the Mend dashboard.
