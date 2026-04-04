"""Tests for packaged frontend runtime assets and bundle compatibility."""

import json
from pathlib import Path

import powercrud


def test_package_runtime_assets_exist() -> None:
    """PowerCRUD should ship package-owned runtime JS and CSS at stable static paths."""
    package_root = Path(powercrud.__file__).resolve().parent

    runtime_js = package_root / "static" / "powercrud" / "js" / "powercrud.js"
    runtime_css = package_root / "static" / "powercrud" / "css" / "powercrud.css"

    assert runtime_js.is_file(), "Expected packaged runtime JS at powercrud/static/powercrud/js/powercrud.js"
    assert runtime_css.is_file(), "Expected packaged runtime CSS at powercrud/static/powercrud/css/powercrud.css"


def test_bundle_manifest_keeps_existing_entry_key() -> None:
    """The packaged Vite manifest should keep the historical entry key for compatibility."""
    package_root = Path(powercrud.__file__).resolve().parent
    manifest_path = package_root / "assets" / "manifest.json"

    assert manifest_path.is_file(), "Expected packaged Vite manifest at powercrud/assets/manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert (
        "config/static/js/main.js" in manifest
    ), "Expected manifest entry 'config/static/js/main.js' for backwards compatibility"


def test_runtime_css_themes_tomselect_with_daisyui_semantic_tokens() -> None:
    """Packaged runtime CSS should override TomSelect with daisyUI semantic theme tokens."""
    package_root = Path(powercrud.__file__).resolve().parent
    runtime_css = package_root / "static" / "powercrud" / "css" / "powercrud.css"

    css = runtime_css.read_text(encoding="utf-8")

    assert (
        "--pc-ts-control-bg: var(--color-base-100, #ffffff);" in css
    ), "TomSelect runtime CSS should derive control backgrounds from daisyUI base theme colors."
    assert (
        "--pc-ts-chip-bg: var(--color-neutral, #374151);" in css
    ), "TomSelect runtime CSS should derive multi-select chip backgrounds from daisyUI neutral colors."
    assert (
        "--pc-ts-option-active-bg: var(--color-primary, #3b82f6);" in css
    ), "TomSelect runtime CSS should derive active option backgrounds from daisyUI primary colors."
    assert (
        ".ts-wrapper .ts-control {" in css
    ), "TomSelect runtime CSS should include an explicit control override block."
    assert (
        ".ts-dropdown .active," in css
    ), "TomSelect runtime CSS should include an explicit active dropdown option override."
