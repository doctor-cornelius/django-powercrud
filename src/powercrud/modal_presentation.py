"""Portable modal-presentation validation and rendering helpers.

The public configuration is deliberately semantic.  Template packs map the
normalized values to their own dialog classes and CSS at the presentation
boundary instead of exposing framework utility classes as a shared contract.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from django.utils.html import format_html


MODAL_PRESENTATION_DEFAULTS: dict[str, Any] = {
    "size": "default",
    "max_width": None,
    "max_height": "viewport",
    "scroll": "body",
    "fullscreen": False,
    "vertical_alignment": "center",
}
MODAL_PRESENTATION_KEYS = frozenset(MODAL_PRESENTATION_DEFAULTS)
MODAL_SIZES = frozenset({"compact", "default", "wide", "extra_wide"})
MODAL_SCROLL_MODES = frozenset({"body", "modal"})
MODAL_VERTICAL_ALIGNMENTS = frozenset({"top", "center"})
CSS_LENGTH_RE = re.compile(r"^\d+(?:\.\d+)?(?:px|rem|em|ch|%|vw|vh|dvw|dvh)$")


def validate_modal_css_length(value: Any, field_name: str) -> str:
    """Return one safe CSS length accepted by the portable modal contract."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty CSS length")
    normalized = value.strip().lower()
    if not CSS_LENGTH_RE.fullmatch(normalized):
        raise ValueError(
            f"{field_name} must use px, rem, em, ch, %, vw, vh, dvw, or dvh"
        )
    return normalized


def normalize_modal_presentation(
    value: Any,
    field_name: str,
    *,
    allow_none: bool = True,
) -> dict[str, Any] | None:
    """Validate a partial portable modal-presentation mapping.

    The returned mapping contains only supplied keys so callers can merge a
    trigger or bulk override over its view-level presentation deterministically.
    """
    if value is None:
        if allow_none:
            return None
        raise ValueError(f"{field_name} must be a mapping")
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping when provided")

    unknown_keys = set(value) - MODAL_PRESENTATION_KEYS
    if unknown_keys:
        raise ValueError(
            f"{field_name} contains unsupported keys: {', '.join(sorted(unknown_keys))}"
        )

    normalized: dict[str, Any] = {}
    if "size" in value:
        size = value["size"]
        if not isinstance(size, str) or size not in MODAL_SIZES:
            raise ValueError(
                f"{field_name}.size must be one of: {', '.join(sorted(MODAL_SIZES))}"
            )
        normalized["size"] = size

    if "max_width" in value:
        max_width = value["max_width"]
        normalized["max_width"] = (
            None
            if max_width is None
            else validate_modal_css_length(max_width, f"{field_name}.max_width")
        )

    if "max_height" in value:
        max_height = value["max_height"]
        if max_height == "viewport":
            normalized["max_height"] = "viewport"
        else:
            normalized["max_height"] = validate_modal_css_length(
                max_height,
                f"{field_name}.max_height",
            )

    if "scroll" in value:
        scroll = value["scroll"]
        if not isinstance(scroll, str) or scroll not in MODAL_SCROLL_MODES:
            raise ValueError(
                f"{field_name}.scroll must be one of: {', '.join(sorted(MODAL_SCROLL_MODES))}"
            )
        normalized["scroll"] = scroll

    if "fullscreen" in value:
        fullscreen = value["fullscreen"]
        if not isinstance(fullscreen, bool):
            raise ValueError(f"{field_name}.fullscreen must be True or False")
        normalized["fullscreen"] = fullscreen

    if "vertical_alignment" in value:
        vertical_alignment = value["vertical_alignment"]
        if (
            not isinstance(vertical_alignment, str)
            or vertical_alignment not in MODAL_VERTICAL_ALIGNMENTS
        ):
            raise ValueError(
                f"{field_name}.vertical_alignment must be one of: "
                f"{', '.join(sorted(MODAL_VERTICAL_ALIGNMENTS))}"
            )
        normalized["vertical_alignment"] = vertical_alignment
    return normalized


def resolve_modal_presentation(*presentations: Mapping[str, Any] | None) -> dict[str, Any]:
    """Merge validated partial modal presentations over the portable defaults."""
    resolved = MODAL_PRESENTATION_DEFAULTS.copy()
    for presentation in presentations:
        if presentation:
            resolved.update(presentation)
    return resolved


def modal_presentation_attributes(presentation: Mapping[str, Any] | None) -> str:
    """Return escaped semantic data attributes for a normalized presentation."""
    resolved = resolve_modal_presentation(presentation)
    return str(
        format_html(
            'data-powercrud-modal-size="{}" '
            'data-powercrud-modal-max-width="{}" '
            'data-powercrud-modal-max-height="{}" '
            'data-powercrud-modal-scroll="{}" '
            'data-powercrud-modal-fullscreen="{}" '
            'data-powercrud-modal-vertical-alignment="{}"',
            resolved["size"],
            resolved["max_width"] or "",
            resolved["max_height"],
            resolved["scroll"],
            "true" if resolved["fullscreen"] else "false",
            resolved["vertical_alignment"],
        )
    )
