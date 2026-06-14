# Dependency Security Notes

## Goal

Add simple, low-maintenance CI security checks for dependency and container risk.

## Current State

- Renovate already applies a release delay and CI-gated automerge for patch/minor updates.
- GitHub Actions runs Python/Django matrix tests and Playwright smoke checks.
- CI does not currently build or scan the Docker image.
- The repo commits `uv.lock`, `package-lock.json`, Docker config, and Django constraint files.

## Decisions

- Implement Trivy first because it can scan the repository, lockfiles, Docker image, OS packages, secrets, and config.
- Keep Trivy in CI only; do not add it to Python or npm dependencies.
- Start with high-signal severities: `HIGH,CRITICAL`.
- Use a non-blocking first pass if existing vulnerability noise is present, then tighten once the baseline is understood.

## Deferred

- Add OSV-Scanner only if a Trivy baseline shows useful room for a dependency-focused second opinion.
- Add GitHub Dependency Review only if this public GitHub repo benefits from PR-native dependency diff checks.
- Skip Socket.dev unless npm supply-chain risk becomes a larger part of this project.
