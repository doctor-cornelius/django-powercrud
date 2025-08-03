from django.conf import settings
from django.core.paginator import Paginator, Page
from django.db.models import QuerySet


class PaginateMixin:
    """
    Provides pagination functionality for powercrud views.
    """
    def get_paginate_by(self):
        """Override of parent method to enable dealing with user-specified
        page size set on screen.
        """
        page_size = self.request.GET.get('page_size')
        if page_size == 'all':
            return None  # disables pagination, returns all records
        try:
            return int(page_size)
        except (TypeError, ValueError):
            return self.paginate_by  # fallback to default

    def get_page_size_options(self):
        standard_sizes = [5, 10, 25, 50, 100]
        default = self.paginate_by
        options = []
        for size in sorted(set(standard_sizes + ([default] if default and default not in standard_sizes else []))):
            if size is not None:
                options.append(str(size))  # convert to string here!
        return options

    def paginate_queryset(self, queryset, page_size):
        """
        Override paginate_queryset to reset to page 1 when filters are applied.
        """
        # If filters were applied, modify the GET request temporarily to force page 1
        original_GET = None
        if hasattr(self, '_reset_pagination') and self._reset_pagination:
            # Store original GET
            original_GET = self.request.GET
            # Create a copy we can modify
            modified_GET = self.request.GET.copy()
            # Set page to 1
            modified_GET['page'] = '1'
            # Replace with our modified version temporarily
            self.request.GET = modified_GET
            # Clean up flag
            delattr(self, '_reset_pagination')

        # Call parent implementation
        try:
            return super().paginate_queryset(queryset, page_size)
        finally:
            # Restore original GET if we modified it
            if original_GET is not None:
                self.request.GET = original_GET