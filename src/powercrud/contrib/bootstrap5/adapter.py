"""Public server adapter for the optional Bootstrap 5 template pack."""

from django import forms

from powercrud.contrib.bootstrap5.styles import (
    get_bootstrap5_framework_styles,
    get_bootstrap5_view_help_style,
)
from powercrud.template_packs import (
    ActionPresentation,
    BaseServerAdapter,
    ServerAdapterContext,
    ServerPresentation,
    WidgetPolicyContext,
    WidgetPresentation,
)


class Bootstrap5DateInput(forms.DateInput):
    """Render date values in the browser's native date control."""

    input_type = "date"

    def __init__(self, attrs=None):
        """Use the HTML-compatible date value format."""
        super().__init__(attrs=attrs, format="%Y-%m-%d")


class Bootstrap5DateTimeLocalInput(forms.DateTimeInput):
    """Render datetime values in the browser's native local datetime control."""

    input_type = "datetime-local"

    def __init__(self, attrs=None):
        """Keep seconds in rendered values so datetime editing round-trips exactly."""
        super().__init__(attrs=attrs, format="%Y-%m-%dT%H:%M:%S")


class Bootstrap5TimeInput(forms.TimeInput):
    """Render time values in the browser's native time control."""

    input_type = "time"

    def __init__(self, attrs=None):
        """Keep seconds in the HTML-compatible time value."""
        super().__init__(attrs=attrs, format="%H:%M:%S")


class Bootstrap5ServerAdapter(BaseServerAdapter):
    """Translate PowerCRUD's semantic presentation requests into Bootstrap classes."""

    widget_defaults = {
        "text": WidgetPresentation(),
        "textarea": WidgetPresentation(),
        "number": WidgetPresentation(),
        "date": WidgetPresentation(
            widget_class=Bootstrap5DateInput,
            attrs={"class": "form-control"},
        ),
        "datetime": WidgetPresentation(
            widget_class=Bootstrap5DateTimeLocalInput,
            attrs={"step": "1", "class": "form-control"},
        ),
        "time": WidgetPresentation(
            widget_class=Bootstrap5TimeInput,
            attrs={"step": "1", "class": "form-control"},
        ),
        "boolean": WidgetPresentation(),
        "select": WidgetPresentation(enhancement="searchable-select"),
        "multiselect": WidgetPresentation(
            enhancement="searchable-multiselect",
            variant="standard",
        ),
        "file": WidgetPresentation(),
    }
    widget_surface_overrides = {
        ("inline", "multiselect"): WidgetPresentation(variant="compact"),
        ("filter", "text"): WidgetPresentation(attrs={"class": "form-control form-control-sm"}),
        ("filter", "textarea"): WidgetPresentation(attrs={"class": "form-control form-control-sm"}),
        ("filter", "select"): WidgetPresentation(attrs={"class": "form-select form-select-sm"}),
        ("filter", "multiselect"): WidgetPresentation(attrs={"class": "form-select form-select-sm", "size": "5"}),
        ("filter", "date"): WidgetPresentation(attrs={"class": "form-control form-control-sm"}),
        ("filter", "datetime"): WidgetPresentation(attrs={"class": "form-control form-control-sm", "step": "1"}),
        ("filter", "number"): WidgetPresentation(attrs={"class": "form-control form-control-sm", "step": "any"}),
        ("filter", "time"): WidgetPresentation(attrs={"class": "form-control form-control-sm"}),
        ("filter", "boolean"): WidgetPresentation(attrs={"class": "form-select form-select-sm"}),
        ("filter", "file"): WidgetPresentation(attrs={"class": "form-control form-control-sm"}),
        ("bulk", "text"): WidgetPresentation(attrs={"class": "form-control"}),
        ("bulk", "textarea"): WidgetPresentation(attrs={"class": "form-control"}),
        ("bulk", "number"): WidgetPresentation(attrs={"class": "form-control"}),
        ("bulk", "date"): WidgetPresentation(attrs={"class": "form-control"}),
        ("bulk", "datetime"): WidgetPresentation(attrs={"class": "form-control"}),
        ("bulk", "time"): WidgetPresentation(attrs={"class": "form-control"}),
        ("bulk", "boolean"): WidgetPresentation(attrs={"class": "form-select"}),
        ("bulk", "select"): WidgetPresentation(attrs={"class": "form-select"}),
        ("bulk", "multiselect"): WidgetPresentation(attrs={"class": "form-select"}),
        ("bulk", "file"): WidgetPresentation(attrs={"class": "form-control"}),
    }

    def get_presentation(self, context: ServerAdapterContext) -> ServerPresentation:
        """Return Bootstrap action presentation for one view."""
        del context
        legacy_styles = get_bootstrap5_framework_styles(None)["bootstrap5"]
        return ServerPresentation(
            actions=ActionPresentation(
                base_classes=legacy_styles["base"],
                role_classes={
                    "view": legacy_styles["actions"]["View"],
                    "edit": legacy_styles["actions"]["Edit"],
                    "delete": legacy_styles["actions"]["Delete"],
                    "extra": legacy_styles["extra_default"],
                },
                group_item_classes=legacy_styles["action_group_item"],
                extra_default_classes=legacy_styles["extra_default"],
                list_cell_link_classes=legacy_styles["list_cell_link_class"],
            ),
        )

    def get_widget_presentation(
        self, context: WidgetPolicyContext) -> WidgetPresentation:
        """Return Bootstrap presentation for one generated widget."""
        return super().get_widget_presentation(context)

    def get_view_help_variables(self, color: str):
        """Return Bootstrap view-help CSS variables."""
        return {"style": get_bootstrap5_view_help_style(color)}


server_adapter = Bootstrap5ServerAdapter()
