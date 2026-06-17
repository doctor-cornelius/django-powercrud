"""Context processors for the bundled sample app."""

from functools import lru_cache
from importlib import metadata
import os
from pathlib import Path
import subprocess
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def app_meta(request):
    """Return runtime metadata displayed by the local sample app shell."""
    return {
        "sample_app_env": _first_env("APP_ENV", "DJANGO_ENV", "DJANGO_LIFECYCLE_ENV")
        or "dev",
        "sample_package_version": _package_version(),
        "sample_git_version": os.environ.get("APP_VERSION") or _git_describe(),
        "sample_git_commit": os.environ.get("APP_COMMIT") or _git_commit(),
    }


def _first_env(*names):
    """Return the first populated environment variable from names."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""


@lru_cache(maxsize=1)
def _package_version():
    """Return the installed package version or the local pyproject fallback."""
    try:
        return metadata.version("django-powercrud")
    except metadata.PackageNotFoundError:
        return _pyproject_version()


def _pyproject_version():
    """Return the local pyproject version when running from an editable checkout."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    try:
        project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]
    except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"
    return str(project.get("version") or "unknown")


@lru_cache(maxsize=1)
def _git_describe():
    """Return a human-readable git description for the current checkout."""
    return _git_output(["git", "describe", "--tags", "--always", "--dirty"], "dev")


@lru_cache(maxsize=1)
def _git_commit():
    """Return the short commit hash for the current checkout."""
    return _git_output(["git", "rev-parse", "--short", "HEAD"], "unknown")


def _git_output(command, fallback):
    """Run a git command in the project root and return a safe fallback on failure."""
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return fallback
    return result.stdout.strip() or fallback
