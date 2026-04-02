from django import forms
from collections import OrderedDict
from django_filters import (
    FilterSet,
    CharFilter,
    DateFilter,
    NumberFilter,
    BooleanFilter,
    ModelChoiceFilter,
    TimeFilter,
    ModelMultipleChoiceFilter,
)
from django.db import models
from django.utils.text import capfirst

from powercrud.conf import get_powercrud_setting
from powercrud.logging import get_logger
from .config_mixin import ConfigMixin, resolve_config

log = get_logger(__name__)

NULL_FILTER_SENTINEL = "__powercrud_empty__"


class AllValuesModelMultipleChoiceFilter(ModelMultipleChoiceFilter):
    """Custom filter that requires ALL selected values to match (AND logic)"""

    def filter(self, qs, value):
        if not value:
            return qs

        # For each value, filter for items that have that value in the M2M field
        for val in value:
            qs = qs.filter(**{f"{self.field_name}": val})
        return qs


class NullableModelChoiceField(forms.ModelChoiceField):
    """ModelChoiceField variant that accepts a sentinel for null-only filtering."""

    def __init__(
        self,
        *args,
        null_value: str = NULL_FILTER_SENTINEL,
        null_label: str = "Empty only",
        **kwargs,
    ):
        self.null_value = null_value
        self.null_label = null_label
        super().__init__(*args, **kwargs)
        self._prepend_null_choice()

    def _prepend_null_choice(self) -> None:
        """Insert the null sentinel choice after the standard blank choice."""
        base_choices = list(super().choices)
        if any(value == self.null_value for value, _label in base_choices):
            self.choices = base_choices
            return
        if base_choices:
            self.choices = [
                base_choices[0],
                (self.null_value, self.null_label),
                *base_choices[1:],
            ]
            return
        self.choices = [
            ("", self.empty_label or "---------"),
            (self.null_value, self.null_label),
        ]

    def to_python(self, value):
        """Return the sentinel unchanged so the filter can translate it."""
        if value == self.null_value:
            return value
        return super().to_python(value)


class NullableModelChoiceFilter(ModelChoiceFilter):
    """ModelChoiceFilter that maps a sentinel option to `field__isnull=True`."""

    field_class = NullableModelChoiceField

    def __init__(
        self,
        *args,
        null_value: str = NULL_FILTER_SENTINEL,
        null_label: str = "Empty only",
        **kwargs,
    ):
        self.null_value = null_value
        super().__init__(
            *args,
            null_value=null_value,
            null_label=null_label,
            **kwargs,
        )

    def filter(self, qs, value):
        """Apply an `isnull` lookup when the null sentinel is selected."""
        if value == self.null_value:
            return qs.filter(**{f"{self.field_name}__isnull": True})
        return super().filter(qs, value)


class HTMXFilterSetMixin:
    """
    Mixin that adds HTMX attributes to filter forms for dynamic updates.

    Attributes:
        HTMX_ATTRS (dict): Base HTMX attributes for form fields
        FIELD_TRIGGERS (dict): Mapping of form field types to HTMX trigger events
    """

    HTMX_ATTRS: dict[str, str] = {
        "hx-get": "",
        "hx-include": "[name]",  # Include all named form fields
    }

    FIELD_TRIGGERS: dict[type[forms.Widget] | str, str] = {
        forms.DateInput: "change",
        forms.TextInput: "keyup changed delay:300ms",
        forms.NumberInput: "keyup changed delay:300ms",
        "default": "change",
    }

    def setup_htmx_attrs(self) -> None:
        """Configure HTMX attributes for form fields and setup crispy form helper."""
        for field in self.form.fields.values():
            widget_class: type[forms.Widget] = type(field.widget)

            trigger: str = self.FIELD_TRIGGERS.get(
                widget_class, self.FIELD_TRIGGERS["default"]
            )

            attrs: dict[str, str] = {**self.HTMX_ATTRS, "hx-trigger": trigger}

            field.widget.attrs.update(attrs)


