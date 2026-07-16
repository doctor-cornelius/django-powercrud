"""Default DaisyUI style declarations for the compatible template pack."""

from typing import Any


def get_daisyui_view_help_style(color: str) -> str:
    """Return DaisyUI theme variables for one portable view-help colour."""
    normalized = color.strip().lower()
    if normalized == "base":
        return (
            "--pc-view-help-border: var(--color-base-300); "
            "--pc-view-help-summary-bg: var(--color-base-100); "
            "--pc-view-help-summary-fg: var(--color-base-content); "
            "--pc-view-help-content-bg: var(--color-base-100); "
            "--pc-view-help-content-fg: var(--color-base-content);"
        )
    if normalized.startswith("#"):
        tone = normalized
    else:
        tone = f"var(--color-{normalized})"
    return (
        f"--pc-view-help-border: color-mix(in srgb, {tone} 35%, var(--color-base-300)); "
        f"--pc-view-help-summary-bg: color-mix(in srgb, {tone} 18%, var(--color-base-100)); "
        "--pc-view-help-summary-fg: var(--color-base-content); "
        f"--pc-view-help-content-bg: color-mix(in srgb, {tone} 8%, var(--color-base-100)); "
        "--pc-view-help-content-fg: var(--color-base-content);"
    )


def get_daisyui_framework_styles(view: Any) -> dict[str, dict[str, Any]]:
    """Return a fresh legacy-compatible DaisyUI style mapping for one view."""
    return {
        "daisyUI": {
            "base": "btn ",
            "filter_attrs": {
                "text": {
                    "class": "input input-bordered input-sm w-full text-xs h-10 min-h-10"
                },
                "select": {
                    "class": "select select-bordered select-sm w-full text-xs h-10 min-h-10"
                },
                "multiselect": {
                    "class": "select select-bordered select-sm w-full text-xs",
                    "size": "5",
                    "style": "min-height: 8rem; max-height: 8rem; overflow-y: auto;",
                },
                "date": {
                    "class": "input input-bordered input-sm w-full text-xs h-10 min-h-10",
                    "type": "date",
                },
                "number": {
                    "class": "input input-bordered input-sm w-full text-xs h-10 min-h-10",
                    "step": "any",
                },
                "time": {
                    "class": "input input-bordered input-sm w-full text-xs h-10 min-h-10",
                    "type": "time",
                },
                "default": {
                    "class": "input input-bordered input-sm w-full text-xs h-10 min-h-10"
                },
            },
            "actions": {
                "View": "btn-info",
                "Edit": "btn-primary",
                "Delete": "btn-error",
            },
            "action_group_item": "join-item",
            "extra_default": "btn-accent",
            "list_cell_link_class": "link link-info",
            "modal_attrs": (
                'data-powercrud-modal-trigger="true" '
                f"onclick=\"document.getElementById('{view.get_modal_id()[1:]}').showModal()\""
            ),
        },
    }
