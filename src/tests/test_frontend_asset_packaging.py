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


def test_runtime_css_exposes_tooltip_theme_variables() -> None:
    """Packaged runtime CSS should expose stable tooltip CSS variables and consume them."""
    package_root = Path(powercrud.__file__).resolve().parent
    runtime_css = package_root / "static" / "powercrud" / "css" / "powercrud.css"

    css = runtime_css.read_text(encoding="utf-8")

    assert (
        "--pc-tooltip-bg: var(--color-neutral, #272728);" in css
    ), "Tooltip runtime CSS should expose a background custom property that defaults to the daisyUI neutral token."
    assert (
        "--pc-tooltip-fg: var(--color-neutral-content, #ffffff);" in css
    ), "Tooltip runtime CSS should expose a foreground custom property that defaults to the daisyUI neutral-content token."
    assert (
        "--pc-tooltip-arrow: var(--pc-tooltip-bg);" in css
    ), "Tooltip runtime CSS should expose an arrow-color custom property that defaults to the tooltip background."
    assert (
        "--pc-tooltip-radius: var(--radius-field, 0.25rem);" in css
    ), "Tooltip runtime CSS should expose a border-radius custom property with a sensible field-radius default."
    assert (
        "--pc-tooltip-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);" in css
    ), "Tooltip runtime CSS should expose a subtle shadow custom property."
    assert (
        "background-color: var(--pc-tooltip-bg);" in css
    ), "Tooltip theme selectors should consume the tooltip background custom property instead of a hard-coded color."
    assert (
        "color: var(--pc-tooltip-fg);" in css
    ), "Tooltip theme selectors should consume the tooltip foreground custom property instead of a hard-coded color."
    assert (
        "color: var(--pc-tooltip-arrow);" in css
    ), "Tooltip arrow selectors should consume the tooltip arrow custom property."


def test_sample_bundle_imports_tooltip_override_css_after_powercrud_runtime_css() -> None:
    """The sample Vite entry should import app-level tooltip overrides after package runtime CSS."""
    entry_js = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "static"
        / "js"
        / "main.js"
    ).read_text(encoding="utf-8")

    powercrud_css_index = entry_js.index(
        "import '../../../powercrud/static/powercrud/css/powercrud.css'"
    )
    app_override_index = entry_js.index("import '@/css/app.custom.css'")

    assert (
        powercrud_css_index < app_override_index
    ), "Sample app CSS overrides should load after package runtime CSS so downstream :root tooltip variables take effect."


def test_sample_tooltip_override_css_uses_primary_sample_theme() -> None:
    """The sample app should demonstrate an active primary-token tooltip override."""
    sample_css = (
        Path(__file__).resolve().parents[1]
        / "config"
        / "static"
        / "css"
        / "app.custom.css"
    ).read_text(encoding="utf-8")

    assert (
        ":root {" in sample_css
    ), "Sample tooltip override CSS should include an active :root block so the sample app demonstrates downstream theming."
    assert (
        "--pc-tooltip-bg: var(--color-primary);" in sample_css
    ), "Sample tooltip override CSS should demonstrate the primary tooltip background token."
    assert (
        "--pc-tooltip-fg: var(--color-primary-content);" in sample_css
    ), "Sample tooltip override CSS should demonstrate the primary tooltip foreground token."
