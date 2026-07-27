from typing import Dict, List, Optional
from django import forms
from django.db import models

from powercrud.labels import resolve_field_label
from powercrud.logging import get_logger
from powercrud.template_packs import WidgetPolicyContext, get_template_pack_server_adapter
from powercrud.widget_policy import apply_widget_presentation, get_model_widget_kind
from ..config_mixin import resolve_config

log = get_logger(__name__)


class MetadataMixin:
    """Mixin providing metadata for bulk editing fields, including field info and choices."""

    def _get_bulk_enhancement_intent(self, field_name: str) -> str:
        """Return the view and field override intent for one bulk value control."""
        setting = resolve_config(self).searchable_selects
        intent = (
            "enabled"
            if setting is True
            else "disabled"
            if setting is False
            else "default"
        )
        field_hook = getattr(self, "get_searchable_select_enabled_for_field", None)
        if not callable(field_hook):
            return intent
        try:
            field_setting = field_hook(field_name=field_name, bound_field=None)
        except TypeError:
            field_setting = field_hook(field_name)
        if field_setting is True:
            return "enabled"
        if field_setting is False:
            return "disabled"
        return intent

    def _build_bulk_value_control(
        self, *, field_name: str, field: models.Field, info: dict
    ) -> forms.BoundField:
        """Build one policy-owned, initially disabled bulk value widget."""
        choices = list(info.get("bulk_choices") or [])
        choice_pairs = [(str(choice.pk), str(choice)) for choice in choices]
        field_type = field.get_internal_type()
        is_m2m = info["is_m2m"]

        if is_m2m:
            form_field: forms.Field = forms.MultipleChoiceField(
                choices=choice_pairs,
                required=False,
            )
        elif field_type == "BooleanField":
            form_field = forms.ChoiceField(
                choices=[("", "-- No change --"), ("true", "Yes"), ("false", "No")],
                required=False,
            )
        elif field.is_relation:
            relation_choices = [("", "-- No change --")]
            if info["null"]:
                relation_choices.append(("null", "-- None --"))
            relation_choices.extend(choice_pairs)
            form_field = forms.ChoiceField(choices=relation_choices, required=False)
        elif info.get("choices"):
            value_choices = [("", "-- No change --")]
            if info["null"] or info["blank"]:
                value_choices.append(
                    ("null", "-- None --" if info["null"] else "-- Blank --")
                )
            value_choices.extend((str(value), label) for value, label in info["choices"])
            form_field = forms.ChoiceField(choices=value_choices, required=False)
        elif isinstance(field, models.DateTimeField):
            form_field = forms.DateTimeField(required=False)
        elif isinstance(field, models.DateField):
            form_field = forms.DateField(required=False)
        elif isinstance(field, models.TimeField):
            form_field = forms.TimeField(required=False)
        elif isinstance(field, (models.IntegerField, models.DecimalField, models.FloatField)):
            form_field = forms.DecimalField(required=False)
            form_field.widget.attrs["step"] = (
                "1" if isinstance(field, models.IntegerField) else "any"
            )
        elif isinstance(field, models.TextField):
            form_field = forms.CharField(required=False, widget=forms.Textarea)
        elif isinstance(field, models.FileField):
            form_field = forms.FileField(required=False)
        else:
            form_field = forms.CharField(required=False)

        form_field.disabled = True
        context = WidgetPolicyContext(
            surface="bulk",
            kind=get_model_widget_kind(field),
            render_mode="native",
            field_name=field_name,
            required=False,
            disabled=True,
            is_relation=field.is_relation,
            has_dependency=False,
            enhancement_intent=self._get_bulk_enhancement_intent(field_name),
        )
        apply_widget_presentation(
            form_field,
            get_template_pack_server_adapter().get_widget_presentation(context),
        )
        bulk_form = forms.Form()
        bulk_form.fields[field_name] = form_field
        return bulk_form[field_name]

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

                info = {
                    "field": field,
                    "type": field_type,
                    "is_relation": is_relation,
                    "is_m2m": is_m2m,  # Add a flag for M2M fields
                    "bulk_choices": bulk_choices,
                    "verbose_name": resolve_field_label(self, field_name, field),
                    "null": field.null if hasattr(field, "null") else False,
                    "blank": field.blank if hasattr(field, "blank") else False,
                    "choices": getattr(
                        field, "choices", None
                    ),  # Add choices for fields with choices
                }
                info["control"] = self._build_bulk_value_control(
                    field_name=field_name,
                    field=field,
                    info=info,
                )
                # Preserve this focused-template context flag for applications
                # that still render their own bulk partial. Pack templates use
                # the policy-owned BoundField above instead.
                info["searchable_select"] = (
                    info["control"].field.widget.attrs.get(
                        "data-powercrud-searchable-select"
                    )
                    == "true"
                )
                field_info[field_name] = info
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
