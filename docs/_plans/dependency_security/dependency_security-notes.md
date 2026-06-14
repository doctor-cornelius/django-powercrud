# Dependency Security Notes

## Goal

Add simple, low-maintenance CI security checks for dependency and container risk.

## Current State

- Renovate already applies a release delay and CI-gated automerge for patch/minor updates.
- GitHub Actions runs Python/Django matrix tests and Playwright smoke checks.
- CI does not currently build or scan the Docker image.
- The repo commits `uv.lock`, `package-lock.json`, Docker config, and Django constraint files.
- The repo is public on GitHub, so GitHub Dependency Review Action is available without paid GitHub Advanced Security.

## Tool Disposition

| # | Tool / control | Use? | Where | Why |
| -: | --- | --- | --- | --- |
| 1 | Renovate release delay | Yes | Renovate config | Reduces risk from fresh poisoned releases. |
| 2 | CI test/build gate | Yes | GitHub Actions | Prevents automerge unless the app still works. |
| 3 | Trivy | Yes, highest priority | CI | Best fit for Dockerised projects: scans repo, lockfiles, Docker image, and OS packages. |
| 4 | OSV-Scanner | Optional but useful | CI | Second opinion focused on open-source dependency vulnerabilities. |
| 5 | GitHub Dependency Review | Nice-to-have | GitHub public repos | PR-native dependency diff check. Less needed if Trivy and OSV already run. |
| 6 | Socket.dev | Selective | Mainly npm-heavy repos | Looks for suspicious npm supply-chain behaviour and may be useful given current npm poisoning risk. |

## Trivy Rollout Decisions

- Keep Trivy in CI only; do not add it to Python or npm project dependencies.
- Scan both the repository/filesystem and the built Docker image.
- Start with high-signal severities: `HIGH,CRITICAL`.
- Use a non-blocking first pass if existing vulnerability noise is present, then tighten once the baseline is understood.

## Deferred

- Decide whether OSV-Scanner should run as PR-only, scheduled-only, or not at all after the Trivy baseline is known.
- Decide whether Socket.dev adds enough npm-specific signal for this repo's frontend tooling dependency surface.
- Record any intentionally ignored Trivy findings in a small, reviewable allowlist instead of burying them in workflow logic.
