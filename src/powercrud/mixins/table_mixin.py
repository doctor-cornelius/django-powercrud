import re
from typing import Any

from django.utils.text import capfirst

from .config_mixin import resolve_config


class TableMixin:
    """
    Provides methods for table styling and layout.
    """

    VIEW_HELP_SEMANTIC_COLORS = {
        "base",
        "primary",
        "secondary",
        "accent",
        "neutral",
        "info",
        "success",
        "warning",
        "error",
    }
    VIEW_HELP_HEX_COLOR_RE = re.compile(r"^#[0-9a-f]{3}([0-9a-f]{3})?$")

    @staticmethod
    def _normalize_hex_color(value: str) -> str:
        """
        Expand short hex colors to six-digit lowercase form.
        """
        normalized = value.strip().lower()
        if len(normalized) == 4:
            return "#" + "".join(character * 2 for character in normalized[1:])
        return normalized

    @classmethod
    def _view_help_style_vars(cls, color: str) -> str:
        """
        Return CSS variables for the collapsed screen-help color theme.
        """
        normalized = color.strip().lower()
        if normalized == "base":
            return (
                "--pc-view-help-border: var(--color-base-300); "
                "--pc-view-help-summary-bg: var(--color-base-100); "
                "--pc-view-help-summary-fg: var(--color-base-content); "
                "--pc-view-help-content-bg: var(--color-base-100); "
                "--pc-view-help-content-fg: var(--color-base-content);"
            )
        if normalized in cls.VIEW_HELP_SEMANTIC_COLORS:
            return (
                f"--pc-view-help-border: color-mix(in srgb, var(--color-{normalized}) 35%, var(--color-base-300)); "
                f"--pc-view-help-summary-bg: color-mix(in srgb, var(--color-{normalized}) 18%, var(--color-base-100)); "
                "--pc-view-help-summary-fg: var(--color-base-content); "
                f"--pc-view-help-content-bg: color-mix(in srgb, var(--color-{normalized}) 8%, var(--color-base-100)); "
                "--pc-view-help-content-fg: var(--color-base-content);"
            )
        if not cls.VIEW_HELP_HEX_COLOR_RE.match(normalized):
            return cls._view_help_style_vars("base")

        hex_color = cls._normalize_hex_color(normalized)
        return (
            f"--pc-view-help-border: color-mix(in srgb, {hex_color} 35%, var(--color-base-300)); "
            f"--pc-view-help-summary-bg: color-mix(in srgb, {hex_color} 18%, var(--color-base-100)); "
            "--pc-view-help-summary-fg: var(--color-base-content); "
            f"--pc-view-help-content-bg: color-mix(in srgb, {hex_color} 8%, var(--color-base-100)); "
            "--pc-view-help-content-fg: var(--color-base-content);"
        )

    def get_table_pixel_height_other_page_elements(self) -> str:
        """Returns the height of other elements on the page that the table is
        displayed on. After subtracting this (in pixels) from the page height,
        the table height will be calculated (in a css style in list.html) as
        {{ get_table_max_height }}% of the remaining viewport height.
        """
        return resolve_config(self).table_pixel_height_px  # px

    def get_table_max_height(self) -> int:
        """Returns the proportion of visible space on the viewport after subtracting
        the height of other elements on the page that the table is displayed on,
        as represented by get_table_pixel_height_other_page_elements().

        The table height is calculated in a css style for max-table-height in list.html.
        """
        return resolve_config(self).table_max_height

    def get_table_max_col_width(self):
        # The max width for the table columns in object_list.html - in characters
        return resolve_config(self).table_max_col_width_css

    def get_table_header_min_wrap_width(self):
        # The max width for the table columns in object_list.html - in characters
        return resolve_config(self).table_header_min_wrap_width_css

    def get_table_classes(self):
        """
        Get the table classes.
        """
        return resolve_config(self).table_classes

    def get_action_button_classes(self):
        """
        Get the action button classes.
        """
        return resolve_config(self).action_button_classes

    def get_extra_button_classes(self):
        """
        Get the extra button classes.
        """
        return resolve_config(self).extra_button_classes

    def get_extra_buttons_mode(self):
        """
        Get the rendering mode for list-level extra buttons.
        """
        return resolve_config(self).extra_buttons_mode

    def get_extra_actions_mode(self):
        """
        Get the rendering mode for row-level extra actions.
        """
        return resolve_config(self).extra_actions_mode

    def get_extra_actions_dropdown_open_upward_bottom_rows(self) -> int:
        """
        Return how many rendered rows from the bottom should open the extra
        actions dropdown upward when dropdown mode is active.
        """
        return int(resolve_config(self).extra_actions_dropdown_open_upward_bottom_rows)

    def get_selected_ids_for_extra_button(self, request, button_spec) -> list[str]:
        """
        Return the persisted selection used by a selection-aware extra button.
        """
        if not request:
            return []
        resolver = getattr(self, "get_selected_ids_from_session", None)
        if not callable(resolver):
            return []
        selected_ids = resolver(request)
        return [str(selected_id) for selected_id in selected_ids]

    def can_delete_object(self, obj, request) -> bool:
        """
        Return whether the built-in Delete action should be enabled for a row.

        Downstream views can override this to disable the standard Delete action
        for specific objects before the modal opens.
        """
        return True

    def can_update_object(self, obj, request) -> bool:
        """
        Return whether the built-in Edit action should be enabled for a row.

        Downstream views can override this to disable update affordances for
        specific objects before the edit modal or page is opened.
        """
        return True

    def get_update_disabled_reason(self, obj, request) -> str | None:
        """
        Return the tooltip shown when update affordances are disabled.

        Downstream views can override this to explain why
        ``can_update_object()`` returned ``False`` for a row.
        """
        return None

    def get_delete_disabled_reason(self, obj, request) -> str | None:
        """
        Return the tooltip shown when the built-in Delete action is disabled.

        Downstream views can override this to explain why
        ``can_delete_object()`` returned ``False`` for a row.
        """
        return None

    def get_view_title(self) -> str:
        """
        Return the visible heading for the list page.

        When `view_title` is configured, it overrides the default heading text.
        Otherwise PowerCRUD falls back to the model plural verbose name.
        """
        configured_title = resolve_config(self).view_title
        if configured_title:
            return configured_title

        model = getattr(self, "model", None)
        if model is None or not hasattr(model, "_meta"):
            return ""

        return capfirst(model._meta.verbose_name_plural)

    def get_view_instructions(self) -> str:
        """
        Return the optional plain-text helper copy shown under the list heading.
        """
        configured_instructions = resolve_config(self).view_instructions
        if configured_instructions:
            return configured_instructions
        return ""

    def get_view_help(self) -> dict[str, Any]:
        """
        Return optional collapsed screen-help configuration.
        """
        config = resolve_config(self)
        configured_help = config.view_help
        if not isinstance(configured_help, dict):
            return {}
        summary = configured_help.get("summary")
        details = configured_help.get("details")
        if not isinstance(summary, str) or not isinstance(details, str):
            return {}
        if not summary.strip() or not details.strip():
            return {}
        color = configured_help.get("color") or config.view_help_default_color or "base"
        min_width = configured_help.get("min_width") or config.view_help_min_width or "40rem"
        return {
            "summary": summary.strip(),
            "details": details.strip(),
            "default_open": configured_help.get("default_open") is True,
            "color": color,
            "min_width": min_width,
            "style": self._view_help_style_vars(str(color)),
        }

    def get_view_help_detail_paragraphs(self) -> list[str]:
        """
        Return screen-help detail text split into paragraph blocks.
        """
        help_config = self.get_view_help()
        details = help_config.get("details", "")
        if not isinstance(details, str) or not details.strip():
            return []
        return [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", details.strip())
            if paragraph.strip()
        ]

    def get_column_help_text(self) -> dict[str, str]:
        """
        Return the optional plain-text help text mapping for rendered list columns.
        """
        configured_help = resolve_config(self).column_help_text
        if isinstance(configured_help, dict):
            return configured_help
        return {}

    def get_column_alignments(self) -> dict[str, str]:
        """
        Return optional per-column list body-cell alignment overrides.
        """
        configured_alignments = resolve_config(self).column_alignments
        if isinstance(configured_alignments, dict):
            return dict(configured_alignments)
        return {}

    def get_list_cell_tooltip_fields(self) -> list[str] | dict[str, Any]:
        """
        Return rendered list fields/properties configured for semantic tooltips.
        """
        configured_fields = resolve_config(self).list_cell_tooltip_fields
        if isinstance(configured_fields, dict):
            return dict(configured_fields)
        if isinstance(configured_fields, list):
            return list(configured_fields)
        return {}

    def get_link_fields(self) -> dict[str, dict[str, Any]]:
        """
        Return narrow declarative list-cell link configuration.
        """
        configured_links = resolve_config(self).link_fields
        if isinstance(configured_links, dict):
            return dict(configured_links)
        return {}

    def get_list_cell_link_default_open_in(self) -> str:
        """
        Return the default opening mode for list-cell links.
        """
        return str(resolve_config(self).list_cell_link_default_open_in)

    def get_list_cell_tooltip(
        self,
        obj,
        field_name: str,
        *,
        is_property: bool,
        request=None,
    ) -> str | None:
        """
        Return the optional semantic tooltip for one rendered list cell.

        Downstream views can override this to provide plain-text tooltip
        explanations for specific rendered list cells.
        """
        return None

    def get_list_cell_link(
        self,
        obj,
        field_name: str,
        value,
        *,
        is_property: bool,
        request=None,
    ) -> dict[str, Any] | bool | None:
        """
        Return optional link metadata for one rendered list cell.

        Return a metadata dict with at least ``url`` to link the cell, ``False``
        to suppress declarative link_fields fallback for this cell, or ``None``
        to allow the declarative fallback path.
        """
        return None

    def get_inline_edit_always_visible(self) -> bool:
        """
        Return whether inline-editable cells keep a subtle resting highlight.
        """
        return bool(resolve_config(self).inline_edit_always_visible)

    def get_inline_edit_highlight_accent(self) -> str:
        """
        Return the configured inline-edit highlight accent as a hex color.
        """
        return str(resolve_config(self).inline_edit_highlight_accent)

    @staticmethod
    def _parse_inline_edit_highlight_accent(value: str) -> tuple[int, int, int]:
        """
        Convert a hex color string into an RGB tuple.
        """
        normalized = value.strip().lstrip("#")
        if len(normalized) == 3:
            normalized = "".join(ch * 2 for ch in normalized)
        return (
            int(normalized[0:2], 16),
            int(normalized[2:4], 16),
            int(normalized[4:6], 16),
        )

    def _inline_edit_highlight_rgba(self, alpha: float) -> str:
        """
        Return an RGBA string derived from the configured inline-edit accent.
        """
        red, green, blue = self._parse_inline_edit_highlight_accent(
            self.get_inline_edit_highlight_accent()
        )
        return f"rgba({red}, {green}, {blue}, {alpha:.2f})"

    def get_inline_edit_highlight_palette(self) -> dict[str, str]:
        """
        Return the derived inline-edit highlight palette used by the list template.
        """
        return {
            "rest_bg": self._inline_edit_highlight_rgba(0.06),
            "rest_border": self._inline_edit_highlight_rgba(0.18),
            "hover_bg": self._inline_edit_highlight_rgba(0.15),
            "hover_border": self._inline_edit_highlight_rgba(0.35),
            "active_row_outline": self._inline_edit_highlight_rgba(0.85),
            "active_row_bg": self._inline_edit_highlight_rgba(0.12),
            "active_row_overlay": self._inline_edit_highlight_rgba(0.05),
            "active_widget_bg": self._inline_edit_highlight_rgba(0.15),
            "active_widget_border": self._inline_edit_highlight_rgba(0.35),
        }

    # Inline editing helpers -------------------------------------------------
    def get_inline_row_id_prefix(self) -> str:
        """Base DOM id prefix for inline-editable rows."""
        return "pc-row-"

    def get_inline_row_id(self, obj) -> str | None:
        """Return the DOM id for a given object's row."""
        if obj is None:
            return None
        pk = getattr(obj, "pk", None)
        if pk in (None, ""):
            return None
        return f"{self.get_inline_row_id_prefix()}{pk}"

    def get_inline_row_target(self, obj) -> str | None:
        """Return the HTMX target selector for the row container."""
        row_id = self.get_inline_row_id(obj)
        return f"#{row_id}" if row_id else None

    def get_inline_context(self) -> dict:
        """
        Context payload consumed by templates to determine inline editing state.
        """
        enabled = self.get_inline_editing()
        endpoint_name = getattr(self, "get_inline_row_endpoint_name", None)
        dependency_endpoint = getattr(self, "get_inline_dependency_endpoint_name", None)
        dependency_endpoint_name = (
            dependency_endpoint() if callable(dependency_endpoint) else None
        )
        dependency_endpoint_url = self._resolve_inline_endpoint(
            dependency_endpoint_name
        )
        return {
            "enabled": enabled,
            "fields": self.get_inline_edit_fields(),
            "dependencies": self.get_inline_field_dependencies(),
            "row_id_prefix": self.get_inline_row_id_prefix(),
            "row_endpoint_name": endpoint_name() if callable(endpoint_name) else None,
            "dependency_endpoint_name": dependency_endpoint_name,
            "dependency_endpoint_url": dependency_endpoint_url,
        }
