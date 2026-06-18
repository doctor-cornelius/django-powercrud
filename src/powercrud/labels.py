"""Helpers for resolving PowerCRUD field and property display labels."""

from __future__ import annotations

from typing import Any

from django.db import models
from django.utils.text import capfirst


def fallback_label_from_name(name: str) -> str:
    """Return a human label derived from a raw field or property name."""
    return name.replace("_", " ").title()


def get_configured_field_label(view: Any, name: str) -> str | None:
    """Return an explicit configured field label when one is available."""
    if view is None:
        return None
    config_getter = getattr(view, "config", None)
    if callable(config_getter):
        field_labels = getattr(config_getter(), "field_labels", {}) or {}
    else:
        field_labels = getattr(view, "field_labels", {}) or {}
    label = field_labels.get(name)
    if label is None:
        return None
    return str(label)


def resolve_field_label(view: Any, field_name: str, field: Any | None = None) -> str:
    """Return the display label for a model field or queryset annotation."""
    configured_label = get_configured_field_label(view, field_name)
    if configured_label is not None:
        return configured_label

    if field is not None and hasattr(field, "remote_field"):
        remote_field = getattr(field, "remote_field", None)
        if remote_field and isinstance(remote_field, models.ManyToManyRel):
            return capfirst(str(remote_field.model._meta.verbose_name_plural))

    verbose_name = getattr(field, "verbose_name", None)
    if verbose_name:
        return capfirst(str(verbose_name))

    return fallback_label_from_name(field_name)


def resolve_property_label(view: Any, property_name: str, property_object: Any = None) -> str:
    """Return the display label for a model property."""
    configured_label = get_configured_field_label(view, property_name)
    if configured_label is not None:
        return configured_label

    if (
        property_object
        and hasattr(property_object.fget, "short_description")
        and property_object.fget.short_description
    ):
        return str(property_object.fget.short_description)

    return fallback_label_from_name(property_name)
