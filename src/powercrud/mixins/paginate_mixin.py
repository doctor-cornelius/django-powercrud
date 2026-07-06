from .config_mixin import resolve_config


class PaginateMixin:
    """
    Provides pagination functionality for powercrud views.
    """

    def _get_fallback_page_size(self):
        """Return the configured default page size for invalid requests."""
        return resolve_config(self).paginate_by

    def _get_explicit_page_size_options(self):
        """Return normalized explicit page-size options, or None for legacy mode."""
        configured_options = resolve_config(self).page_size_options
        if configured_options is None:
            return None
        return sorted(
            {
                int(size)
                for size in configured_options
                if type(size) is int and size > 0
            }
        )

    def get_paginate_by(self):
        """Override of parent method to enable dealing with user-specified
        page size set on screen.
        """
        cfg = resolve_config(self)
        explicit_options = self._get_explicit_page_size_options()
        page_size = self.request.GET.get("page_size")
        if page_size == "all":
            if cfg.page_size_all_enabled is not False:
                return None  # disables pagination, returns all records
            return self._get_fallback_page_size()
        try:
            requested_size = int(page_size)
        except (TypeError, ValueError):
            return self._get_fallback_page_size()
        if requested_size <= 0:
            return self._get_fallback_page_size()
        if explicit_options is not None and requested_size not in explicit_options:
            return self._get_fallback_page_size()
        return requested_size

    def get_page_size_options(self):
        cfg = resolve_config(self)
        explicit_options = self._get_explicit_page_size_options()
        if explicit_options is not None:
            return [str(size) for size in explicit_options]

        standard_sizes = [5, 10, 25, 50, 100]
        default = cfg.paginate_by
        options = []
        for size in sorted(
            set(
                standard_sizes
                + ([default] if default and default not in standard_sizes else [])
            )
        ):
            if size is not None:
                options.append(str(size))  # convert to string here!
        return options

    def paginate_queryset(self, queryset, page_size):
        """
        Override paginate_queryset to reset to page 1 when filters are applied.
        """
        # If filters were applied, modify the GET request temporarily to force page 1
        original_GET = None
        if hasattr(self, "_reset_pagination") and self._reset_pagination:
            # Store original GET
            original_GET = self.request.GET
            # Create a copy we can modify
            modified_GET = self.request.GET.copy()
            # Set page to 1
            modified_GET["page"] = "1"
            # Replace with our modified version temporarily
            self.request.GET = modified_GET
            # Clean up flag
            delattr(self, "_reset_pagination")

        # Call parent implementation
        try:
            return super().paginate_queryset(queryset, page_size)
        finally:
            # Restore original GET if we modified it
            if original_GET is not None:
                self.request.GET = original_GET
