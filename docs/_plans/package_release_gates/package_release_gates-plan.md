# Package Release Gates Plan

## Status

Draft plan created. No workflow or ruleset changes have been made.

## Next

Decide which dependency/security checks should block PR merge and which should remain advisory or release-only.

## Phase A: Decide Merge Gates

1. [ ] Keep the existing test matrix and Playwright smoke checks as required PR checks.
2. [ ] Decide whether `Dependency Review` should become a required PR check.
3. [ ] Decide whether `Socket Firewall` should become a required PR check or remain advisory.
4. [ ] Keep Docker-image scanning out of package merge gates unless a separate deployment policy needs it.

## Phase B: Split Security Signal

1. [ ] Separate package dependency checks from Docker image checks in workflow naming and policy.
2. [ ] Keep package-relevant dependency checks easy to require in the `main` ruleset.
3. [ ] Keep Docker-image vulnerability checks advisory, scheduled, or deployment-specific.

## Phase C: Align Release Safety

1. [ ] Decide whether package-relevant dependency checks should run before publishing a release tag.
2. [ ] Ensure the release workflow blocks publishing on test failures.
3. [ ] Ensure release blocking checks match the actual PyPI package risk, not unrelated container risk.

## Phase D: Remove Redundant Main Push Work

1. [ ] Decide whether PR checks are strong enough to stop rerunning the same test workflow on `main` pushes.
2. [ ] Keep scheduled security scans for changing vulnerability databases.
3. [ ] Remove only redundant post-merge checks after the PR and release gates are agreed.
