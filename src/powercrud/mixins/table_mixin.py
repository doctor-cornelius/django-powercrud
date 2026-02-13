from .config_mixin import resolve_config


class TableMixin:
    """
    Provides methods for table styling and layout.
    """

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
