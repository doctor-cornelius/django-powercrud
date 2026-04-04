from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.http import Http404

from .config_mixin import ConfigMixin


class CoreMixin(ConfigMixin):
    """
    Behavioural core mixin for queryset handling and list view orchestration.
    """

    def get_column_sort_fields_override(self) -> dict[str, str]:
        """
        Return explicit queryset ordering overrides keyed by visible column name.
        """
        configured = getattr(self.config(), "column_sort_fields_override", None)
        if isinstance(configured, dict):
            return configured
        return {}

    def _get_sortable_field_map(self) -> dict[str, str]:
        """
        Return the visible sortable column names mapped to canonical field/property names.
        """
        valid_fields = {f.name: f.name for f in self.model._meta.fields}
        properties = getattr(self.config(), "properties", []) or []
        valid_fields.update({p: p for p in properties})
        return valid_fields

    def _resolve_sort_column_name(self, field_name: str) -> str | None:
        """
        Resolve a requested sort column name to the configured visible column key.
        """
        valid_fields = self._get_sortable_field_map()
        if field_name in valid_fields:
            return valid_fields[field_name]

        matches = {key.lower(): value for key, value in valid_fields.items()}
        return matches.get(field_name.lower())

    def _resolve_default_sort_expression(self, column_name: str) -> str:
        """
        Resolve the default queryset ordering expression for a visible column.
        """
        try:
            model_field = self.model._meta.get_field(column_name)
        except FieldDoesNotExist:
            return column_name

        if (
            not getattr(model_field, "is_relation", False)
            or getattr(model_field, "many_to_many", False)
            or getattr(model_field, "auto_created", False)
        ):
            return column_name

        related_model = getattr(model_field, "related_model", None)
        if related_model is None:
            return column_name

        try:
            related_name_field = related_model._meta.get_field("name")
        except FieldDoesNotExist:
            return column_name

        if not getattr(related_name_field, "concrete", False):
            return column_name

        return f"{column_name}__name"

    def resolve_sort_expression(self, field_name: str) -> str | None:
        """
        Return the queryset ordering expression for a requested sort field.
        """
        column_name = self._resolve_sort_column_name(field_name)
        if column_name is None:
            return None

        overrides = self.get_column_sort_fields_override()
        override = overrides.get(column_name)
        if override:
            return override

        return self._resolve_default_sort_expression(column_name)

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
            sort_field = self.resolve_sort_expression(field_name)

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

    def get_show_bulk_selection_meta(self) -> bool:
        """
        Return whether the bulk-selection metadata row should be displayed.
        """
        return bool(self.config().show_bulk_selection_meta)

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
                filtered_queryset=queryset,
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
                filtered_queryset=queryset,
                sort=request.GET.get("sort", ""),  # Add sort to context
                use_htmx=self.get_use_htmx(),
                request=request,
                **record_count_context,
            )

        return self.render_to_response(context)