class FilteringMixin:
    """
    Provides dynamic FilterSet generation for powercrud views.
    """

    NULLABLE_SCALAR_FILTER_TYPES = (
        models.CharField,
        models.TextField,
        models.DateField,
        models.TimeField,
        models.IntegerField,
        models.DecimalField,
        models.FloatField,
        models.BooleanField,
    )

    def _is_boolean_like_filter_select_field(self, field: forms.Field) -> bool:
        """
        Return True when a filter select field represents a boolean choice set.

        Boolean-like selects should remain native controls so users can reliably
        distinguish unset/true/false semantics in filter forms.
        """
        if isinstance(field, forms.BooleanField):
            return True

        choices = [choice for choice in getattr(field, "choices", []) if choice]
        normalized_values = {
            str(value).strip().lower()
            for value, _label in choices
            if str(value).strip() != ""
        }
        if not normalized_values:
            return False
        boolean_values = {"true", "false", "1", "0"}
        return normalized_values.issubset(boolean_values)

    def _is_filter_searchable_select_enabled_for_field(
        self, field_name: str, field: forms.Field
    ) -> bool:
        """
        Resolve whether a filter field should receive Tom Select enhancement.

        This reuses the existing per-field hook when available so views can opt
        out specific fields consistently across regular, inline, bulk, and
        filter form controls.
        """
        field_hook = getattr(self, "get_searchable_select_enabled_for_field", None)
        if not callable(field_hook):
            return True
        return bool(field_hook(field_name=field_name, bound_field=field))

    def _apply_filter_searchable_select_attrs(self, filterset: FilterSet | None) -> None:
        """
        Tag eligible filter select widgets for frontend Tom Select enhancement.
        """
        if filterset is None:
            return
        if resolve_config(self).searchable_selects_enabled is False:
            return

        for field_name, field in filterset.form.fields.items():
            widget = getattr(field, "widget", None)
            if widget is None or not isinstance(widget, forms.Select):
                continue

            attrs = widget.attrs
            attrs.pop("data-powercrud-searchable-select", None)
            attrs.pop("data-powercrud-searchable-multiselect", None)

            if not self._is_filter_searchable_select_enabled_for_field(
                field_name=field_name, field=field
            ):
                continue

            if getattr(widget, "allow_multiple_selected", False):
                attrs["data-powercrud-searchable-multiselect"] = "true"
                continue

            if self._is_boolean_like_filter_select_field(field):
                continue

            attrs["data-powercrud-searchable-select"] = "true"

    def _apply_custom_filterset_htmx_attrs(self, filterset: FilterSet | None) -> None:
        """
        Apply HTMX widget attributes to custom filtersets when supported.

        Auto-generated filtersets already wire this up during construction. This
        helper preserves the same reactive filtering ergonomics for custom
        `filterset_class` implementations that expose `setup_htmx_attrs()`,
        typically by subclassing `HTMXFilterSetMixin`.
        """
        if filterset is None:
            return
        if not self.get_use_htmx():
            return

        setup_htmx_attrs = getattr(filterset, "setup_htmx_attrs", None)
        if callable(setup_htmx_attrs):
            setup_htmx_attrs()

    def get_filter_queryset_for_field(self, field_name, model_field):
        """Get an efficiently filtered and sorted queryset for filter options."""

        # Start with an empty queryset
        queryset = model_field.related_model.objects

        # Define model_fields early to ensure it exists in all code paths
        model_fields = [f.name for f in model_field.related_model._meta.fields]

        # Apply custom filters if defined
        filter_options = getattr(self, "filter_queryset_options", {})
        if field_name in filter_options:
            filters = filter_options[field_name]
            if callable(filters):
                try:
                    # Add error handling for the callable
                    result = filters(self.request, field_name, model_field)
                    if isinstance(result, models.QuerySet):
                        queryset = result
                    else:
                        queryset = queryset.filter(**result)
                except Exception as e:
                    import logging

                    logging.error(
                        f"Error in filter callable for {field_name}: {str(e)}"
                    )
            elif isinstance(filters, dict):
                # Apply filter dict directly
                queryset = queryset.filter(**filters)
            elif isinstance(filters, (int, str)):
                # Handle simple ID/PK filtering
                queryset = queryset.filter(pk=filters)
        else:
            # No filters specified, get all records
            queryset = queryset.all()

        # Check if we should sort by a specific field
        sort_options = resolve_config(self).dropdown_sort_options
        if field_name in sort_options:
            sort_field = sort_options[field_name]  # Can be "name" or "-name"
            return queryset.order_by(sort_field)

        # If no specified sort field but model has common name fields, use that
        for field in ["name", "title", "label", "display_name"]:
            if field in model_fields:
                return queryset.order_by(field)

        # Only if really necessary, fall back to string representation sorting
        sorted_objects = sorted(list(queryset), key=lambda x: str(x).lower())
        pk_list = [obj.pk for obj in sorted_objects]

        if not pk_list:  # Empty list case
            return queryset.none()

        # Return ordered queryset
        from django.db.models import Case, When, Value, IntegerField

        preserved_order = Case(
            *[When(pk=pk, then=Value(i)) for i, pk in enumerate(pk_list)],
            output_field=IntegerField(),
        )

        return queryset.filter(pk__in=pk_list).order_by(preserved_order)

    def get_null_filter_field_name(self, field_name: str) -> str:
        """Return the companion null-filter name for a base filter field."""
        return f"{field_name}__isnull"

    def _get_filter_widget_attrs(
        self,
        base_attrs: dict[str, dict[str, str]] | dict[str, str],
        field_to_check,
        *,
        prefer_select: bool = False,
    ) -> dict[str, str]:
        """Resolve widget attrs for a filter field based on model-field type."""
        if not isinstance(base_attrs, dict) or (
            "text" not in base_attrs and "select" not in base_attrs
        ):
            return base_attrs.copy()

        if prefer_select:
            return base_attrs.get("select", base_attrs.get("default", {})).copy()

        if isinstance(field_to_check, models.ManyToManyField):
            return base_attrs.get(
                "multiselect",
                base_attrs.get("select", base_attrs.get("default", {})),
            ).copy()
        if isinstance(field_to_check, (models.ForeignKey, models.OneToOneField)):
            return base_attrs.get("select", base_attrs.get("default", {})).copy()
        if isinstance(field_to_check, (models.CharField, models.TextField)):
            return base_attrs.get("text", base_attrs.get("default", {})).copy()
        if isinstance(field_to_check, models.DateField):
            return base_attrs.get("date", base_attrs.get("default", {})).copy()
        if isinstance(
            field_to_check,
            (models.IntegerField, models.DecimalField, models.FloatField),
        ):
            return base_attrs.get("number", base_attrs.get("default", {})).copy()
        if isinstance(field_to_check, models.TimeField):
            return base_attrs.get("time", base_attrs.get("default", {})).copy()
        if isinstance(field_to_check, models.BooleanField):
            return base_attrs.get("select", base_attrs.get("default", {})).copy()
        return base_attrs.get("default", {}).copy()

    def _field_supports_auto_null_filter(self, field_name: str, field_to_check) -> bool:
        """Return whether a field should receive automatic null-filter support."""
        if getattr(field_to_check, "null", False) is not True:
            return False
        return field_name not in resolve_config(self).filter_null_fields_exclude

    def _get_filter_label(self, model_field) -> str:
        """Return the base label for an auto-generated filter field."""
        return capfirst(model_field.verbose_name)

    def _field_uses_merged_null_relation_filter(self, field_to_check) -> bool:
        """Return whether a field should merge null filtering into its select."""
        return isinstance(field_to_check, (models.ForeignKey, models.OneToOneField))

    def _field_uses_companion_null_filter(self, field_to_check) -> bool:
        """Return whether a field should get a companion null filter."""
        return isinstance(
            field_to_check, self.NULLABLE_SCALAR_FILTER_TYPES
        ) and not isinstance(field_to_check, models.DateTimeField)

    def _build_companion_null_filter(
        self,
        field_name: str,
        model_field,
        field_attrs: dict[str, str],
    ) -> BooleanFilter:
        """Build the companion boolean filter used for nullable scalar fields."""
        label = f"{model_field.verbose_name} is empty".capitalize()
        return BooleanFilter(
            field_name=field_name,
            lookup_expr="isnull",
            label=label,
            widget=forms.Select(
                attrs=field_attrs,
                choices=(
                    ("", "---------"),
                    ("true", "Yes"),
                    ("false", "No"),
                ),
            ),
        )

    def get_filterset(self, queryset=None):  # pragma: no cover
        """
        Create a dynamic FilterSet class based on provided parameters:
            - filterset_class (in which case the provided class is used); or
            - filterset_fields (in which case a dynamic class is created)

        Args:
            queryset: Optional queryset to filter

        Returns:
            FilterSet: Configured filter set instance or None
        """
        filterset_class = getattr(self, "filterset_class", None)
        filterset_fields = getattr(self, "filterset_fields", None)
        if isinstance(filterset_fields, list):
            filterset_fields = ConfigMixin._dedupe_preserving_first(filterset_fields)
        using_custom_filterset_class = filterset_class is not None

        if filterset_class is not None or filterset_fields is not None:
            # Check if any filter params (besides page/sort) are present
            filter_keys = [
                k
                for k in self.request.GET.keys()
                if k not in ("page", "sort", "page_size")
            ]

            # Only reset pagination for actual filter form submissions
            is_filter_form_submission = (
                self.request.headers.get("X-Filter-Setting-Request") == "true"
            )

            if filter_keys and "page" in self.request.GET and is_filter_form_submission:
                setattr(self, "_reset_pagination", True)

        if filterset_class is None and filterset_fields is not None:
            use_htmx = self.get_use_htmx()
            framework = get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK")
            base_attrs = self.get_framework_styles()[framework]["filter_attrs"]
            declared_filters = {}
            filter_form_order = []

            for field_name in filterset_fields:
                model_field = self.model._meta.get_field(field_name)

                if hasattr(models, "GeneratedField") and isinstance(
                    model_field, models.GeneratedField
                ):
                    field_to_check = model_field.output_field
                else:
                    field_to_check = model_field

                field_attrs = self._get_filter_widget_attrs(base_attrs, field_to_check)

                if isinstance(field_to_check, models.ManyToManyField):
                    filter_class = (
                        AllValuesModelMultipleChoiceFilter
                        if resolve_config(self).m2m_filter_and_logic
                        else ModelMultipleChoiceFilter
                    )
                    declared_filters[field_name] = filter_class(
                        queryset=self.get_filter_queryset_for_field(
                            field_name, model_field
                        ),
                        widget=forms.SelectMultiple(attrs=field_attrs),
                    )
                elif isinstance(field_to_check, (models.CharField, models.TextField)):
                    declared_filters[field_name] = CharFilter(
                        lookup_expr="icontains",
                        label=self._get_filter_label(model_field),
                        widget=forms.TextInput(attrs=field_attrs),
                    )
                elif isinstance(field_to_check, models.DateField):
                    if "type" not in field_attrs:
                        field_attrs["type"] = "date"
                    declared_filters[field_name] = DateFilter(
                        widget=forms.DateInput(attrs=field_attrs)
                    )
                elif isinstance(
                    field_to_check,
                    (models.IntegerField, models.DecimalField, models.FloatField),
                ):
                    if "step" not in field_attrs:
                        field_attrs["step"] = "any"
                    declared_filters[field_name] = NumberFilter(
                        widget=forms.NumberInput(attrs=field_attrs)
                    )
                elif isinstance(field_to_check, models.BooleanField):
                    declared_filters[field_name] = BooleanFilter(
                        widget=forms.Select(
                            attrs=field_attrs,
                            choices=(
                                (None, "---------"),
                                (True, True),
                                (False, False),
                            ),
                        )
                    )
                elif isinstance(field_to_check, (models.ForeignKey, models.OneToOneField)):
                    filter_class = (
                        NullableModelChoiceFilter
                        if self._field_supports_auto_null_filter(
                            field_name, field_to_check
                        )
                        and self._field_uses_merged_null_relation_filter(field_to_check)
                        else ModelChoiceFilter
                    )
                    declared_filters[field_name] = filter_class(
                        queryset=self.get_filter_queryset_for_field(
                            field_name, model_field
                        ),
                        widget=forms.Select(attrs=field_attrs),
                    )
                elif isinstance(field_to_check, models.TimeField):
                    if "type" not in field_attrs:
                        field_attrs["type"] = "time"
                    declared_filters[field_name] = TimeFilter(
                        widget=forms.TimeInput(attrs=field_attrs)
                    )
                else:
                    declared_filters[field_name] = CharFilter(
                        lookup_expr="icontains",
                        label=self._get_filter_label(model_field),
                        widget=forms.TextInput(attrs=field_attrs),
                    )
                filter_form_order.append(field_name)

                if self._field_supports_auto_null_filter(
                    field_name, field_to_check
                ) and self._field_uses_companion_null_filter(field_to_check):
                    null_field_name = self.get_null_filter_field_name(field_name)
                    null_attrs = self._get_filter_widget_attrs(
                        base_attrs,
                        field_to_check,
                        prefer_select=True,
                    )
                    declared_filters[null_field_name] = (
                        self._build_companion_null_filter(
                            field_name,
                            model_field,
                            null_attrs,
                        )
                    )
                    filter_form_order.append(null_field_name)

            class Meta:
                """FilterSet metadata for the dynamically generated class."""

                model = self.model
                fields = filterset_fields

            def __init__(filterset_self, *args, **kwargs):
                """Initialize the FilterSet and set up HTMX attributes if needed."""
                FilterSet.__init__(filterset_self, *args, **kwargs)
                ordered_filters = OrderedDict()
                for filter_name in filter_form_order:
                    if filter_name in filterset_self.filters:
                        ordered_filters[filter_name] = filterset_self.filters[
                            filter_name
                        ]
                for filter_name, filter_value in filterset_self.filters.items():
                    if filter_name not in ordered_filters:
                        ordered_filters[filter_name] = filter_value
                filterset_self.filters = ordered_filters
                filterset_self.form.order_fields(list(ordered_filters.keys()))
                if use_htmx:
                    filterset_self.setup_htmx_attrs()

            filterset_class = type(
                f"{self.model.__name__}DynamicFilterSet",
                (HTMXFilterSetMixin, FilterSet),
                {
                    "__doc__": (
                        "Dynamically generated FilterSet for PowerCRUD auto-filters."
                    ),
                    "__module__": self.__class__.__module__,
                    "Meta": Meta,
                    "__init__": __init__,
                    **declared_filters,
                },
            )

        if filterset_class is None:
            return None

        filterset = filterset_class(
            self.request.GET,
            queryset=queryset,
            request=self.request,
        )
        if using_custom_filterset_class:
            self._apply_custom_filterset_htmx_attrs(filterset)
        self._apply_filter_searchable_select_attrs(filterset)
        return filterset
