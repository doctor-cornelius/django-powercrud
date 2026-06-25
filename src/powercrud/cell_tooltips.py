from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ImproperlyConfigured


TOOLTIP_MODES = {"eager", "lazy"}


@dataclass(frozen=True)
class ListCellTooltipSpec:
    """Normalized list-cell tooltip declaration for one field/property."""

    field_name: str
    hook: str | None
    mode: str = "eager"


def normalize_list_cell_tooltip_specs(
    configured_tooltips: Any,
) -> dict[str, ListCellTooltipSpec]:
    """Return normalized tooltip specs from legacy, eager, or rich config."""
    if configured_tooltips is None:
        return {}

    specs: dict[str, ListCellTooltipSpec] = {}
    if isinstance(configured_tooltips, list):
        for field_name in configured_tooltips:
            if field_name not in specs:
                specs[field_name] = ListCellTooltipSpec(
                    field_name=field_name,
                    hook=None,
                    mode="eager",
                )
        return specs

    if not isinstance(configured_tooltips, dict):
        return {}

    for field_name, config in configured_tooltips.items():
        if isinstance(config, str):
            specs[field_name] = ListCellTooltipSpec(
                field_name=field_name,
                hook=config,
                mode="eager",
            )
            continue

        if isinstance(config, dict):
            hook = config.get("hook")
            mode = config.get("mode") or "eager"
            specs[field_name] = ListCellTooltipSpec(
                field_name=field_name,
                hook=hook,
                mode=mode,
            )

    return specs


def has_lazy_list_cell_tooltip(configured_tooltips: Any) -> bool:
    """Return True when any list-cell tooltip declares lazy resolution."""
    return any(
        spec.mode == "lazy"
        for spec in normalize_list_cell_tooltip_specs(configured_tooltips).values()
    )


def resolve_list_cell_tooltip(
    *,
    view: Any,
    obj: Any,
    field_name: str,
    is_property: bool,
    request: Any,
    hook_name: str | None = None,
) -> str | None:
    """Resolve a plain-text semantic tooltip for one rendered list cell."""
    if hook_name is not None:
        resolver = getattr(view, hook_name, None)
        if not callable(resolver):
            raise ImproperlyConfigured(
                "list_cell_tooltip_fields configured "
                f"{field_name!r} with missing or non-callable hook "
                f"{hook_name!r}."
            )
        tooltip_text = resolver(obj, request=request)
        if tooltip_text is None:
            return None
        tooltip_text = str(tooltip_text).strip()
        return tooltip_text or None

    resolver = getattr(view, "get_list_cell_tooltip", None)
    if not callable(resolver):
        return None
    try:
        tooltip_text = resolver(
            obj,
            field_name,
            is_property=is_property,
            request=request,
        )
    except Exception:
        return None
    if tooltip_text is None:
        return None
    tooltip_text = str(tooltip_text).strip()
    return tooltip_text or None
