from django.http import Http404

from .config_mixin import ConfigMixin


class CoreMixin(ConfigMixin):
    """
    Behavioural core mixin for queryset handling and list view orchestration.
    """

    def get_inline_editing(self) -> bool:
        """
        Determine whether inline editing should be active for this view.
        Inline editing is only available when HTMX is enabled and the view
        explicitly opts in.
        """
        return bool(self.config().inline_editing_active)

    def get_queryset(self):
        """
        Get the queryset for the view, applying sorting if specified.
        Always includes a secondary sort by primary key for stable pagination.
        """
        queryset = super().get_queryset()
        sort_param = self.request.GET.get("sort")

        if sort_param:
            # Handle descending sort (prefixed with '-')
            descending = sort_param.startswith("-")
            field_name = sort_param[1:] if descending else sort_param

            # Get all valid field names and properties
            valid_fields = {f.name: f.name for f in self.model._meta.fields}
            # Add any properties that are sortable
            properties = getattr(self.config(), "properties", []) or []
            valid_fields.update({p: p for p in properties})

            # Try to match the sort parameter to a valid field
            # First try exact match
            if field_name in valid_fields:
                sort_field = valid_fields[field_name]
            else:
                # Try case-insensitive match
                matches = {k.lower(): v for k, v in valid_fields.items()}
                sort_field = matches.get(field_name.lower())

            if sort_field:
                # Re-add the minus sign if it was descending
                if descending:
                    sort_field = f"-{sort_field}"
                    # Add secondary sort by -pk for descending
                    queryset = queryset.order_by(sort_field, "-pk")
                else:
                    # Add secondary sort by pk for ascending
                    queryset = queryset.order_by(sort_field, "pk")
        else:
            # If no sort specified, sort by pk as default
            queryset = queryset.order_by("pk")

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Handle GET requests for list view, including filtering and pagination.
        """
        queryset = self.get_queryset()
        filterset = self.get_filterset(queryset)
        if filterset is not None:
            queryset = filterset.qs

        if not self.allow_empty and not queryset.exists():
            raise Http404

        paginate_by = self.get_paginate_by()
        if paginate_by is None:
            # Unpaginated response
            self.object_list = queryset
            context = self.get_context_data(
                page_obj=None,
                is_paginated=False,
                paginator=None,
                filterset=filterset,
                sort=request.GET.get("sort", ""),  # Add sort to context
                use_htmx=self.get_use_htmx(),
                request=request,
            )
        else:
            # Paginated response
            page = self.paginate_queryset(queryset, paginate_by)
            self.object_list = page.object_list
            context = self.get_context_data(
                page_obj=page,
                is_paginated=page.has_other_pages(),
                paginator=page.paginator,
                filterset=filterset,
                sort=request.GET.get("sort", ""),  # Add sort to context
                use_htmx=self.get_use_htmx(),
                request=request,
            )

        return self.render_to_response(context)
