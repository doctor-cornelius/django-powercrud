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


class DaisyUIDateTimeLocalInput(forms.DateTimeInput):
    """Render datetime values in the browser's native local datetime control."""

    input_type = "datetime-local"

    def __init__(self, attrs=None):
        """Keep seconds in rendered values so datetime editing round-trips exactly."""
        super().__init__(attrs=attrs, format="%Y-%m-%dT%H:%M:%S")


class DaisyUIServerAdapter(BaseServerAdapter):
    """Translate PowerCRUD's semantic presentation requests into DaisyUI classes."""

    widget_defaults = {
        "text": WidgetPresentation(),
        "textarea": WidgetPresentation(),
        "number": WidgetPresentation(),
        "date": WidgetPresentation(
            widget_class=forms.DateInput,
            attrs={"type": "date", "class": "form-control"},
        ),
        "datetime": WidgetPresentation(
            widget_class=DaisyUIDateTimeLocalInput,
            attrs={"step": "1", "class": "form-control"},
        ),
        "time": WidgetPresentation(
            widget_class=forms.TimeInput,
            attrs={"type": "time", "class": "form-control"},
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
        ("filter", "text"): WidgetPresentation(
            attrs={"class": "input input-bordered input-sm w-full text-xs h-10 min-h-10"}
        ),
        ("filter", "textarea"): WidgetPresentation(
            attrs={"class": "input input-bordered input-sm w-full text-xs h-10 min-h-10"}
        ),
        ("filter", "select"): WidgetPresentation(
            attrs={"class": "select select-bordered select-sm w-full text-xs h-10 min-h-10"}
        ),
        ("filter", "multiselect"): WidgetPresentation(
            attrs={
                "class": "select select-bordered select-sm w-full text-xs",
                "size": "5",
                "style": "min-height: 8rem; max-height: 8rem; overflow-y: auto;",
            }
        ),
        ("filter", "date"): WidgetPresentation(
            attrs={"class": "input input-bordered input-sm w-full text-xs h-10 min-h-10", "type": "date"}
        ),
        ("filter", "datetime"): WidgetPresentation(
            attrs={"class": "input input-bordered input-sm w-full text-xs h-10 min-h-10", "step": "1"}
        ),
        ("filter", "number"): WidgetPresentation(
            attrs={"class": "input input-bordered input-sm w-full text-xs h-10 min-h-10", "step": "any"}
        ),
        ("filter", "time"): WidgetPresentation(
            attrs={"class": "input input-bordered input-sm w-full text-xs h-10 min-h-10", "type": "time"}
        ),
        ("filter", "boolean"): WidgetPresentation(
            attrs={"class": "select select-bordered select-sm w-full text-xs h-10 min-h-10"}
        ),
        ("filter", "file"): WidgetPresentation(
            attrs={"class": "input input-bordered input-sm w-full text-xs h-10 min-h-10"}
        ),
        ("bulk", "text"): WidgetPresentation(
            attrs={"class": "input input-bordered w-full"}
        ),
        ("bulk", "textarea"): WidgetPresentation(
            attrs={"class": "textarea textarea-bordered w-full"}
        ),
        ("bulk", "number"): WidgetPresentation(
            attrs={"class": "input input-bordered w-full"}
        ),
        ("bulk", "date"): WidgetPresentation(
            attrs={"class": "input input-bordered w-full", "type": "date"}
        ),
        ("bulk", "datetime"): WidgetPresentation(
            attrs={"class": "input input-bordered w-full"}
        ),
        ("bulk", "time"): WidgetPresentation(
            attrs={"class": "input input-bordered w-full", "type": "time"}
        ),
        ("bulk", "boolean"): WidgetPresentation(
            attrs={"class": "select select-bordered w-full"}
        ),
        ("bulk", "select"): WidgetPresentation(
            attrs={"class": "select select-bordered w-full"}
        ),
        ("bulk", "multiselect"): WidgetPresentation(
            attrs={"class": "select select-bordered w-full min-h-[150px] h-auto"}
        ),
        ("bulk", "file"): WidgetPresentation(
            attrs={"class": "file-input file-input-bordered w-full"}
        ),
    }

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
        """Return DaisyUI presentation for one generated widget."""
        return super().get_widget_presentation(context)

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
