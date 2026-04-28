from typing import Dict, List, Optional
from django.db import models

from powercrud.logging import get_logger
from ..config_mixin import resolve_config

log = get_logger(__name__)


class MetadataMixin:
    """Mixin providing metadata for bulk editing fields, including field info and choices."""

    def _get_bulk_field_queryset_meta(self, field_name: str) -> dict:
        """
        Return declarative queryset metadata relevant to bulk relation choices.
        """
        dependencies = resolve_config(self).field_queryset_dependencies or {}
        meta = dependencies.get(field_name)
        if not isinstance(meta, dict):
            return {}

        static_filters = meta.get("static_filters") or {}
        if not isinstance(static_filters, dict):
            log.warning(
                "Bulk field queryset metadata for '%s' ignored non-dictionary static_filters on %s",
                field_name,
                self.__class__.__name__,
            )
            static_filters = {}

        order_by = meta.get("order_by")
        if order_by is not None and not isinstance(order_by, str):
            log.warning(
                "Bulk field queryset metadata for '%s' ignored non-string order_by on %s",
                field_name,
                self.__class__.__name__,
            )
            order_by = None

        if not static_filters and order_by is None:
            return {}

        return {
            "static_filters": static_filters,
            "order_by": order_by,
        }

    def _get_bulk_field_info(self, bulk_fields: List[str]) -> Dict[str, Dict]:
        """
        Get information about fields for bulk editing.

        Args:
            bulk_fields: List of field names for bulk editing.

        Returns:
            Dictionary mapping field names to their metadata (type, relation flags, choices, etc.).
        """
        field_info = {}

        for field_name in bulk_fields:
            try:
                field = self.model._meta.get_field(field_name)

                # Get field type and other metadata
                field_type = field.get_internal_type()
                is_relation = field.is_relation
                is_m2m = field_type == "ManyToManyField"

                # For related fields, get all possible related objects
                bulk_choices = None
                if is_relation and hasattr(field, "related_model"):
                    # Use the related model's objects manager directly
                    bulk_choices = self.get_bulk_choices_for_field(
                        field_name=field_name, field=field
                    )

                field_info[field_name] = {
                    "field": field,
                    "type": field_type,
                    "is_relation": is_relation,
                    "is_m2m": is_m2m,  # Add a flag for M2M fields
                    "bulk_choices": bulk_choices,
                    "verbose_name": field.verbose_name,
                    "null": field.null if hasattr(field, "null") else False,
                    "blank": field.blank if hasattr(field, "blank") else False,
                    "choices": getattr(
                        field, "choices", None
                    ),  # Add choices for fields with choices
                    "searchable_select": self._is_bulk_searchable_select(
                        field_name=field_name,
                        field=field,
                    ),
                }
            except Exception as e:
                # Skip invalid fields
                print(f"Error processing field {field_name}: {str(e)}")
                continue

        return field_info

    def _is_bulk_searchable_select(
        self, *, field_name: str, field: models.Field
    ) -> bool:
        """
        Determine whether a bulk-edit field should render as a searchable select.
        """
        if resolve_config(self).searchable_selects_enabled is False:
            return False

        field_type = field.get_internal_type()
        if field_type in {"BooleanField", "NullBooleanField", "ManyToManyField"}:
            return False

        if not (
            field.is_relation and field_type in {"ForeignKey", "OneToOneField"}
        ) and not getattr(field, "choices", None):
            return False

        field_hook = getattr(self, "get_searchable_select_enabled_for_field", None)
        if callable(field_hook):
            try:
                return bool(
                    field_hook(
                        field_name=field_name,
                        bound_field=None,
                    )
                )
            except TypeError:
                # Backward-compatible call style for simplified overrides.
                return bool(field_hook(field_name))

        return True

    def get_bulk_choices_for_field(
        self, field_name: str, field: models.Field
    ) -> Optional[models.QuerySet] | None:
        """
        Hook to get the queryset for bulk choices for a given field in bulk edit.

        By default, returns related-model objects filtered by any declarative
        static queryset rules for the field, then ordered by dependency
        metadata or dropdown sort config. Override in a subclass to take full
        control of bulk choices for that field.

        Args:
            field_name: Name of the field.
            field: Django model field instance.

        Returns:
            Queryset of choices for the related model, or None if not applicable.
        """
        if hasattr(field, "related_model") and field.related_model is not None:
            qs = field.related_model.objects.all()
            queryset_meta = self._get_bulk_field_queryset_meta(field_name)

            static_filters = queryset_meta.get("static_filters") or {}
            if static_filters:
                qs = qs.filter(**static_filters)

            sort_field = queryset_meta.get("order_by")
            if sort_field:
                qs = qs.order_by(sort_field)
            else:
                # Apply dropdown sorting if configured
                sort_options = resolve_config(self).dropdown_sort_options
                if field_name in sort_options:
                    sort_field = sort_options[field_name]  # Can be "name" or "-name"
                    qs = qs.order_by(sort_field)

            return qs
        return None
