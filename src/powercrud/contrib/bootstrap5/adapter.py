"""Public server adapter for the optional Bootstrap 5 template pack."""

from powercrud.contrib.bootstrap5.styles import (
    get_bootstrap5_framework_styles,
    get_bootstrap5_view_help_style,
)
from powercrud.template_packs import (
    ActionPresentation,
    BaseServerAdapter,
    ServerAdapterContext,
    ServerPresentation,
)


class Bootstrap5ServerAdapter(BaseServerAdapter):
    """Translate PowerCRUD's semantic presentation requests into Bootstrap classes."""

    def get_presentation(self, context: ServerAdapterContext) -> ServerPresentation:
        """Return Bootstrap action and filter presentation for one view."""
        del context
        legacy_styles = get_bootstrap5_framework_styles(None)["bootstrap5"]
        return ServerPresentation(
            filter_widget_attrs=legacy_styles["filter_attrs"],
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

    def get_view_help_variables(self, color: str):
        """Return Bootstrap view-help CSS variables."""
        return {"style": get_bootstrap5_view_help_style(color)}


server_adapter = Bootstrap5ServerAdapter()
