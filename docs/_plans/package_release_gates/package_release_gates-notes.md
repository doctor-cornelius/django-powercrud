# Package Release Gates Notes

## Goal

Protect the PyPI package from untested code and newly introduced dependency risk without letting unrelated Docker image findings block normal package work.

## Current Situation

- `main` is protected by an active GitHub ruleset.
- PRs are required before changes can merge to `main`.
- Status checks are required, but the observed required PR checks were the test matrix and Playwright smoke checks.
- The Security workflow runs on pull requests and on pushes to `main`.
- The Security workflow currently mixes package-relevant checks with Docker-image checks.

## Important Distinction

The package release risk is not the same as the Docker image risk.

Package-relevant checks:

- Python/Django test matrix.
- Playwright smoke checks for packaged frontend/runtime behaviour.
- GitHub `Dependency Review`, because it reviews dependency changes introduced by a PR.
- Possibly `Socket Firewall`, because the package includes frontend assets and npm install behaviour can expose supply-chain risk.

Less relevant to PyPI package gating:

- Docker image OS/package vulnerability scanning.
- Vulnerabilities from globally installed Docker image tooling that is not included in the published Python package.

## Plan Phases

### Phase A: Decide Merge Gates

The safest small step is to keep tests required and consider making `Dependency Review` required.

`Dependency Review` is the best first security gate because it is PR-native and focused on dependency changes. It should be less likely to block unrelated code changes than a full image scanner.

`Socket Firewall` may be useful, but it should be observed for stability before making it a hard gate.

Docker-image scanning should not be a required package merge gate unless the project explicitly wants container deployment health to block all package work.

### Phase B: Split Security Signal

The current Security workflow has useful checks, but the policy boundary is blurry because the job set combines package dependency checks and image scanning.

A clearer setup would make the check names match their policy meaning:

- `Dependency Review`: package dependency gate candidate.
- `Socket Firewall`: npm supply-chain gate candidate.
- `Trivy Filesystem`: package/repo dependency scan candidate, if stable and scoped.
- `Trivy Docker Image`: advisory, scheduled, or deployment-specific.

This would let the `main` ruleset require package-relevant checks without requiring Docker-image findings.

### Phase C: Align Release Safety

If the real concern is "do not publish a bad package", the release workflow should also run the package-relevant gates before publishing.

The current release workflow already reruns the test matrix for release tags. The open policy question is whether release publishing should also require dependency/security checks that reflect PyPI package risk.

### Phase D: Remove Redundant Main Push Work

The workflows currently rerun after merge because they are configured for both `pull_request` and `push` to `main`.

If PR checks are required and branches must be current enough before merging, rerunning the same tests after the squash merge is mostly redundant.

Scheduled security scans should probably stay because vulnerability databases change even when code does not.

Do not remove post-merge checks until the required PR checks and release gates are agreed.

## Open Questions

- Should `Dependency Review` become required immediately?
- Should `Socket Firewall` remain advisory until it has a longer stability record?
- Should Trivy be split into filesystem and Docker-image jobs before any Trivy check is required?
- Should release publishing require dependency checks in addition to the existing release test matrix?
