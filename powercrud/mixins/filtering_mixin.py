import logging

from django import forms
from django_filters import (
    FilterSet, CharFilter, DateFilter, NumberFilter, 
    BooleanFilter, ModelChoiceFilter, TimeFilter,
    ModelMultipleChoiceFilter,
)
from django.db import models
from django.conf import settings

log = logging.getLogger("powercrud")


class AllValuesModelMultipleChoiceFilter(ModelMultipleChoiceFilter):
    """Custom filter that requires ALL selected values to match (AND logic)"""
    def filter(self, qs, value):
        if not value:
            return qs
        
        # For each value, filter for items that have that value in the M2M field
        for val in value:
            qs = qs.filter(**{f"{self.field_name}": val})
        return qs


class HTMXFilterSetMixin:
    """
    Mixin that adds HTMX attributes to filter forms for dynamic updates.
    
    Attributes:
        HTMX_ATTRS (dict): Base HTMX attributes for form fields
        FIELD_TRIGGERS (dict): Mapping of form field types to HTMX trigger events
    """

    HTMX_ATTRS: dict[str, str] = {
        'hx-get': '',
        'hx-include': '[name]',  # Include all named form fields
    }

    FIELD_TRIGGERS: dict[type[forms.Widget] | str, str] = {
        forms.DateInput: 'change',
        forms.TextInput: 'keyup changed delay:300ms',
        forms.NumberInput: 'keyup changed delay:300ms',
        'default': 'change'
    }

    def setup_htmx_attrs(self) -> None:
        """Configure HTMX attributes for form fields and setup crispy form helper."""
        for field in self.form.fields.values():
            widget_class: type[forms.Widget] = type(field.widget)

            trigger: str = self.FIELD_TRIGGERS.get(widget_class, self.FIELD_TRIGGERS['default'])

            attrs: dict[str, str] = {**self.HTMX_ATTRS, 'hx-trigger': trigger}

            field.widget.attrs.update(attrs)


