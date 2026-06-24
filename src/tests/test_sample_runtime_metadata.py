"""Tests for the bundled sample app runtime metadata footer."""

from pathlib import Path
from subprocess import CalledProcessError

import pytest
from django.urls import reverse
from importlib import metadata

from sample import context_processors
from sample.models import Author, Book


def _clear_metadata_caches():
    """Clear cached metadata helpers so each test controls its own inputs."""
    context_processors._package_version.cache_clear()
    context_processors._git_describe.cache_clear()
    context_processors._git_commit.cache_clear()


def _clear_metadata_environment(monkeypatch):
    """Remove runtime metadata env vars so fallback tests are deterministic."""
    for name in (
        "APP_ENV",
        "DJANGO_ENV",
        "DJANGO_LIFECYCLE_ENV",
        "APP_VERSION",
        "APP_COMMIT",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def clear_sample_metadata_caches():
    """Reset sample metadata caches around each test."""
    _clear_metadata_caches()
    yield
    _clear_metadata_caches()


def test_sample_app_meta_prefers_explicit_environment_values(monkeypatch):
    """Explicit runtime environment variables should win over computed values."""
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("APP_VERSION", "0.8.0a1")
    monkeypatch.setenv("APP_COMMIT", "abc1234")
    monkeypatch.setattr(
        context_processors.metadata,
        "version",
        lambda package: "0.7.13",
    )

    context = context_processors.app_meta(None)

    assert context == {
        "sample_app_env": "preview",
        "sample_package_version": "0.7.13",
        "sample_git_version": "0.8.0a1",
        "sample_git_commit": "abc1234",
    }, "Explicit sample app metadata environment values should be exposed unchanged."


def test_sample_app_meta_falls_back_to_git_and_pyproject(monkeypatch, tmp_path):
    """Local editable checkouts should fall back to pyproject and git metadata."""
    _clear_metadata_environment(monkeypatch)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "django-powercrud"\nversion = "0.8.0a1"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(context_processors, "PROJECT_ROOT", tmp_path)

    def fake_version(package):
        raise metadata.PackageNotFoundError(package)

    def fake_run(command, **kwargs):
        class Result:
            stdout = ""

        result = Result()
        if command[:3] == ["git", "describe", "--tags"]:
            result.stdout = "0.8.0a1-2-gabc1234-dirty\n"
            return result
        if command[:3] == ["git", "rev-parse", "--short"]:
            result.stdout = "abc1234\n"
            return result
        raise AssertionError(f"Unexpected git command: {command}")

    monkeypatch.setattr(context_processors.metadata, "version", fake_version)
    monkeypatch.setattr(context_processors.subprocess, "run", fake_run)

    context = context_processors.app_meta(None)

    assert context["sample_app_env"] == "dev", (
        "Missing environment metadata should default the sample app env to dev."
    )
    assert context["sample_package_version"] == "0.8.0a1", (
        "Editable checkouts should expose the pyproject package version."
    )
    assert context["sample_git_version"] == "0.8.0a1-2-gabc1234-dirty", (
        "Local checkouts should expose git describe output when available."
    )
    assert context["sample_git_commit"] == "abc1234", (
        "Local checkouts should expose the short git commit when available."
    )


def test_sample_app_meta_uses_safe_fallbacks_when_git_and_package_fail(
    monkeypatch, tmp_path
):
    """Runtime metadata should remain renderable when package and git lookups fail."""
    _clear_metadata_environment(monkeypatch)
    monkeypatch.setattr(context_processors, "PROJECT_ROOT", tmp_path)

    def fake_version(package):
        raise metadata.PackageNotFoundError(package)

    def fake_run(command, **kwargs):
        raise CalledProcessError(128, command)

    monkeypatch.setattr(context_processors.metadata, "version", fake_version)
    monkeypatch.setattr(context_processors.subprocess, "run", fake_run)

    context = context_processors.app_meta(None)

    assert context["sample_package_version"] == "unknown", (
        "Missing package metadata and pyproject should fall back to unknown."
    )
    assert context["sample_git_version"] == "dev", (
        "Failed git describe should fall back to dev."
    )
    assert context["sample_git_commit"] == "unknown", (
        "Failed git commit lookup should fall back to unknown."
    )


def test_sample_runtime_meta_places_login_before_version_badge():
    """The sample shell should show auth first, then runtime version metadata."""
    project_root = Path(__file__).resolve().parents[1]
    template_path = (
        project_root / "sample" / "templates" / "sample" / "_runtime_meta.html"
    )
    template = template_path.read_text(encoding="utf-8")

    assert 'class="dropdown dropdown-start"' in template, (
        "The sample auth dropdown should align from the top-left of the shell."
    )
    assert 'class="dropdown dropdown-end"' not in template, (
        "The sample auth dropdown should no longer sit on the far right."
    )
    assert template.index('class="dropdown dropdown-start"') < template.index(
        "django-powercrud {{ sample_package_version }}"
    ), "The auth control should render immediately before the runtime version badge."


@pytest.mark.django_db
def test_sample_home_full_page_includes_runtime_metadata_footer(client):
    """The sample home shell should include one persistent runtime metadata footer."""
    response = client.get(reverse("home"))

    assert response.status_code == 200, "The sample home page should render."
    response_text = response.content.decode()
    assert response_text.count('data-sample-runtime-meta="true"') == 1, (
        "The full-page sample home response should include exactly one metadata footer."
    )


@pytest.mark.django_db
def test_sample_powercrud_full_page_includes_runtime_metadata_footer(client):
    """PowerCRUD sample screens should include the shell-level metadata footer."""
    author = Author.objects.create(name="Runtime Metadata Author")
    Book.objects.create(
        title="Runtime Metadata Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9780000000990",
        pages=101,
    )

    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200, "The sample Book list should render."
    response_text = response.content.decode()
    assert response_text.count('data-sample-runtime-meta="true"') == 1, (
        "Full-page PowerCRUD sample responses should include one metadata footer."
    )


@pytest.mark.django_db
def test_sample_manual_static_full_page_includes_runtime_metadata_footer(client):
    """The manual-static sample shell should show the same metadata footer."""
    response = client.get(reverse("sample:manual-static-bigbook-list"))

    assert response.status_code == 200, "The manual-static Book list should render."
    response_text = response.content.decode()
    assert response_text.count('data-sample-runtime-meta="true"') == 1, (
        "The manual-static sample response should include one metadata footer."
    )


@pytest.mark.django_db
def test_sample_htmx_partial_does_not_render_runtime_metadata_footer(client):
    """HTMX partial responses should not duplicate the persistent shell footer."""
    response = client.get(reverse("home"), HTTP_HX_REQUEST="true")

    assert response.status_code == 200, "The sample home HTMX partial should render."
    response_text = response.content.decode()
    assert 'data-sample-runtime-meta="true"' not in response_text, (
        "HTMX partial responses should leave the shell-level metadata footer alone."
    )
