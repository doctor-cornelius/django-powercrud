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


class Bootstrap5ServerAdapter(BaseServerAdapter):
    """Translate PowerCRUD's semantic presentation requests into Bootstrap classes."""

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
        """Return Bootstrap's current generated-filter presentation without changing UI."""
        if context.surface in {"form", "inline"}:
            temporal_presentation = {
                "date": WidgetPresentation(
                    widget_class=forms.DateInput,
                    attrs={"type": "date", "class": "form-control"},
                ),
                "datetime": WidgetPresentation(
                    widget_class=forms.DateInput,
                    attrs={"type": "date", "class": "form-control"},
                ),
                "time": WidgetPresentation(
                    widget_class=forms.TimeInput,
                    attrs={"type": "time", "class": "form-control"},
                ),
            }
            if context.kind in temporal_presentation:
                return temporal_presentation[context.kind]
            if (
                context.surface == "inline"
                and context.kind == "multiselect"
                and context.searchable_requested
            ):
                return WidgetPresentation(enhancement="searchable-multiselect")
            return WidgetPresentation()
        if context.surface != "filter":
            return WidgetPresentation()

        attributes_by_kind = {
            "text": {"class": "form-control form-control-sm"},
            "textarea": {"class": "form-control form-control-sm"},
            "select": {"class": "form-select form-select-sm"},
            "multiselect": {"class": "form-select form-select-sm", "size": "5"},
            "date": {"class": "form-control form-control-sm", "type": "date"},
            "datetime": {"class": "form-control form-control-sm", "type": "date"},
            "number": {"class": "form-control form-control-sm", "step": "any"},
            "time": {"class": "form-control form-control-sm", "type": "time"},
            "boolean": {"class": "form-select form-select-sm"},
            "file": {"class": "form-control form-control-sm"},
        }
        enhancement = None
        if context.searchable_requested:
            enhancement = (
                "searchable-multiselect"
                if context.kind == "multiselect"
                else "searchable-select"
            )
        return WidgetPresentation(
            attrs=attributes_by_kind.get(context.kind, {}), enhancement=enhancement
        )

    def get_view_help_variables(self, color: str):
        """Return Bootstrap view-help CSS variables."""
        return {"style": get_bootstrap5_view_help_style(color)}


server_adapter = Bootstrap5ServerAdapter()
