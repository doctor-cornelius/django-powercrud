"""Default DaisyUI style declarations for the compatible template pack."""

from typing import Any


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
            "extra_default": "btn-accent",
            "modal_attrs": (
                'data-powercrud-modal-trigger="true" '
                f"onclick=\"document.getElementById('{view.get_modal_id()[1:]}').showModal()\""
            ),
        },
    }
