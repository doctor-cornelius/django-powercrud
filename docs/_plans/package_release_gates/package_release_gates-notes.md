# Package Release Gates Notes

## Goal

Protect the PyPI package from untested code and newly introduced dependency risk without letting unrelated Docker image findings block normal package work.

The current recommendation is to improve package gates incrementally rather than making every security signal a hard blocker at once.

The next implementation slice should be small: split `Dependency Review` into a required runtime-package check and an advisory dev/local-repo check.

Implementation status: the Security workflow should expose `Dependency Review / Runtime Package` as the required candidate and `Dependency Review / Dev and Local Repo` as an advisory signal. The `protect_main` ruleset still needs to be updated after the new check names are visible from a PR run.

## Current Situation

- `main` is protected by an active GitHub ruleset.
- PRs are required before changes can merge to `main`.
- Status checks are required, but the observed required PR checks were the test matrix and Playwright smoke checks.
- The Security workflow runs on pull requests and on pushes to `main`.
- The Security workflow currently mixes package-relevant checks with Docker-image checks.
- The active `protect_main` ruleset requires the Python/Django test matrix and Playwright smoke checks, but not `Dependency Review`.
- Recent Security and Pull Request Tests workflow runs were green on PR and `main` push events.
- GitHub Dependency Review can filter by dependency scope, but it does not directly know this repo's Hatch wheel boundary.

## Important Distinction

The package release risk is not the same as the Docker image risk.

Package-relevant checks:

- Python/Django test matrix.
- Playwright smoke checks for packaged frontend/runtime behaviour.
- GitHub `Dependency Review / Runtime Package`, because it reviews runtime dependency changes introduced by a PR.
- Possibly `Socket Firewall`, because the package includes frontend assets and npm install behaviour can expose supply-chain risk. This remains advisory for now.

Local repo and sample-app checks:

- `Dependency Review / Dev and Local Repo`, because optional, development, docs, test, and npm dependencies can affect contributors or users running the sample app locally.
- This check should be visible but not required at first.

Less relevant to PyPI package gating:

- Docker image OS/package vulnerability scanning.
- Vulnerabilities from globally installed Docker image tooling that is not included in the published Python package.

## Plan Phases

### Phase A: Decide Merge Gates

The safest small step is to keep tests required and make only the runtime-package dependency review required.

`Dependency Review / Runtime Package` is the best first security gate because it is PR-native and focused on dependency changes that affect normal package consumers. It should fail on high-severity runtime dependency additions.

`Dependency Review / Dev and Local Repo` should run separately for development and unknown scopes, but it should remain advisory. It covers useful risk for people running the repo locally or trying the sample app without turning every dev-tool issue into a package merge blocker.

`Socket Firewall` may be useful, but it should not become a hard gate yet. PowerCRUD package work should not have to wait for a formal 7-day pass window before normal PRs can merge. Treat Socket as advisory signal first, then decide later whether its stability and value justify making it required.

Docker-image scanning should not be a required package merge gate unless the project explicitly wants container deployment health to block all package work.

### Phase B: Split Security Signal

The current Security workflow has useful checks, but the policy boundary is blurry because the job set combines package dependency checks and image scanning.

A clearer setup would make the check names match their policy meaning:

- `Dependency Review / Runtime Package`: required package dependency gate.
- `Dependency Review / Dev and Local Repo`: advisory local contributor/sample-app signal.
- `Socket Firewall`: npm supply-chain gate candidate.
- `Trivy Filesystem`: package/repo dependency scan candidate, if stable and scoped.
- `Trivy Docker Image`: advisory, scheduled, or deployment-specific.

This would let the `main` ruleset require package-relevant checks without requiring Docker-image findings.

Do not make any Trivy check required while filesystem/package and Docker-image findings are bundled under a single practical policy decision.

Dependency Review scope filtering is a pragmatic split, not a perfect shipped-artifact model. In this repo, npm packages are development dependencies, but built frontend assets can still ship inside `src/powercrud`. Treat that frontend asset supply-chain question as a deferred Socket or separate frontend-gate decision rather than overloading the first Dependency Review split.

### Phase C: Align Release Safety

If the real concern is "do not publish a bad package", the release workflow should also run the package-relevant gates before publishing.

The current release workflow already reruns the test matrix for release tags. The first release-safety layer should be release PRs passing the required PR gates plus the tag-time test matrix already in `publish.yml`.

Do not add Docker-image scanning to the release publish path. Defer release-tag dependency/security jobs until the required PR gates have settled and there is still a concrete release-only gap to close.

### Phase D: Remove Redundant Main Push Work

The workflows currently rerun after merge because they are configured for both `pull_request` and `push` to `main`.

If PR checks are required and branches must be current enough before merging, rerunning the same tests after the squash merge is mostly redundant.

Scheduled security scans should probably stay because vulnerability databases change even when code does not.

Do not remove post-merge checks until the required PR checks and release gates are agreed.

## Deferred Decisions

- Whether `Socket Firewall` should become required after a stable record across dependency PRs.
- Whether any split Trivy filesystem/package check is stable and package-relevant enough to require.
- Whether Docker image scanning needs a separate deployment policy outside the PyPI package release path.
- Whether release tags need additional dependency/security jobs after PR gates are stable.
- Whether shipped frontend asset supply-chain risk needs a separate gate beyond Dependency Review scopes.

## Open Questions

- Should `Dependency Review / Runtime Package` be added to `protect_main` in the same PR as the Security workflow split?
- What level of Socket Firewall failure history would justify promoting it later?
- Should Trivy be split into filesystem and Docker-image jobs before any Trivy check is required?
- Should release publishing require dependency checks in addition to the existing release test matrix after PR gates are stable?
