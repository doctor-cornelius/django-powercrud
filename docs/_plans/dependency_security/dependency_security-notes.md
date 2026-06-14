# Dependency Security Notes

## Goal

Add simple, low-maintenance CI security checks for dependency and container risk.

## Current State

- Renovate already applies a release delay and CI-gated automerge for patch/minor updates.
- GitHub Actions runs Python/Django matrix tests and Playwright smoke checks.
- The new Security workflow builds and scans the Docker image with Trivy.
- The repo commits `uv.lock`, `package-lock.json`, Docker config, and Django constraint files.
- The repo is public on GitHub, so GitHub Dependency Review Action is available without paid GitHub Advanced Security.
- Dependency Graph is enabled, so GitHub Dependency Review now runs successfully.
- The root README has a Security workflow badge.

## Tool Disposition

| # | Tool / control | Use? | Where | Why |
| -: | --- | --- | --- | --- |
| 1 | Renovate release delay | Yes | Renovate config | Reduces risk from fresh poisoned releases. |
| 2 | CI test/build gate | Yes | GitHub Actions | Prevents automerge unless the app still works. |
| 3 | Trivy | Yes, highest priority | CI | Best fit for Dockerised projects: scans repo, lockfiles, Docker image, and OS packages. |
| 4 | GitHub Dependency Review | Yes, after Trivy | GitHub public repos | PR-native dependency diff check for newly introduced dependency risk. |
| 5 | Socket.dev | Yes, selective | npm dependency checks | Adds npm supply-chain behaviour signal given current npm poisoning risk. |
| 6 | OSV-Scanner | Optional | CI | Second opinion focused on open-source dependency vulnerabilities. |

## Trivy Rollout Decisions

- Keep Trivy in CI only; do not add it to Python or npm project dependencies.
- Scan both the repository/filesystem and the built Docker image.
- Keep `HIGH,CRITICAL` report scans so baseline detail remains visible.
- Add critical-only gate scans so CI fails on `CRITICAL` findings.
- Keep `HIGH` report-only until baseline findings are reviewed.

## First Baseline Findings

- Filesystem scan found 6 high findings and 0 critical findings in `uv.lock`.
- The filesystem highs were for `tornado` and `urllib3`.
- Image scan found 11 high findings and 0 critical findings.
- The image highs included `cross-spawn`, `glob`, `minimatch`, and `tar` findings in npm/package metadata.
- Socket Firewall passed and reported 0 npm install vulnerabilities.
- Dependency Review passed and found no high-or-higher vulnerable dependency additions in the PR diff.

## High Finding Audit Approach

- Split the audit into two read-only lanes: Python lockfile findings and npm/image findings.
- For Python findings, identify whether vulnerable packages are app/runtime dependencies or dev/test/docs transitive dependencies and whether Renovate can update them safely.
- For npm/image findings, identify whether vulnerable packages come from this repo's `package-lock.json`, built `node_modules`, or Node/npm tooling bundled into the Docker image.
- Use the audit to choose fix, defer, or allowlist rather than blocking all `HIGH` findings immediately.

## High Finding Audit Outcome

- Python highs are stale transitive tooling entries in `uv.lock`, not core runtime dependencies.
- `tornado` comes through `ipykernel -> jupyter-client`; refresh to at least `6.5.5`.
- `urllib3` comes through docs/test tooling via `requests`; refresh to `2.7.0` to clear the listed highs.
- Python lockfile fix applied on `security/dependency-hardening`: `tornado` `6.5.2` to `6.5.7` and `urllib3` `2.5.0` to `2.7.0`.
- npm/image highs are bundled npm tooling inside the Docker image, not this repo's `package-lock.json`.
- Trivy pointed those findings at `/usr/lib/node_modules/npm/node_modules/...` for `cross-spawn`, `glob`, `minimatch`, and `tar`.
- The project-installed image `node_modules` tree had no npm vulnerabilities in the Trivy run.
- Docker image fix applied on `security/dependency-hardening`: move NodeSource from `node_20.x` to `node_22.x`.
- Remaining validation: rebuild through the Security workflow and confirm the bundled npm findings clear or reduce.

## Deferred

- Decide whether OSV-Scanner should run as PR-only, scheduled-only, or not at all after Trivy, GitHub Dependency Review, and Socket.dev are in place.
- Decide whether any remaining high findings after the lockfile and Docker image updates need a documented allowlist.
- Record any intentionally ignored Trivy findings in a small, reviewable allowlist instead of burying them in workflow logic.
