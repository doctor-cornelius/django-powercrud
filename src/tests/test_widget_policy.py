"""Focused semantic tests for PowerCRUD widget presentation policy."""

import re
from datetime import date, time

from django import forms
import pytest

from powercrud.contrib.bootstrap5.adapter import (
    Bootstrap5DateInput,
    Bootstrap5ServerAdapter,
    Bootstrap5TimeInput,
)
from powercrud.packs.daisyui.adapter import (
    DaisyUIDateInput,
    DaisyUIServerAdapter,
    DaisyUITimeInput,
)
from powercrud.template_packs import WidgetPolicyContext, WidgetPresentation
from powercrud.widget_policy import apply_widget_presentation


TEMPORAL_CASES = (
    ("date", forms.DateField, forms.DateInput, date(2026, 8, 9), "2026-08-09"),
    ("time", forms.TimeField, forms.TimeInput, time(14, 5, 6), "14:05:06"),
)
ADAPTER_CASES = (
    (DaisyUIServerAdapter(), DaisyUIDateInput, DaisyUITimeInput),
    (Bootstrap5ServerAdapter(), Bootstrap5DateInput, Bootstrap5TimeInput),
)


def _input_type_values(rendered: str) -> list[str]:
    """Return every rendered input type without depending on attribute ordering."""
    return re.findall(r'\btype="([^"]+)"', rendered)


def _policy_context(*, surface: str, kind: str) -> WidgetPolicyContext:
    """Build the neutral policy facts needed by one temporal widget test."""
    return WidgetPolicyContext(
        surface=surface,
        kind=kind,
        render_mode="native",
        field_name=kind,
        required=False,
        disabled=surface == "bulk",
        is_relation=False,
        has_dependency=False,
        enhancement_intent="default",
    )


@pytest.mark.parametrize(
    ("kind", "field_class", "widget_class", "value", "expected_value"),
    TEMPORAL_CASES,
)
def test_input_type_presentation_is_idempotent(
    kind, field_class, widget_class, value, expected_value
):
    """Legacy type attrs must become one semantic input type after repeat application."""
    field = field_class(widget=widget_class())
    presentation = WidgetPresentation(
        widget_class=widget_class,
        attrs={"type": kind},
    )

    apply_widget_presentation(field, presentation)
    apply_widget_presentation(field, presentation)
    rendered = field.widget.render(kind, value)

    assert field.widget.input_type == kind, (
        f"Repeated {kind} presentation must update the widget's semantic input type."
    )
    assert "type" not in field.widget.attrs, (
        f"Repeated {kind} presentation must not leave a duplicate type attribute in widget attrs."
    )
    assert _input_type_values(rendered) == [kind], (
        f"Rendered {kind} controls must contain exactly one matching type attribute."
    )
    assert f'value="{expected_value}"' in rendered, (
        f"Rendered {kind} controls must retain their HTML-compatible value format."
    )


@pytest.mark.parametrize(("adapter", "date_class", "time_class"), ADAPTER_CASES)
@pytest.mark.parametrize("surface", ("form", "inline", "filter", "bulk"))
@pytest.mark.parametrize(
    ("kind", "value", "expected_value"),
    (
        ("date", date(2026, 8, 9), "2026-08-09"),
        ("time", time(14, 5, 6), "14:05:06"),
    ),
)
def test_first_party_temporal_widgets_use_native_input_types(
    adapter, date_class, time_class, surface, kind, value, expected_value
):
    """Both first-party packs must own native, HTML-compatible temporal widgets."""
    expected_class = date_class if kind == "date" else time_class
    presentation = adapter.get_widget_presentation(
        _policy_context(surface=surface, kind=kind)
    )
    widget = presentation.widget_class(attrs=dict(presentation.attrs))
    rendered = widget.render(kind, value)

    assert presentation.widget_class is expected_class, (
        f"The {adapter.__class__.__name__} must use its dedicated {kind} widget on {surface}."
    )
    assert "type" not in presentation.attrs, (
        f"The {adapter.__class__.__name__} must not express {kind} semantics through attrs."
    )
    assert widget.input_type == kind, (
        f"The {adapter.__class__.__name__} {kind} widget must expose the native input type."
    )
    assert _input_type_values(rendered) == [kind], (
        f"The {adapter.__class__.__name__} {surface} {kind} widget must render one type attribute."
    )
    assert f'value="{expected_value}"' in rendered, (
        f"The {adapter.__class__.__name__} {kind} widget must render an HTML-compatible value."
    )
    if kind == "time":
        assert presentation.attrs.get("step") == "1", (
            f"The {adapter.__class__.__name__} time widget must permit its rendered seconds."
        )
