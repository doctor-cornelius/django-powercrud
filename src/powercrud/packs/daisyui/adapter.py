"""Public server adapter for the built-in DaisyUI template pack."""

from powercrud.packs.daisyui.styles import (
    get_daisyui_framework_styles,
    get_daisyui_view_help_style,
)
from powercrud.template_packs import (
    ActionPresentation,
    BaseServerAdapter,
    ServerAdapterContext,
    ServerPresentation,
)


class DaisyUIServerAdapter(BaseServerAdapter):
    """Translate PowerCRUD's semantic presentation requests into DaisyUI classes."""

    def get_presentation(self, context: ServerAdapterContext) -> ServerPresentation:
        """Return DaisyUI action and filter presentation for one view."""
        legacy_styles = get_daisyui_framework_styles(_AdapterView(context))["daisyUI"]
        return ServerPresentation(
            filter_widget_attrs=legacy_styles["filter_attrs"],
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