class FilteringMixin:
    """
    Provides dynamic FilterSet generation for powercrud views.
    """
    def get_filter_queryset_for_field(self, field_name, model_field):
        """Get an efficiently filtered and sorted queryset for filter options."""

        # Start with an empty queryset
        queryset = model_field.related_model.objects

        # Define model_fields early to ensure it exists in all code paths
        model_fields = [f.name for f in model_field.related_model._meta.fields]

        # Apply custom filters if defined
        filter_options = getattr(self, 'filter_queryset_options', {})
        if field_name in filter_options:
            filters = filter_options[field_name]
            if callable(filters):
                try:
                    # Add error handling for the callable
                    from datetime import datetime  # Ensure datetime is available
                    result = filters(self.request, field_name, model_field)
                    if isinstance(result, models.QuerySet):
                        queryset = result
                    else:
                        queryset = queryset.filter(**result)
                except Exception as e:
                    import logging
                    logging.error(f"Error in filter callable for {field_name}: {str(e)}")
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
        sort_options = getattr(self, 'dropdown_sort_options', {})
        if field_name in sort_options:
            sort_field = sort_options[field_name]  # Can be "name" or "-name"
            return queryset.order_by(sort_field)

        # If no specified sort field but model has common name fields, use that
        for field in ['name', 'title', 'label', 'display_name']:
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

    def get_filterset(self, queryset=None):
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

        if filterset_class is not None or filterset_fields is not None:
            # Check if any filter params (besides page/sort) are present
            filter_keys = [k for k in self.request.GET.keys() if k not in ('page', 'sort', 'page_size')]
            
            # Only reset pagination for actual filter form submissions
            is_filter_form_submission = self.request.headers.get('X-Filter-Setting-Request') == 'true'
            
            if filter_keys and 'page' in self.request.GET and is_filter_form_submission:
                setattr(self, '_reset_pagination', True)


        if filterset_class is None and filterset_fields is not None:
            use_htmx = self.get_use_htmx()
            use_crispy = self.get_use_crispy()

            class DynamicFilterSet(HTMXFilterSetMixin, FilterSet):
                """
                Dynamically create a FilterSet class based on the model fields.
                This class inherits from HTMXFilterSetMixin to add HTMX functionality
                and FilterSet for Django filtering capabilities.
                """
                framework = getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'daisyui')
                BASE_ATTRS = self.get_framework_styles()[framework]['filter_attrs']

                # Dynamically create filter fields based on the model's fields
                for field_name in filterset_fields:
                    model_field = self.model._meta.get_field(field_name)

                    # Handle GeneratedField special case
                    field_to_check = model_field.output_field if isinstance(model_field, models.GeneratedField) else model_field
                    # Check if BASE_ATTRS is structured by field type
                    if isinstance(BASE_ATTRS, dict) and ('text' in BASE_ATTRS or 'select' in BASE_ATTRS):
                        # Get appropriate attributes based on field type
                        if isinstance(field_to_check, models.ManyToManyField):
                            field_attrs = BASE_ATTRS.get('multiselect', BASE_ATTRS.get('select', BASE_ATTRS.get('default', {}))).copy()
                        elif isinstance(field_to_check, models.ForeignKey):
                            field_attrs = BASE_ATTRS.get('select', BASE_ATTRS.get('default', {})).copy()
                        elif isinstance(field_to_check, (models.CharField, models.TextField)):
                            field_attrs = BASE_ATTRS.get('text', BASE_ATTRS.get('default', {})).copy()
                        elif isinstance(field_to_check, models.DateField):
                            field_attrs = BASE_ATTRS.get('date', BASE_ATTRS.get('default', {})).copy()
                        elif isinstance(field_to_check, (models.IntegerField, models.DecimalField, models.FloatField)):
                            field_attrs = BASE_ATTRS.get('number', BASE_ATTRS.get('default', {})).copy()
                        elif isinstance(field_to_check, models.TimeField):
                            field_attrs = BASE_ATTRS.get('time', BASE_ATTRS.get('default', {})).copy()
                        elif isinstance(field_to_check, models.BooleanField):
                            field_attrs = BASE_ATTRS.get('select', BASE_ATTRS.get('default', {})).copy()
                        else:
                            field_attrs = BASE_ATTRS.get('default', {}).copy()
                    else:
                        # Legacy behavior - use the same attributes for all fields
                        field_attrs = BASE_ATTRS.copy()

                    # Create appropriate filter based on field type
                    if isinstance(field_to_check, models.ManyToManyField):
                        # Add max-height and other useful styles to the select widget
                        field_attrs.update({
                            'style': 'max-height: 200px; overflow-y: auto;',
                            'class': field_attrs.get('class', '') + ' select2',  # Add select2 class if you want to use Select2
                        })

                        # Choose between OR logic (ModelMultipleChoiceFilter) or AND logic (AllValuesModelMultipleChoiceFilter)
                        filter_class = AllValuesModelMultipleChoiceFilter if self.m2m_filter_and_logic else ModelMultipleChoiceFilter

                        locals()[field_name] = filter_class(
                            queryset=self.get_filter_queryset_for_field(field_name, model_field),
                            widget=forms.SelectMultiple(attrs=field_attrs)
                        )
                    elif isinstance(field_to_check, (models.CharField, models.TextField)):
                        locals()[field_name] = CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs=field_attrs))
                    elif isinstance(field_to_check, models.DateField):
                        if 'type' not in field_attrs:
                            field_attrs['type'] = 'date'
                        locals()[field_name] = DateFilter(widget=forms.DateInput(attrs=field_attrs))
                    elif isinstance(field_to_check, (models.IntegerField, models.DecimalField, models.FloatField)):
                        if 'step' not in field_attrs:
                            field_attrs['step'] = 'any'
                        locals()[field_name] = NumberFilter(widget=forms.NumberInput(attrs=field_attrs))
                    elif isinstance(field_to_check, models.BooleanField):
                        locals()[field_name] = BooleanFilter(widget=forms.Select(
                            attrs=field_attrs, choices=((None, '---------'), (True, True), (False, False))))
                    elif isinstance(field_to_check, models.ForeignKey):
                        locals()[field_name] = ModelChoiceFilter(
                            queryset=self.get_filter_queryset_for_field(field_name, model_field),
                            widget=forms.Select(attrs=field_attrs)
                        )
                    elif isinstance(field_to_check, models.TimeField):
                        if 'type' not in field_attrs:
                            field_attrs['type'] = 'time'
                        locals()[field_name] = TimeFilter(widget=forms.TimeInput(attrs=field_attrs))
                    else:
                        locals()[field_name] = CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs=field_attrs))

                class Meta:
                    model = self.model
                    fields = filterset_fields

                def __init__(self, *args, **kwargs):
                    """Initialize the FilterSet and set up HTMX attributes if needed."""
                    super().__init__(*args, **kwargs)
                    if use_htmx:
                        self.setup_htmx_attrs()

            filterset_class = DynamicFilterSet

        if filterset_class is None:
            return None

        return filterset_class(
            self.request.GET,
            queryset=queryset,
            request=self.request,
        )