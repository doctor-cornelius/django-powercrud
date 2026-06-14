# Dependency Security Plan

## Status

Initial CI workflow implemented, baseline findings fixed, and Trivy critical gates pass.

## Next

Review draft PR #140 and decide whether to mark it ready for merge.

## Phase A: Baseline CI Security Scan

1. [x] Add a GitHub Actions security workflow for pull requests, `main`, and scheduled runs.
2. [x] Add a Trivy filesystem scan for the repository with `HIGH,CRITICAL` severity.
3. [x] Keep the first filesystem scan output readable and low-noise.

## Phase B: Docker Image Scan

1. [x] Build the local Django Docker image in the security workflow.
2. [x] Scan the built image with Trivy after the build completes.
3. [x] Include OS and library vulnerabilities while ignoring unfixed issues where appropriate.

## Phase C: Rollout Tightening

1. [x] Review first-run Trivy findings and separate critical policy from high baseline noise.
2. [x] Keep high findings report-only for now and fail CI on critical findings.
3. [x] Confirm the critical-only gate passes on the hardening branch.
4. [x] Confirm no allowlist is needed for the current baseline.

## Phase D: High Finding Audit

1. [x] Audit Python `uv.lock` highs and identify whether they are runtime, test/dev, docs, or tool dependencies.
2. [x] Audit npm/image highs and identify whether they come from the repo npm tree or bundled Node/npm tooling in the Docker image.
3. [x] Decide per finding group: fix now, defer behind Renovate, or document as baseline/tooling noise.
4. [x] Update notes with the audit outcome and next fix branch, if needed.

## Phase E: Fix Audited High Findings

1. [x] Refresh `uv.lock` for the affected transitive Python packages.
2. [x] Update Docker image Node/npm tooling so bundled npm package highs are removed where practical.
3. [x] Rerun Security workflow and confirm high findings are reduced or cleared.
4. [x] Decide whether any remaining highs need a small documented allowlist.

## Phase F: GitHub Dependency Review

1. [x] Add GitHub Dependency Review Action for pull requests after Trivy is working.
2. [x] Configure it as a PR dependency-diff check for this public GitHub repo.
3. [x] Keep it secondary to Trivy rather than treating it as the main scanner.

## Phase G: Socket.dev

1. [x] Add Socket.dev selectively for npm supply-chain behaviour checks.
2. [x] Keep the configuration focused on actionable npm risk for this repo.

## Phase H: README Badge

1. [x] Add the Security workflow badge to the root README.

## Phase I: Optional OSV-Scanner

1. [ ] Consider OSV-Scanner only after Trivy, GitHub Dependency Review, and Socket.dev are in place.
2. [ ] Add it only if it provides useful dependency vulnerability signal without duplicating too much noise.
