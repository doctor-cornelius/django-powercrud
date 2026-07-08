# Package Release Gates Plan

## Status

Runtime-package dependency review is now the only new required merge gate. Phase D cleanup is removing redundant post-merge test/security reruns.

## Next

Split `Dependency Review` into one required runtime-package check and one advisory dev/local-repo check. Leave Socket, Trivy, Docker image scanning, and release-tag security changes deferred.

## Phase A: Decide Merge Gates

1. [x] Keep the existing test matrix and Playwright smoke checks as required PR checks.
2. [x] Add `Dependency Review / Runtime Package` as the required dependency check for PR merge.
3. [x] Keep `Dependency Review / Dev and Local Repo` advisory for local sample-app, test, docs, and contributor tooling risk.
4. [x] Keep `Socket Firewall` advisory for now; do not require a formal 7-day pass window before ordinary PowerCRUD package work can merge.
5. [x] Keep Docker-image scanning out of package merge gates unless a separate deployment policy needs it.

## Phase B: Split Security Signal

1. [x] Configure `Dependency Review / Runtime Package` for runtime dependency scope and high-severity failures.
2. [x] Configure `Dependency Review / Dev and Local Repo` for development and unknown dependency scopes, but do not require it.
3. [x] Keep package-relevant dependency checks easy to require in the `main` ruleset.
4. [x] Keep Docker-image vulnerability checks advisory, scheduled, or deployment-specific.
5. [x] Keep Trivy checks non-required until filesystem/package and Docker-image results are separated and reviewed.

## Phase C: Align Release Safety

1. [x] Rely on release PR gates plus the existing tag-time test matrix as the first release-safety layer.
2. [x] Ensure the release workflow blocks publishing on test failures.
3. [x] Ensure release blocking checks match the actual PyPI package risk, not unrelated container risk.
4. [x] Defer adding release-tag dependency/security jobs until the PR gates are stable and a concrete gap remains.

## Phase D: Remove Redundant Main Push Work

1. [x] Decide whether PR checks are strong enough to stop rerunning the same test workflow on `main` pushes.
2. [x] Keep scheduled security scans for changing vulnerability databases.
3. [x] Remove only redundant post-merge checks after the PR and release gates are agreed.

## Deferred Until Later

1. [ ] Decide whether `Socket Firewall` should become required after it has a stable record across dependency PRs.
2. [ ] Decide whether any split Trivy filesystem/package check should become required.
3. [ ] Decide whether Docker image scanning needs a separate deployment gate outside the PyPI package merge path.
4. [ ] Decide whether shipped frontend asset supply-chain risk needs a separate gate beyond Dependency Review scopes.
