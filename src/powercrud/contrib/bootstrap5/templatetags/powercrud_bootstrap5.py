"""Bootstrap-specific field rendering helpers for the optional template pack."""

from django import template
from django.forms.boundfield import BoundField
from django.forms.widgets import CheckboxInput, FileInput, Select, SelectMultiple


register = template.Library()


@register.filter
def bootstrap5_text_alignment(value: object) -> str:
    """Translate PowerCRUD's semantic alignment names to Bootstrap utilities."""
    return {"left": "start", "center": "center", "right": "end"}.get(
        str(value or "").strip().lower(),
        "start",
    )


@register.simple_tag
def bootstrap5_field(
    field: BoundField,
    small: bool = False,
    error_suffix: str = "_errors",
    include_help: bool = True,
) -> str:
    """Render one bound field with Bootstrap classes and accessible descriptions."""
    widget = field.field.widget
    existing_classes = str(widget.attrs.get("class", "")).strip()
    if isinstance(widget, CheckboxInput):
        bootstrap_class = "form-check-input pc-inline-checkbox" if small else "form-check-input"
    elif isinstance(widget, (Select, SelectMultiple)):
        bootstrap_class = "form-select form-select-sm" if small else "form-select"
    elif isinstance(widget, FileInput):
        bootstrap_class = "form-control form-control-sm" if small else "form-control"
    else:
        bootstrap_class = "form-control form-control-sm" if small else "form-control"

    if field.errors:
        bootstrap_class = f"{bootstrap_class} is-invalid"

    classes = " ".join(part for part in (existing_classes, bootstrap_class) if part)
    described_by = []
    if include_help and field.help_text:
        described_by.append(f"{field.auto_id}_help")
    if field.errors:
        described_by.append(f"{field.auto_id}{error_suffix}")
    attrs = {"class": classes}
    if described_by:
        attrs["aria-describedby"] = " ".join(described_by)
    if field.errors:
        attrs["aria-invalid"] = "true"
    return field.as_widget(attrs=attrs)
