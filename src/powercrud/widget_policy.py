"""Neutral helpers for applying selected-pack widget presentation."""

from copy import deepcopy
from typing import Mapping

from django import forms
from django.db import models

from powercrud.template_packs import WidgetKind, WidgetPresentation


def get_model_widget_kind(field: models.Field) -> WidgetKind:
    """Return PowerCRUD's semantic category for one model field."""
    if isinstance(field, models.ManyToManyField):
        return "multiselect"
    if isinstance(field, (models.ForeignKey, models.OneToOneField)):
        return "select"
    if isinstance(field, models.BooleanField):
        return "boolean"
    if getattr(field, "choices", None):
        return "select"
    if isinstance(field, models.DateTimeField):
        return "datetime"
    if isinstance(field, models.DateField):
        return "date"
    if isinstance(field, models.TimeField):
        return "time"
    if isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)):
        return "number"
    if isinstance(field, models.TextField):
        return "textarea"
    if isinstance(field, models.FileField):
        return "file"
    return "text"


def get_form_widget_kind(field: forms.Field) -> WidgetKind:
    """Return a semantic category from a bound Django form field."""
    widget = field.widget
    if isinstance(widget, forms.SelectMultiple):
        return "multiselect"
    if isinstance(widget, forms.Select):
        return "boolean" if isinstance(field, forms.BooleanField) else "select"
    if isinstance(widget, forms.DateTimeInput):
        return "datetime"
    if isinstance(widget, forms.DateInput):
        return "date"
    if isinstance(widget, forms.TimeInput):
        return "time"
    if isinstance(widget, forms.NumberInput) or isinstance(
        field, (forms.IntegerField, forms.DecimalField, forms.FloatField)
    ):
        return "number"
    if isinstance(widget, forms.Textarea):
        return "textarea"
    if isinstance(widget, forms.FileInput):
        return "file"
    if isinstance(widget, forms.CheckboxInput):
        return "boolean"
    return "text"


def merge_widget_attrs(
    existing_attrs: Mapping[str, str], presentation_attrs: Mapping[str, str]
) -> dict[str, str]:
    """Merge pack presentation attrs while retaining semantic Django attributes."""
    merged_attrs = dict(existing_attrs)
    for attr_name, attr_value in presentation_attrs.items():
        if attr_name == "class" and merged_attrs.get("class"):
            class_names: list[str] = []
            for class_name in (
                f"{merged_attrs['class']} {attr_value}".strip().split()
            ):
                if class_name not in class_names:
                    class_names.append(class_name)
            merged_attrs["class"] = " ".join(class_names)
            continue
        if attr_name == "style" and merged_attrs.get("style"):
            existing_style = merged_attrs["style"].strip().rstrip(";")
            presentation_style = attr_value.strip().rstrip(";")
            merged_attrs["style"] = f"{existing_style}; {presentation_style}"
            continue
        merged_attrs.setdefault(attr_name, attr_value)
    return merged_attrs


def apply_widget_presentation(
    field: forms.Field, presentation: WidgetPresentation
) -> None:
    """Apply a compatible widget override, attributes, and semantic marker."""
    current_widget = field.widget
    attrs = merge_widget_attrs(current_widget.attrs, presentation.attrs)
    widget_class = presentation.widget_class
    if widget_class is not None and not isinstance(current_widget, widget_class):
        replacement = widget_class(attrs=attrs)
        if hasattr(current_widget, "choices"):
            replacement.choices = current_widget.choices
        field.widget = replacement
    else:
        try:
            widget = deepcopy(current_widget)
        except Exception:
            widget = current_widget
        widget.attrs = attrs
        field.widget = widget

    field.widget.attrs.pop("data-powercrud-searchable-select", None)
    field.widget.attrs.pop("data-powercrud-searchable-multiselect", None)
    if presentation.enhancement == "searchable-select":
        field.widget.attrs["data-powercrud-searchable-select"] = "true"
    elif presentation.enhancement == "searchable-multiselect":
        field.widget.attrs["data-powercrud-searchable-multiselect"] = "true"
