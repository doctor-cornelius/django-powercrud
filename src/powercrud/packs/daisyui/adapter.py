"""Public server adapter for the built-in DaisyUI template pack."""

from django import forms

from powercrud.packs.daisyui.styles import (
    get_daisyui_framework_styles,
    get_daisyui_view_help_style,
)
from powercrud.template_packs import (
    ActionPresentation,
    BaseServerAdapter,
    ServerAdapterContext,
    ServerPresentation,
    WidgetPolicyContext,
    WidgetPresentation,
)


class DaisyUIServerAdapter(BaseServerAdapter):
    """Translate PowerCRUD's semantic presentation requests into DaisyUI classes."""

    def get_presentation(self, context: ServerAdapterContext) -> ServerPresentation:
        """Return DaisyUI action presentation for one view."""
        legacy_styles = get_daisyui_framework_styles(_AdapterView(context))["daisyUI"]
        return ServerPresentation(
            actions=ActionPresentation(
                base_classes=legacy_styles["base"].strip(),
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
        """Return DaisyUI's current generated-filter presentation without changing UI."""
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
            "text": {
                "class": "input input-bordered input-sm w-full text-xs h-10 min-h-10"
            },
            "textarea": {
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
            "datetime": {
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
            "boolean": {
                "class": "select select-bordered select-sm w-full text-xs h-10 min-h-10"
            },
            "file": {
                "class": "input input-bordered input-sm w-full text-xs h-10 min-h-10"
            },
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
        """Return DaisyUI view-help CSS variables."""
        return {"style": get_daisyui_view_help_style(color)}


class _AdapterView:
    """Supply the small legacy style-provider surface during the migration."""

    def __init__(self, context: ServerAdapterContext):
        """Keep modal identifiers available to the legacy style helper."""
        self.context = context

    def get_modal_id(self) -> str:
        """Return the configured modal identifier in its legacy form."""
        return self.context.modal_id


server_adapter = DaisyUIServerAdapter()
