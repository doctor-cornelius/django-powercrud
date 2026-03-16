from typing import Any

from django.http import Http404

from .config_mixin import ConfigMixin


class CoreMixin(ConfigMixin):
    """
    Behavioural core mixin for queryset handling and list view orchestration.
    """

    def get_inline_editing(self) -> bool:
        """
        Determine whether inline editing should be active for this view.
        Inline editing is only available when HTMX is enabled and
        `inline_edit_fields` resolves to a non-empty editable field list.
        """
        return bool(self.get_use_htmx() and self.get_inline_edit_fields())

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

    def get_show_record_count(self) -> bool:
        """
        Return whether the filtered record count metadata should be displayed.
        """
        return bool(self.config().show_record_count)

    def has_active_filters(self, filterset: Any | None) -> bool:
        """
        Return True when any bound filter field contains a non-empty value.

        Sort, page, and page-size parameters are intentionally excluded because
        they change presentation rather than the queryset membership.
        """
        if filterset is None or not hasattr(filterset, "form"):
            return False

        filter_fields = getattr(filterset.form, "fields", {}) or {}
        for field_name in filter_fields.keys():
            values = self.request.GET.getlist(field_name)
            if any(str(value).strip() for value in values):
                return True

        return False

    def get_queryset_record_count(
        self, queryset: Any, paginator: Any | None = None
    ) -> int:
        """
        Return the total number of records represented by the filtered queryset.
        """
        if paginator is not None:
            return int(paginator.count)

        count_method = getattr(queryset, "count", None)
        if callable(count_method):
            try:
                return int(count_method())
            except TypeError:
                # Some non-queryset iterables expose count(value) instead.
                pass

        return len(queryset)

    def get_record_count_context(
        self,
        queryset: Any,
        filterset: Any | None = None,
        page_obj: Any | None = None,
        paginator: Any | None = None,
    ) -> dict[str, Any]:
        """
        Build context for the optional record-count status line shown above the table.
        """
        total = self.get_queryset_record_count(queryset, paginator=paginator)

        if page_obj is not None and total > 0:
            start = page_obj.start_index()
            end = page_obj.end_index()
        else:
            start = 0
            end = 0

        return {
            "show_record_count": self.get_show_record_count(),
            "record_count_total": total,
            "record_count_start": start,
            "record_count_end": end,
            "record_count_has_active_filters": self.has_active_filters(filterset),
        }

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
            record_count_context = self.get_record_count_context(
                queryset=queryset,
                filterset=filterset,
            )
            context = self.get_context_data(
                page_obj=None,
                is_paginated=False,
                paginator=None,
                filterset=filterset,
                sort=request.GET.get("sort", ""),  # Add sort to context
                use_htmx=self.get_use_htmx(),
                request=request,
                **record_count_context,
            )
        else:
            # Paginated response
            page = self.paginate_queryset(queryset, paginate_by)
            self.object_list = page.object_list
            record_count_context = self.get_record_count_context(
                queryset=queryset,
                filterset=filterset,
                page_obj=page,
                paginator=page.paginator,
            )
            context = self.get_context_data(
                page_obj=page,
                is_paginated=page.has_other_pages(),
                paginator=page.paginator,
                filterset=filterset,
                sort=request.GET.get("sort", ""),  # Add sort to context
                use_htmx=self.get_use_htmx(),
                request=request,
                **record_count_context,
            )

        return self.render_to_response(context)
