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
