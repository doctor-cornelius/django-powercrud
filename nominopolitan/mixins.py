from django import forms
from django.db import models

from django.http import Http404
from django.urls import NoReverseMatch, path, reverse
from django.utils.decorators import classonlymethod
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.template.response import TemplateResponse

from django.conf import settings
from django.db.models.fields.reverse_related import ManyToOneRel

import json
import logging
log = logging.getLogger("nominopolitan")

from crispy_forms.helper import FormHelper
from django import forms
from django_filters import (
    FilterSet, CharFilter, DateFilter, NumberFilter, 
    BooleanFilter, ModelChoiceFilter, TimeFilter,
    )
from django_filters.filterset import filterset_factory
from neapolitan.views import Role

class HTMXFilterSetMixin:
    HTMX_ATTRS = {
        'hx-get': '',
        # 'hx-target': '#content',
        'hx-include': '[name]',  # This will include all named form fields
    }

    FIELD_TRIGGERS = {
        forms.DateInput: 'change',
        forms.TextInput: 'keyup changed delay:300ms',
        forms.NumberInput: 'keyup changed delay:300ms',
        'default': 'change'
    }

    def setup_htmx_attrs(self):
        for field in self.form.fields.values():
            widget_class = type(field.widget)
            trigger = self.FIELD_TRIGGERS.get(widget_class, self.FIELD_TRIGGERS['default'])
            attrs = {**self.HTMX_ATTRS, 'hx-trigger': trigger, }
            field.widget.attrs.update(attrs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.wrapper_class = 'col-auto'
        self.helper.template = 'bootstrap5/layout/inline_field.html'

class NominopolitanMixin:
    namespace = None
    create_form_class = None
    # templates_path = "nominopolitan" # path to overridden set of templates
    templates_path = f"nominopolitan/{getattr(
        settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bulma'
        )}"
    base_template_path = f"{templates_path}/base.html" # location of template

    use_crispy = None # True = use crispy-forms if installed; False otherwise.

    exclude = [] # fields to exclude from the list
    properties = [] # properties to include in the list
    properties_exclude = [] # properties to exclude from the list

    detail_fields = [] # fields to include in the detail view
    detail_exclude = [] # fields to exclude from the detail view
    detail_properties = [] # properties to include in the detail view
    detail_properties_exclude = [] # properties to exclude from the detail view

    use_htmx = None
    hx_trigger = None

    use_modal = None
    modal_id = None # Allows override of the default modal id (#nominopolitanModalContent)
    modal_target = None # Allows override of the default modal target
        # which is #nominopolitanModalContent. Useful if for example
        # the project has a modal with a different id available
        # eg in the base template.

    table_font_size = None
    def get_table_font_size(self):
        # The font size for the table (buttons, filters, column headers, rows) in object_list.html
        return self.table_font_size or '0.875'

    def get_framework_styles(self):
        
        table_font_size = self.get_table_font_size()

        return {
            'bulma': {
                'base': 'button is-small',
                'button_style': 'font-size: 0.875rem;' ,
                'actions': {
                    'View': 'is-info',
                    'Edit': 'is-link',
                    'Delete': 'is-danger'
                },
                'extra_default': 'is-link',
                'modal_attrs': '',
                'filter_attrs': {
                    'class': 'input is-small',
                    'style': 'font-size: 0.875rem;'
                }
            },
            'bootstrap5': {
                'font-size': f'{table_font_size}rem;',
                'base': 'btn btn-sm py-0',
                'button_style': f'font-size: {table_font_size}rem;' ,
                'filter_attrs': {
                    'class': 'form-control-xs small py-1',
                    'style': f'font-size: {table_font_size}rem;'
                },
                'actions': {
                    'View': 'btn-info',
                    'Edit': 'btn-primary',
                    'Delete': 'btn-danger'
                },
                'extra_default': 'btn-primary',
                'modal_attrs': f'data-bs-toggle="modal" data-bs-target="{self.get_modal_id()}"',
            }
        }


    def list(self, request, *args, **kwargs):
        """GET handler for the list view."""

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
                test_variable="Testing",
                page_obj=None,
                is_paginated=False,
                paginator=None,
                filterset=filterset,
            )
        else:
            # Paginated response
            page = self.paginate_queryset(queryset, paginate_by)
            self.object_list = page.object_list
            context = self.get_context_data(
                test_variable="Testing",
                page_obj=page,
                is_paginated=page.has_other_pages(),
                paginator=page.paginator,
                filterset=filterset,
            )

        return self.render_to_response(context)


    def get_filterset(self, queryset=None):
        filterset_class = getattr(self, "filterset_class", None)
        filterset_fields = getattr(self, "filterset_fields", None)

        if filterset_class is None and filterset_fields:
            use_htmx = self.get_use_htmx()
            use_crispy = self.get_use_crispy()

            class DynamicFilterSet(HTMXFilterSetMixin, FilterSet):
                framework = getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bulma')
                BASE_ATTRS = self.get_framework_styles()[framework]['filter_attrs']

                # Define filters here, before Meta
                for field_name in filterset_fields:
                    model_field = self.model._meta.get_field(field_name)
                    field_attrs = BASE_ATTRS.copy()

                    # Handle GeneratedField special case first
                    if isinstance(model_field, models.GeneratedField):
                        field_to_check = model_field.output_field
                    else:
                        field_to_check = model_field                    

                    if isinstance(field_to_check, models.CharField):
                        locals()[field_name] = CharFilter(
                            lookup_expr='icontains',
                            widget=forms.TextInput(attrs=field_attrs)
                        )
                    elif isinstance(field_to_check, models.DateField):
                        field_attrs['type'] = 'date'
                        locals()[field_name] = DateFilter(
                            widget=forms.DateInput(attrs=field_attrs)
                        )
                    elif isinstance(field_to_check, (models.IntegerField, models.DecimalField, models.FloatField)):
                        field_attrs['step'] = 'any'
                        locals()[field_name] = NumberFilter(
                            widget=forms.NumberInput(attrs=field_attrs)
                        )
                    elif isinstance(field_to_check, models.BooleanField):
                        locals()[field_name] = BooleanFilter(
                            widget=forms.Select(attrs=field_attrs, choices=((None, '---------'), (True, True), (False, False)))
                        )
                    elif isinstance(field_to_check, models.ForeignKey):
                        locals()[field_name] = ModelChoiceFilter(
                            queryset=model_field.related_model.objects.all(),
                            widget=forms.Select(attrs=field_attrs)
                        )
                    elif isinstance(field_to_check, models.TimeField):
                        field_attrs.update({'type': 'time'})
                        locals()[field_name] = TimeFilter(
                            widget=forms.TimeInput(attrs=field_attrs)
                        )
                    else:
                        locals()[field_name] = CharFilter(
                            widget=forms.TextInput(attrs=field_attrs)
                        )

                class Meta:
                    model = self.model
                    fields = filterset_fields
               
                def __init__(self, *args, **kwargs):
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
    
    def _get_all_fields(self):
        fields = [field.name for field in self.model._meta.get_fields()]
            
        # Exclude reverse relations
        fields = [
            field.name for field in self.model._meta.get_fields()
            if not isinstance(field, ManyToOneRel)
        ]
        return fields

    
    def _get_all_properties(self):
        return [name for name in dir(self.model)
                    if isinstance(getattr(self.model, name), property) and name != 'pk'
                ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # determine the starting list of fields (before exclusions)
        if not self.fields or self.fields == '__all__':
            # set to all fields in model
            self.fields = self._get_all_fields()
        elif type(self.fields) == list:
            # check all are valid fields
            all_fields = self._get_all_fields()
            for field in self.fields:
                if field not in all_fields:
                    raise ValueError(f"Field {field} not defined in {self.model.__name__}")
        elif type(self.fields) != list:
            raise TypeError("fields must be a list")        
        else:
            raise ValueError("fields must be '__all__', a list of valid fields or not defined")

        # exclude fields
        if type(self.exclude) == list:
            self.fields = [field for field in self.fields if field not in self.exclude]
        else:
            raise TypeError("exclude must be a list")

        if self.properties:
            if self.properties == '__all__':
                # Set self.properties to a list of every property in self.model
                self.properties = self._get_all_properties()
            elif type(self.properties) == list:
                # check all are valid properties
                all_properties = self._get_all_properties()
                for prop in self.properties:
                    if prop not in all_properties:
                        raise ValueError(f"Property {prop} not defined in {self.model.__name__}")
            elif type(self.properties) != list:
                raise TypeError("properties must be a list or '__all__'")
            
        # exclude properties
        if type(self.properties_exclude) == list:
            self.properties = [prop for prop in self.properties if prop not in self.properties_exclude]
        else:
            raise TypeError("properties_exclude must be a list")

        # determine the starting list of detail_fields (before exclusions)
        if self.detail_fields == '__all__':
            # Set self.detail_fields to a list of every field in self.model
            self.detail_fields = self._get_all_fields()        
        elif not self.detail_fields or self.detail_fields == '__fields__':
            # Set self.detail_fields to self.fields
            self.detail_fields = self.fields
        elif type(self.detail_fields) == list:
            # check all are valid fields
            all_fields = self._get_all_fields()
            for field in self.detail_fields:
                if field not in all_fields:
                    raise ValueError(f"detail_field {field} not defined in {self.model.__name__}")
        elif type(self.detail_fields) != list:
            raise TypeError("detail_fields must be a list or '__all__' or '__fields__' or a list of fields")

        # exclude detail_fields
        if type(self.detail_exclude) == list:
            self.detail_fields = [field for field in self.detail_fields 
                                  if field not in self.detail_exclude]
        else:
            raise TypeError("detail_fields_exclude must be a list")

        # add specified detail_properties            
        if self.detail_properties:
            if self.detail_properties == '__all__':
                # Set self.detail_properties to a list of every property in self.model
                self.detail_properties = self._get_all_properties()
            elif self.detail_properties == '__properties__':
                # Set self.detail_properties to a list of every property in self.model
                self.detail_properties = self.properties
            elif type(self.detail_properties) == list:
                # check all are valid properties
                all_properties = self._get_all_properties()
                for prop in self.detail_properties:
                    if prop not in all_properties:
                        raise ValueError(f"Property {prop} not defined in {self.model.__name__}")
            elif type(self.detail_properties) != list:
                raise TypeError("detail_properties must be a list or '__all__' or '__properties__'")

        # exclude detail_properties
        if type(self.detail_properties_exclude) == list:
            self.detail_properties = [prop for prop in self.detail_properties 
                                  if prop not in self.detail_properties_exclude]
        else:
            raise TypeError("detail_properties_exclude must be a list")
        
    def get_session_key(self):
        return f"nominopolitan_list_target_{self.url_base}"

    def get_original_target(self):
        return self.request.session.get(self.get_session_key(), None)

    def get_use_htmx(self):
        # return True if it was set to be True, and False otherwise
        return self.use_htmx is True

    def get_use_modal(self):
        # must be using htmx for this to work
        result = self.use_modal is True and self.get_use_htmx()
        return result
    
    def get_modal_id(self):
        # use default if modal_id not set
        modal_id = self.modal_id or 'nominopolitanBaseModal'
        return f'#{modal_id}'
    
    def get_modal_target(self):
        # use default if modal_target not set
        modal_target = self.modal_target or 'nominopolitanModalContent'
        return f'#{modal_target}'
    
    def get_hx_trigger(self):
        if not self.get_use_htmx() or not self.hx_trigger:
            return None
            
        if isinstance(self.hx_trigger, (str, int, float)):
            return str(self.hx_trigger)
        elif isinstance(self.hx_trigger, dict):
            # Validate all keys are strings
            if not all(isinstance(k, str) for k in self.hx_trigger.keys()):
                raise TypeError("HX-Trigger dict keys must be strings")
            return json.dumps(self.hx_trigger)
        else:
            raise TypeError("hx_trigger must be either a string or dict with string keys")


    def get_htmx_target(self):

        # only if using htmx
        if not self.get_use_htmx():
            htmx_target = None
        elif self.use_modal:
            htmx_target = self.get_modal_target()
        elif hasattr(self.request, 'htmx') and self.request.htmx.target:
            # return the target of the original list request
            htmx_target = f"#{self.request.htmx.target}"
        else:
            htmx_target = "#content"  # Default target for non-HTMX requests

        return htmx_target

    def get_use_crispy(self):
        # check if attribute was set
        use_crispy_set = self.use_crispy is not None
        # check if crispy_forms is installed
        crispy_installed = "crispy_forms" in settings.INSTALLED_APPS

        if use_crispy_set:
            if self.use_crispy is True and not crispy_installed:
                log.warning("use_crispy is set to True, but crispy_forms is not installed. Forcing to False.")
                return False
            return self.use_crispy
        # user did not set attribute. Return True if crispy_forms is installed else False
        return crispy_installed

    @staticmethod
    def get_url(role, view_cls):
        return path(
            role.url_pattern(view_cls),
            view_cls.as_view(role=role),
            name=f"{view_cls.url_base}-{role.url_name_component}",
        )

    @classonlymethod
    def get_urls(cls, roles=None):
        if roles is None:
            roles = iter(Role)
        return [NominopolitanMixin.get_url(role, cls) for role in roles]

    def reverse(self, role, view, object=None):
        url_name = (
            f"{view.namespace}:{view.url_base}-{role.url_name_component}"
            if view.namespace
            else f"{view.url_base}-{role.url_name_component}"
        )
        url_kwarg = view.lookup_url_kwarg or view.lookup_field

        match role:
            case Role.LIST | Role.CREATE:
                return reverse(url_name)
            case _:
                if object is None:
                    raise ValueError("Object required for detail, update, and delete URLs")
                return reverse(
                    url_name,
                    kwargs={url_kwarg: getattr(object, view.lookup_field)},
                )

    def maybe_reverse(self, view, object=None):
        try:
            return self.reverse(view, object)
        except NoReverseMatch:
            return None
    
    def get_form_class(self):
        """
        Override get_form_classto remove any non-editable fields 
        where a form_class was not specified. This is because the form class gets
        constructed from model_forms.modelform_factory(self.model, fields=self.fields)
        """

        # if fields were specified, but form_class was not, remove non-editable fields
        if self.fields and not self.form_class:
            non_editable_fields = [
                    field.name for field in self.model._meta.fields 
                    if not field.editable
                ]
            self.fields = [field for field in self.fields if field not in non_editable_fields]

        # if create_form_class parameter was specified, use it
        if self.create_form_class and self.role is Role.CREATE:
            return self.create_form_class

        return super().get_form_class()

    def get_prefix(self):
        return f"{self.namespace}:{self.url_base}" if self.namespace else self.url_base

    def safe_reverse(self, viewname, kwargs=None):
        """Attempt to reverse a URL, returning None if it fails."""
        try:
            return reverse(viewname, kwargs=kwargs)
        except NoReverseMatch:
            return None

    def get_template_names(self):
        if self.template_name is not None:
            return [self.template_name]

        if self.model is not None and self.template_name_suffix is not None:
            names = [
                f"{self.model._meta.app_label}/"
                f"{self.model._meta.object_name.lower()}"
                f"{self.template_name_suffix}.html",
                f"{self.templates_path}/object{self.template_name_suffix}.html",
            ]
            return names
        msg = (
            "'%s' must either define 'template_name' or 'model' and "
            "'template_name_suffix', or override 'get_template_names()'"
        )
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Override the create_view_url to use our namespaced reverse
        view_name = f"{self.get_prefix()}-{Role.CREATE.value}"
        context["create_view_url"] = self.safe_reverse(view_name)

        if self.object:
            update_view_name = f"{self.get_prefix()}-{Role.UPDATE.value}"
            context["update_view_url"] = self.safe_reverse(update_view_name, kwargs={"pk": self.object.pk})
            delete_view_name = f"{self.get_prefix()}-{Role.DELETE.value}"
            context["delete_view_url"] = self.safe_reverse(delete_view_name, kwargs={"pk": self.object.pk})

        # to be used in partials to update the header title
        context["header_title"] = f"{self.url_base.title()}-{self.role.value.title()}"

        # set base_template_path
        context["base_template_path"] = self.base_template_path

        # set use_crispy for templates
        context["use_crispy"] = self.get_use_crispy()

        # set use_htmx for templates
        context["use_htmx"] = self.get_use_htmx()

        # set use_modal for templates
        context['use_modal'] = self.get_use_modal()

        context["original_target"] = self.get_original_target()

        # for table font sie used in list.html
        context['table_font_size'] = f"{self.get_table_font_size()}rem"


        if self.get_use_htmx():
            context["htmx_target"] = self.get_htmx_target()

        # Add related fields for list view
        if self.role == Role.LIST and hasattr(self, "object_list"):
            context["related_fields"] = {
                field.name: field.related_model._meta.verbose_name
                for field in self.model._meta.fields
                if field.is_relation
            }

        # Add related objects for detail view
        if self.role == Role.DETAIL and hasattr(self, "object"):
            context["related_objects"] = {
                field.name: str(getattr(self.object, field.name))
                for field in self.model._meta.fields
                if field.is_relation and getattr(self.object, field.name)
            }

        return context

    def get_success_url(self):
        # Verify that a model is defined for this view
        # This is required to construct the URL patterns
        assert self.model is not None, (
            "'%s' must define 'model' or override 'get_success_url()'"
            % self.__class__.__name__
        )

        # Construct the list URL name, using namespace if provided
        # Example: "sample:author-list" or just "author-list"
        url_name = (
            f"{self.namespace}:{self.url_base}-list"
            if self.namespace
            else f"{self.url_base}-list"
        )

        # Different behavior based on the role
        if self.role in (Role.DELETE, Role.UPDATE, Role.CREATE):
            # After deletion, go to the list view
            success_url = reverse(url_name)
        else:
            # For create/update, construct detail URL
            # Example: "sample:author-detail" or "author-detail"
            detail_url = (
                f"{self.namespace}:{self.url_base}-detail"
                if self.namespace
                else f"{self.url_base}-detail"
            )
            # Reverse the detail URL with the object's primary key
            success_url = reverse(detail_url, kwargs={"pk": self.object.pk})

        return success_url

    def render_to_response(self, context={}):
        """Handle both HTMX and regular requests"""
        template_names = self.get_template_names()
        template_name = template_names[0] if self.template_name else template_names[1]

        if self.request.htmx:
            # Store original target when first receiving list view
            if self.role == Role.LIST:
                self.request.session[self.get_session_key()] = f"#{self.request.htmx.target}"
                context["original_target"] = self.get_original_target()
                context['table_font_size'] = f"{self.get_table_font_size()}rem"

            response = render(
                request=self.request,
                template_name=f"{template_name}#content",
                context=context,
            )
            # Add a HX-Trigger header to refresh the target element
            response['HX-Trigger'] = self.get_hx_trigger()
            return response
        else:
            return TemplateResponse(
                request=self.request, template=template_name, context=context
            )
