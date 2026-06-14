# Dependency Security Plan

## Status

Planning.

## Next

Create the minimal Trivy CI workflow, run it on a PR, and decide whether the first rollout should block merges.

## Phase A: Baseline CI Security Scan

1. [ ] Add a GitHub Actions security workflow for pull requests, `main`, and scheduled runs.
2. [ ] Add a Trivy filesystem scan for the repository with `HIGH,CRITICAL` severity.
3. [ ] Keep the first filesystem scan output readable and low-noise.

## Phase B: Docker Image Scan

1. [ ] Build the local Django Docker image in the security workflow.
2. [ ] Scan the built image with Trivy after the build completes.
3. [ ] Include OS and library vulnerabilities while ignoring unfixed issues where appropriate.

## Phase C: Rollout Tightening

1. [ ] Review first-run findings and separate real fixes from baseline noise.
2. [ ] Decide whether Trivy should remain non-blocking or fail on `HIGH,CRITICAL`.
3. [ ] Record any intentionally ignored findings in a small, reviewable allowlist.

## Phase D: Optional Follow-Ups

1. [ ] Consider OSV-Scanner only if it adds useful dependency coverage beyond Trivy.
2. [ ] Consider GitHub Dependency Review for PR dependency diffs.
3. [ ] Revisit Socket.dev only if npm risk becomes meaningful.
