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

- Renovate release delay: already used. Keep it as the first supply-chain control against very fresh poisoned releases.
- CI test/build gate: already used for Python and Playwright checks. Verify dependency PRs remain gated by required checks.
- Trivy: implement first. It covers the widest surface for this Dockerised repo: repository filesystem, lockfiles, Docker image, OS packages, secrets, and config.
- GitHub Dependency Review: add after Trivy is working. This is a public GitHub repo, so the action can provide PR-native dependency diff checks without relying on paid security features.
- OSV-Scanner: optional later step. Use it only if it adds a useful open-source dependency vulnerability second opinion without duplicating Trivy noise.
- Socket.dev: optional later step. It is relevant to npm supply-chain behaviour, but it is not a Docker/image scanner and should not replace Trivy.

## Trivy Rollout Decisions

- Keep Trivy in CI only; do not add it to Python or npm project dependencies.
- Scan both the repository/filesystem and the built Docker image.
- Start with high-signal severities: `HIGH,CRITICAL`.
- Use a non-blocking first pass if existing vulnerability noise is present, then tighten once the baseline is understood.

## Deferred

- Decide whether OSV-Scanner should run as PR-only, scheduled-only, or not at all after the Trivy baseline is known.
- Decide whether Socket.dev adds enough npm-specific signal for this repo's frontend tooling dependency surface.
- Record any intentionally ignored Trivy findings in a small, reviewable allowlist instead of burying them in workflow logic.
