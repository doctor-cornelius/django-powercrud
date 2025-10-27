---
date: 2025-10-26
categories:
  - dependencies
  - CI
---
# Automatically Updating Dependency Versions

Need to implement `dependabot` or `renovate` for automatically bumping versions to take account of dependency version increments. Also need to consider how to keep docker images and python versions updated.
<!-- more -->

## Objectives

- Keep Python, Node, Docker, and CI toolchain dependencies current with minimal manual effort.
- Use a dependency bot that works on both GitHub and GitLab free plans.
- Ensure every automated bump runs our test matrix before landing.
- Preserve our manual release flow (we still run `new_release.sh` to bump package versions).

## Expectations & tooling choice

- **Renovate** is preferred over Dependabot because it supports both GitHub and GitLab (and even self-hosting) on the free tiers. Dependabot only works on GitHub.
- Renovate’s “poetry” manager understands `pyproject.toml`/PEP 621 metadata even when `uv` generates the lockfile, so it can propose `pyproject.toml` + `uv.lock` updates without issue.
- Renovate opens pull requests on a schedule we choose (daily/weekly) and our GitHub Actions matrix runs on those PRs. We can enable auto-merge once we’re confident.
- Renovate will not bump our own package version automatically—that still happens in `new_release.sh` after we merge the dependency PR.

## Plan

1. ✅ **Configure Renovate**  
   Add a repo-level `renovate.json` enabling the poetry/uv manager, Dockerfile updates, and GitHub Actions dependency checks. Set schedule, labels, and optional automerge rules.

2. ✅ **Enable the bot**  
   Install the Renovate GitHub app (or run the Renovate Runner on GitLab using the same config). Verify it can open PRs.

3. ✅ **Wire CI safeguards**  
   Ensure Renovate PRs automatically invoke our test matrix by adding a thin wrapper workflow that triggers on `pull_request`/`push` and reuses `.github/workflows/run_tests.yml`, so Python/Django compatibility remains guaranteed before merging.

4. **Observe & iterate**  
   Start with manual merges, refine grouping and automerge policies, and expand coverage (Docker images, Python base images) as needed.

5. **Document the flow**  
   Capture how Renovate feeds into releases (merge PR → run `new_release.sh`) in the project docs/blog once the setup is stable.
