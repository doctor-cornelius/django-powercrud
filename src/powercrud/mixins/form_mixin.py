import json

from django import forms
from django.conf import settings
from django.forms import models as form_models
from django.db import models as db_models
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import render
from django.urls import reverse

from urllib.parse import urlencode

from crispy_forms.helper import FormHelper
from neapolitan.views import Role
from powercrud.logging import get_logger
from .config_mixin import resolve_config

log = get_logger(__name__)


class FormMixin:
    """
    Provides form handling and Crispy Forms integration for powercrud views.
    """

    def get_use_crispy(self):
        """
        Determine if crispy forms should be used.

        This method is called in get_context_data() to set the 'use_crispy' context
        variable for templates. It checks if the crispy_forms app is installed and
        if the use_crispy attribute is explicitly set.

        Returns:
            bool: True if crispy forms should be used, False otherwise

        Note:
            - If use_crispy is explicitly set to True but crispy_forms is not installed,
              it logs a warning and returns False.
            - If use_crispy is not set, it returns True if crispy_forms is installed,
              False otherwise.
        """
        return bool(resolve_config(self).use_crispy_enabled)

    def _apply_crispy_helper(self, form_class):
        """Helper method to apply crispy form settings to a form class."""
        if not self.get_use_crispy():
            # Apply dropdown sorting even if not using crispy
            self._apply_dropdown_sorting(form_class)
            return form_class

        # Create a new instance to check if it has a helper
        _temp_form = form_class()
        has_helper = hasattr(_temp_form, 'helper')

        # Capture the current FormMixin instance
        mixin_instance = self

        if not has_helper:
            old_init = form_class.__init__

            def new_init(self, *args, **kwargs):
                old_init(self, *args, **kwargs)
                self.helper = FormHelper()
                self.helper.form_tag = False
                self.helper.disable_csrf = True
            form_class.__init__ = new_init
        else:
            old_init = form_class.__init__

            def new_init(self, *args, **kwargs):
                old_init(self, *args, **kwargs)

                # Check if form_tag has been explicitly set to True
                if self.helper.form_tag is True:
                    self.helper.form_tag = False

                # Check if disable_csrf has been explicitly set to False
                if self.helper.disable_csrf is False:
                    self.helper.disable_csrf = True
            form_class.__init__ = new_init

        # Apply dropdown sorting
        self._apply_dropdown_sorting(form_class)

        return form_class

    def _apply_dropdown_sorting(self, form_class):
        """Apply dropdown sorting to form fields."""
        sort_options = resolve_config(self).dropdown_sort_options
        for field_name, sort_field in sort_options.items():
            if field_name in form_class.base_fields:
                form_field = form_class.base_fields[field_name]
                if hasattr(form_field, 'queryset') and form_field.queryset is not None:
                    # sort_field can be "name" or "-name" - Django's order_by handles both
                    form_field.queryset = form_field.queryset.order_by(sort_field)

    def get_form_class(self):
        """Override get_form_class to use form_fields for form generation."""

        # Use explicitly defined form class if provided
        cfg = resolve_config(self)
        if cfg.form_class is not None:
            return self._apply_crispy_helper(cfg.form_class)

        # Generate a default form class using form_fields
        if self.model is not None and cfg.form_fields:
            # Configure HTML5 input widgets for date/time fields
            widgets = {}
            for field in self.model._meta.get_fields():
                if field.name not in cfg.form_fields:
                    continue
                if isinstance(field, db_models.DateField):
                    widgets[field.name] = forms.DateInput(
                        attrs={'type': 'date', 'class': 'form-control'}
                    )
                elif isinstance(field, db_models.DateTimeField):
                    widgets[field.name] = forms.DateTimeInput(
                        attrs={'type': 'datetime-local', 'class': 'form-control'}
                    )
                elif isinstance(field, db_models.TimeField):
                    widgets[field.name] = forms.TimeInput(
                        attrs={'type': 'time', 'class': 'form-control'}
                    )

            # Create the form class with our configured widgets
            form_class = form_models.modelform_factory(
                self.model,
                fields=cfg.form_fields,
                widgets=widgets
            )

            # Apply dropdown sorting to form fields
            sort_options = cfg.dropdown_sort_options
            for field_name, sort_field in sort_options.items():
                if field_name in cfg.form_fields:
                    model_field = self.model._meta.get_field(field_name)
                    if hasattr(model_field, 'related_model') and model_field.related_model:
                        form_field = form_class.base_fields[field_name]
                        form_field.queryset = model_field.related_model.objects.order_by(sort_field)

            # Apply crispy forms if enabled
            if self.get_use_crispy():
                old_init = form_class.__init__

                def new_init(self, *args, **kwargs):
                    old_init(self, *args, **kwargs)
                    self.helper = FormHelper()
                    self.helper.form_tag = False
                    self.helper.disable_csrf = True

                form_class.__init__ = new_init

            return form_class

        msg = (
            "'%s' must either define 'form_class' or both 'model' and "
            "'form_fields', or override 'get_form_class()'"
        )
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_inline_form_kwargs(self, *, instance, data=None, files=None):
        """
        Build kwargs for an inline form instance so inline endpoints can reuse the
        standard form pipeline without duplicating logic.
        """
        kwargs = {'instance': instance}
        if data is not None:
            kwargs['data'] = data
        if files is not None:
            kwargs['files'] = files
        return kwargs

    def build_inline_form(self, *, instance, data=None, files=None):
        """
        Construct a ModelForm for inline editing using the same configuration as
        regular edit forms.
        """
        form_class = self.get_form_class()
        form_kwargs = self.get_inline_form_kwargs(instance=instance, data=data, files=files)
        return form_class(**form_kwargs)

    def show_form(self, request, *args, **kwargs):
        """Override to check for conflicts before showing edit form"""
        # Only check conflicts for UPDATE operations (not CREATE)
        pk = None
        current_object = None
        if self.role == Role.UPDATE:
            try:
                current_object = self.get_object()
                pk = current_object.pk
            except Exception:
                pk = None

        if (
            self.role == Role.UPDATE and 
            self.get_conflict_checking_enabled() and 
            pk is not None and 
            self._check_for_conflicts(selected_ids=[pk])
        ):
            if current_object is None:
                current_object = self.get_object()
            self.object = current_object

            # Get filter params (like sort selection does)
            filter_params = request.GET.copy()
            if 'sort' in filter_params:
                filter_params.pop('sort')  
            if 'page' in filter_params:
                filter_params.pop('page')

            # Return conflict response
            context = self.get_context_data(
                conflict_detected=True,
                conflict_message=(
                    f"Cannot update - bulk operation in progress on "
                    f"{self.model._meta.verbose_name_plural}. Please try again later."
                ),
                filter_params=filter_params.urlencode() if filter_params else "",
            )
            return self.render_to_response(context)
        
        # No conflict, proceed normally
        return super().show_form(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Handle form validation success with HTMX support.
        
        This method saves the form and then handles the response differently based on
        whether it's an HTMX request or not:
        
        For HTMX requests:
        1. Temporarily changes the role to LIST to access list view functionality
        2. Sets the template to the filtered_results partial from object_list.html
        3. Uses the existing list() method to handle pagination and filtering
        4. Adds HTMX headers to:
        - Close the modal (via formSuccess trigger)
        - Target the filtered_results div (via HX-Retarget)
        
        For non-HTMX requests:
        - Redirects to the success URL (typically the list view)
        
        This approach ensures consistent behavior with the standard list view,
        including proper pagination and filtering, while avoiding code duplication.
        
        Args:
            form: The validated form instance
            
        Returns:
            HttpResponse: Either a rendered list view or a redirect
        """
        if (
            self.role == Role.UPDATE
            and self.get_conflict_checking_enabled()
        ):
            pk = getattr(form.instance, "pk", None) or self.kwargs.get(getattr(self, "pk_url_kwarg", "pk"))
            if pk and self._check_for_conflicts(selected_ids=[pk]):
                self.object = form.instance
                return self._render_conflict_response(self.request, pk, "update")

        self.object = form.save()

        # If this is an HTMX request, handle it specially
        if hasattr(self, 'request') and getattr(self.request, 'htmx', False):
            # unpack hidden filter parameters
            filter_params = QueryDict('', mutable=True)
            # prefix is set in object_form.html
            filter_prefix = '_powercrud_filter_'

            for k, v in self.request.POST.lists():
                if k.startswith(filter_prefix):
                    real_key = k[len(filter_prefix):]
                    for value in v:
                        filter_params.appendlist(real_key, value)

            # Build canonical list URL with current filter/sort params
            clean_params = {}
            for k, v in filter_params.lists():
                # filter out keys with no values
                if v:
                    clean_params[k] = v[-1]

            # determine the canonical url that includes the filter parameters
            if self.namespace:
                list_url_name = f"{self.namespace}:{self.url_base}-list"
            else:
                list_url_name = f"{self.url_base}-list"
            list_path = reverse(list_url_name)

            if clean_params:
                canonical_query = urlencode(clean_params)
                canonical_url = f"{list_path}?{canonical_query}"
            else:
                canonical_url = list_path

            # Patch self.request.GET
            original_get = self.request.GET
            self.request.GET = filter_params
            # Temporarily change the role to LIST
            original_role = self.role
            self.role = Role.LIST
            # Use the list method to handle pagination and filtering
            response = self.list(self.request)
            # Restore original GET
            self.request.GET = original_get
            
            response["HX-Trigger"] = json.dumps({"formSuccess": True})
            response["HX-Retarget"] = f"{self.get_original_target()}"
            response["HX-Push-Url"] = canonical_url
            return response
        # For non-HTMX requests, use the default redirect
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """
        Handle form validation errors, ensuring proper display in modals.
        
        This method handles form validation errors differently based on whether
        it's an HTMX request with modals enabled:
        
        For HTMX requests with modals:
        1. Stores the form with errors
        2. Sets a flag to indicate the modal should stay open
        3. Ensures the correct form template is used (not object_list)
        4. Adds HTMX headers to:
        - Keep the modal open (via formError and showModal triggers)
        - Target the modal content (via HX-Retarget)
        
        For other requests:
        - Uses the default form_invalid behavior
        
        Args:
            form: The form with validation errors
            
        Returns:
            HttpResponse: The rendered form with error messages
        """
        # Store the form with errors
        self.object_form = form

        # If using modals, set a flag to indicate we need to show the modal again
        if self.get_use_modal():
            self.form_has_errors = True

        # For HTMX requests with modals, ensure we use the form template
        if hasattr(self, 'request') and getattr(self.request, 'htmx', False) and self.get_use_modal():
            # Ensure we're using the form template, not object_list
            original_template_name = getattr(self, 'template_name', None)

            # Set template to the form partial
            if self.object:  # Update form
                self.template_name = f"{self.templates_path}/object_form.html#pcrud_content"
            else:  # Create form
                self.template_name = f"{self.templates_path}/object_form.html#pcrud_content"

            # Render the response with the form template
            context = self.get_context_data(form=form)
            response = render(
                request=self.request,
                template_name=self.template_name,
                context=context,
            )

            # Add HTMX headers to keep the modal open
            modal_id = self.get_modal_id()[1:]  # Remove the # prefix
            response["HX-Trigger"] = json.dumps({"formError": True, "showModal": modal_id})
            response["HX-Retarget"] = self.get_modal_target()

            return response

        # For non-HTMX requests or without modals, use the default behavior
        return super().form_invalid(form)
