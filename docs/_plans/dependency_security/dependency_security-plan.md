# Dependency Security Plan

## Status

Initial CI workflow implemented and baseline runs passed on the PR branch and `main`.

## Next

Review Trivy output for actual high/critical findings, then decide whether Trivy should remain report-only or start blocking.

## Phase A: Baseline CI Security Scan

1. [x] Add a GitHub Actions security workflow for pull requests, `main`, and scheduled runs.
2. [x] Add a Trivy filesystem scan for the repository with `HIGH,CRITICAL` severity.
3. [x] Keep the first filesystem scan output readable and low-noise.

## Phase B: Docker Image Scan

1. [x] Build the local Django Docker image in the security workflow.
2. [x] Scan the built image with Trivy after the build completes.
3. [x] Include OS and library vulnerabilities while ignoring unfixed issues where appropriate.

## Phase C: Rollout Tightening

1. [ ] Review first-run Trivy findings and separate real fixes from baseline noise.
2. [ ] Decide whether Trivy should remain non-blocking or fail on `HIGH,CRITICAL`.
3. [ ] Record any intentionally ignored findings in a small, reviewable allowlist.

## Phase D: GitHub Dependency Review

1. [x] Add GitHub Dependency Review Action for pull requests after Trivy is working.
2. [x] Configure it as a PR dependency-diff check for this public GitHub repo.
3. [x] Keep it secondary to Trivy rather than treating it as the main scanner.

## Phase E: Socket.dev

1. [x] Add Socket.dev selectively for npm supply-chain behaviour checks.
2. [x] Keep the configuration focused on actionable npm risk for this repo.

## Phase F: README Badge

1. [x] Add the Security workflow badge to the root README.

## Phase G: Optional OSV-Scanner

1. [ ] Consider OSV-Scanner only after Trivy, GitHub Dependency Review, and Socket.dev are in place.
2. [ ] Add it only if it provides useful dependency vulnerability signal without duplicating too much noise.
