#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
CURRENT_USER="${USER:-$(id -un)}"

# Keep Ruff cache inside the mounted project path in containers.
# Prefer /home/${CURRENT_USER}/${PROJECT_DIR} when available (e.g. /home/devuser/django_powercrud).
if [[ "${CURRENT_USER}" == "root" ]]; then
    # Avoid root-owned cache files in bind mounts.
    CACHE_ROOT="/tmp"
elif [[ -n "${PROJECT_DIR:-}" && -d "/home/${CURRENT_USER}/${PROJECT_DIR}" ]]; then
    CACHE_ROOT="/home/${CURRENT_USER}/${PROJECT_DIR}"
elif [[ -d "/home/devuser/django_powercrud" ]]; then
    CACHE_ROOT="/home/devuser/django_powercrud"
else
    CACHE_ROOT="${REPO_ROOT}"
fi

RUFF_CACHE_DIR="${RUFF_CACHE_DIR:-${CACHE_ROOT}/.ruff_cache}"

cd "${REPO_ROOT}"

if command -v uv >/dev/null 2>&1; then
    uv run --project "${REPO_ROOT}" --group dev --no-sync ruff check --cache-dir "${RUFF_CACHE_DIR}" --fix src
    uv run --project "${REPO_ROOT}" --group dev --no-sync ruff format --cache-dir "${RUFF_CACHE_DIR}" src
else
    ruff check --cache-dir "${RUFF_CACHE_DIR}" --fix src
    ruff format --cache-dir "${RUFF_CACHE_DIR}" src
fi
