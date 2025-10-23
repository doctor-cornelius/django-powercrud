import logging
from typing import Dict, List, Optional
from django.db import models

log = logging.getLogger("powercrud")


class MetadataMixin:
    """Mixin providing metadata for bulk editing fields, including field info and choices."""

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
                is_m2m = field_type == 'ManyToManyField'

                # For related fields, get all possible related objects
                bulk_choices = None
                if is_relation and hasattr(field, 'related_model'):
                    # Use the related model's objects manager directly
                    bulk_choices = self.get_bulk_choices_for_field(field_name=field_name, field=field)

                field_info[field_name] = {
                    'field': field,
                    'type': field_type,
                    'is_relation': is_relation,
                    'is_m2m': is_m2m,  # Add a flag for M2M fields
                    'bulk_choices': bulk_choices,
                    'verbose_name': field.verbose_name,
                    'null': field.null if hasattr(field, 'null') else False,
                    'choices': getattr(field, 'choices', None),  # Add choices for fields with choices
                }
            except Exception as e:
                # Skip invalid fields
                print(f"Error processing field {field_name}: {str(e)}")
                continue

        return field_info

    def get_bulk_choices_for_field(self, field_name: str, field: models.Field) -> Optional[models.QuerySet] | None:
        """
        Hook to get the queryset for bulk choices for a given field in bulk edit.

        By default, returns all objects for the related model. Override in subclass to restrict choices.

        Args:
            field_name: Name of the field.
            field: Django model field instance.

        Returns:
            Queryset of choices for the related model, or None if not applicable.
        """
        if hasattr(field, 'related_model') and field.related_model is not None:
            qs = field.related_model.objects.all()
            
            # Apply dropdown sorting if configured
            sort_options = getattr(self, 'dropdown_sort_options', {})
            if field_name in sort_options:
                sort_field = sort_options[field_name]  # Can be "name" or "-name"
                qs = qs.order_by(sort_field)
            
            return qs
        return None
