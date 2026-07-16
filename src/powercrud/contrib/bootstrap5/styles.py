"""Bootstrap 5 style declarations for the optional template pack."""

from typing import Any


_VIEW_HELP_TONES = {
    "accent": "primary",
    "base": None,
    "error": "danger",
    "info": "info",
    "neutral": "secondary",
    "primary": "primary",
    "secondary": "secondary",
    "success": "success",
    "warning": "warning",
}


def get_bootstrap5_view_help_style(color: str) -> str:
    """Return Bootstrap CSS variables for one portable view-help colour."""
    normalized = color.strip().lower()
    tone = normalized if normalized.startswith("#") else _VIEW_HELP_TONES[normalized]
    if tone is None:
        return (
            "--pc-view-help-border: var(--bs-border-color); "
            "--pc-view-help-summary-bg: var(--bs-tertiary-bg); "
            "--pc-view-help-summary-fg: var(--bs-body-color); "
            "--pc-view-help-content-bg: var(--bs-body-bg); "
            "--pc-view-help-content-fg: var(--bs-secondary-color);"
        )
    colour = tone if normalized.startswith("#") else f"rgb(var(--bs-{tone}-rgb))"
    return (
        f"--pc-view-help-border: color-mix(in srgb, {colour} 35%, var(--bs-border-color)); "
        f"--pc-view-help-summary-bg: color-mix(in srgb, {colour} 18%, var(--bs-body-bg)); "
        "--pc-view-help-summary-fg: var(--bs-body-color); "
        f"--pc-view-help-content-bg: color-mix(in srgb, {colour} 8%, var(--bs-body-bg)); "
        "--pc-view-help-content-fg: var(--bs-secondary-color);"
    )


def get_bootstrap5_framework_styles(view: Any) -> dict[str, dict[str, Any]]:
    """Return a fresh Bootstrap 5 style mapping for one view."""
    return {
        "bootstrap5": {
            "base": "btn",
            "filter_attrs": {
                "text": {"class": "form-control form-control-sm"},
                "select": {"class": "form-select form-select-sm"},
                "multiselect": {"class": "form-select form-select-sm", "size": "5"},
                "date": {"class": "form-control form-control-sm", "type": "date"},
                "number": {"class": "form-control form-control-sm", "step": "any"},
                "time": {"class": "form-control form-control-sm", "type": "time"},
                "default": {"class": "form-control form-control-sm"},
            },
            "actions": {
                "View": "btn-info",
                "Edit": "btn-primary",
                "Delete": "btn-danger",
            },
            "action_group_item": "",
            "extra_default": "btn-success",
            "list_cell_link_class": "link-primary text-decoration-underline",
            "modal_attrs": 'data-powercrud-modal-trigger="true"',
        }
    }
