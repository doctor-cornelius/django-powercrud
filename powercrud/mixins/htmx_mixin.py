"""
This module provides mixins for Django views that enhance CRUD operations with HTMX support,
filtering capabilities, and modal interactions.

Key Components:
- HTMXFilterSetMixin: Adds HTMX attributes to filter forms for dynamic updates
- PowerCRUDMixin: Main mixin that provides CRUD view enhancements with HTMX and modal support
"""


from django.shortcuts import render
from django.template.response import TemplateResponse

import json
import logging
log = logging.getLogger("powercrud")

from neapolitan.views import Role


class HtmxMixin:
    """
    Provides htmx (including modal) and other styling functionality for powercrud views.
    """
    def get_framework_styles(self):
        """
        Get framework-specific styles. Override this method and add 
        the new framework name as a key to the returned dictionary.
        
        Returns:
            dict: Framework-specific style configurations
        """

        return {
            'bootstrap5': {
                # base class for all buttons
                'base': 'btn ',
                # attributes for filter form fields
                'filter_attrs': {
                    'text': {'class': 'form-control form-control-sm small py-1'},
                    'select': {'class': 'form-select form-select-sm small py-1'},
                    'multiselect': {
                        'class': 'form-select form-select-sm small', 
                        'size': '5',
                        'style': 'min-height: 8rem; padding: 0.25rem;'
                    },
                    'date': {'class': 'form-control form-control-sm small py-1', 'type': 'date'},
                    'number': {'class': 'form-control form-control-sm small py-1', 'step': 'any'},
                    'time': {'class': 'form-control form-control-sm small py-1', 'type': 'time'},
                    'default': {'class': 'form-control form-control-sm small py-1'},
                },
                # set colours for the action buttons
                'actions': {
                    'View': 'btn-info',
                    'Edit': 'btn-primary',
                    'Delete': 'btn-danger'
                },
                # default colour for extra action buttons
                'extra_default': 'btn-primary',
                # modal class attributes
                'modal_attrs': f'data-bs-toggle="modal" data-bs-target="{self.get_modal_id()}"',
            },
            'daisyUI': {
                # base class for all buttons
                'base': 'btn ',
                # attributes for filter form fields
                'filter_attrs': {
                    'text': {'class': 'input input-bordered input-sm w-full text-xs h-10 min-h-10'},
                    'select': {'class': 'select select-bordered select-sm w-full text-xs h-10 min-h-10'},
                    'multiselect': {
                        'class': 'select select-bordered select-sm w-full text-xs', 
                        'size': '5',
                        'style': 'min-height: 8rem; max-height: 8rem; overflow-y: auto;'
                    },
                    'date': {'class': 'input input-bordered input-sm w-full text-xs h-10 min-h-10', 'type': 'date'},
                    'number': {'class': 'input input-bordered input-sm w-full text-xs h-10 min-h-10', 'step': 'any'},
                    'time': {'class': 'input input-bordered input-sm w-full text-xs h-10 min-h-10', 'type': 'time'},
                    'default': {'class': 'input input-bordered input-sm w-full text-xs h-10 min-h-10'},
                },
                # set colours for the action buttons
                'actions': {
                    'View': 'btn-info',
                    'Edit': 'btn-primary',
                    'Delete': 'btn-error'
                },
                # default colour for extra action buttons
                'extra_default': 'btn-primary',
                # modal class attributes
                'modal_attrs': f'onclick="{self.get_modal_id()[1:]}.showModal()"', 
            },
        }

    def get_original_target(self):
        """
        Retrieve the original HTMX target from the session.

        This method is called in get_context_data() to provide the original target
        in the context for templates.

        Returns:
            str or None: The original HTMX target or None if not set
        """
        return self.default_htmx_target

    def get_use_htmx(self):
        """
        Determine if HTMX should be used.

        This method is called in multiple places, including get_context_data(),
        get_htmx_target(), and get_use_modal(), to check if HTMX functionality
        should be enabled.

        Returns:
            bool: True if HTMX should be used, False otherwise
        """
        return self.use_htmx is True

    def get_use_modal(self):
        """
        Determine if modal functionality should be used.

        This method is called in get_context_data() to set the 'use_modal' context
        variable for templates. It requires HTMX to be enabled.

        Returns:
            bool: True if modal should be used and HTMX is enabled, False otherwise
        """
        result = self.use_modal is True and self.get_use_htmx()
        return result

    def get_modal_id(self):
        """
        Get the ID for the modal element.

        This method is called in get_framework_styles() to set the modal attributes

        Returns:
            str: The modal ID with a '#' prefix
        """
        modal_id = self.modal_id or 'powercrudBaseModal'
        return f'#{modal_id}'

    def get_modal_target(self):
        """
        Get the target element ID for the modal content.

        This method is called in get_htmx_target() when use_modal is True to
        determine where to render the modal content.

        Returns:
            str: The modal target ID with a '#' prefix
        """
        modal_target = self.modal_target or 'powercrudModalContent'
        return f'#{modal_target}'

    def get_hx_trigger(self):
        """
        Get the HX-Trigger value for HTMX responses.
        
        This method is called in render_to_response() to set the HX-Trigger header
        for HTMX responses. It handles string, numeric, and dictionary values for
        the hx_trigger attribute.
        
        Returns:
            str or None: The HX-Trigger value as a JSON string, or None if not applicable
        """
        if not self.get_use_htmx() or not self.hx_trigger:
            return None

        if isinstance(self.hx_trigger, (str, int, float)):
            # Convert simple triggers to JSON format
            # 'messagesChanged' becomes '{"messagesChanged":true}'
            return json.dumps({str(self.hx_trigger): True})
        elif isinstance(self.hx_trigger, dict):
            # Validate all keys are strings
            if not all(isinstance(k, str) for k in self.hx_trigger.keys()):
                raise TypeError("HX-Trigger dict keys must be strings")
            return json.dumps(self.hx_trigger)
        else:
            raise TypeError("hx_trigger must be either a string or dict with string keys")

    def get_htmx_target(self):
        """
        Determine the HTMX target for rendering responses.

        This method is called in get_context_data() to set the htmx_target context
        variable for templates. It handles different scenarios based on whether
        HTMX and modal functionality are enabled.

        Returns:
            str or None: The HTMX target as a string with '#' prefix, or None if not applicable
        """
        # only if using htmx
        if not self.get_use_htmx():
            htmx_target = None
        elif self.use_modal:
            htmx_target = self.get_modal_target()
        elif hasattr(self.request, 'htmx') and self.request.htmx.target:
            # return the target of the original list request
            htmx_target = self.get_original_target()
        else:
            htmx_target = self.default_htmx_target  # Default target for htmx requests

        return htmx_target

    def _prepare_htmx_response(self, response, context=None, form_has_errors=False):
        """
        Prepare an HTMX response with appropriate triggers and headers.
        """
        # Handle modal display for forms with errors
        if form_has_errors and self.get_use_modal():
            # For daisyUI, we need to trigger the showModal() method
            modal_id = self.get_modal_id()[1:]  # Remove the # prefix

            # Create or update HX-Trigger header
            trigger_data = {"showModal": modal_id, "formSubmitError": True}

            # If there's an existing HX-Trigger, merge with it
            existing_trigger = self.get_hx_trigger()
            if existing_trigger:
                # Since get_hx_trigger always returns a JSON string, we can parse it directly
                existing_data = json.loads(existing_trigger)
                trigger_data.update(existing_data)

            response['HX-Trigger'] = json.dumps(trigger_data)

            # Make sure the response targets the modal content
            if self.get_modal_target():
                response['HX-Retarget'] = self.get_modal_target()

        # For successful form submissions
        elif context and context.get('success') is True:
            # Create success trigger
            trigger_data = {
                "formSubmitSuccess": True, 
                "modalFormSuccess": True,
                "refreshList": True,
                "refreshUrl": self.request.path
            }

            # If there's an existing HX-Trigger, merge with it
            existing_trigger = self.get_hx_trigger()
            if existing_trigger:
                existing_data = json.loads(existing_trigger)
                trigger_data.update(existing_data)

            response['HX-Trigger'] = json.dumps(trigger_data)

        # For other cases, just use the existing HX-Trigger if any
        elif self.get_hx_trigger():
            response['HX-Trigger'] = self.get_hx_trigger()

        return response

    def render_to_response(self, context={}):
        """
        Render the response, handling both HTMX and regular requests.
        Ensure modal context is maintained when forms have errors.
        """
        template_names = self.get_template_names()

        # Try the first template (app-specific), fall back to second (generic)
        from django.template.loader import get_template
        from django.template.exceptions import TemplateDoesNotExist

        try:
            # try to use overriden template if it exists
            template_name = template_names[0]
            # this call check if valid template
            template = get_template(template_name)
        except TemplateDoesNotExist:
            template_name = template_names[1]
            template = get_template(template_name)
        except Exception as e:
            log.error(f"Unexpected error checking template {template_name}: {str(e)}")
            template_name = template_names[1]

        # Check if this is a form with errors being redisplayed
        form_has_errors = hasattr(self, 'form_has_errors') and self.form_has_errors

        if self.request.htmx:
            if self.request.headers.get('X-Redisplay-Object-List'):
                # Use object_list template
                object_list_template = f"{self.templates_path}/object_list.html"

                if self.request.headers.get('X-Filter-Sort-Request'):
                    template_name = f"{object_list_template}#filtered_results"
                else:
                    template_name = f"{object_list_template}#pcrud_content"
            else:
                # Use whatever template was determined normally
                if self.request.headers.get('X-Filter-Sort-Request'):
                    template_name = f"{template_name}#filtered_results"
                else:
                    template_name = f"{template_name}#pcrud_content"

            log.debug(f"render_to_response: template_name = {template_name}")

            response = render(
                request=self.request,
                template_name=f"{template_name}",
                context=context,
            )

            # Only set HX-Push-Url for GET requests and when role is LIST
            if self.request.method == "GET" and self.role == Role.LIST:
                clean_params = {}
                for k in self.request.GET:
                    values = self.request.GET.getlist(k)
                    if values and values[-1]:  # Only non-empty
                        clean_params[k] = values[-1]
                if clean_params:
                    from urllib.parse import urlencode
                    canonical_query = urlencode(clean_params)
                    canonical_url = f"{self.request.path}?{canonical_query}"
                else:
                    canonical_url = self.request.path
                response['HX-Push-Url'] = canonical_url

            # Add HX-Trigger for modal if form has errors and modal should be used
            if form_has_errors and self.get_use_modal():
                # Single, simplified trigger
                response['HX-Trigger'] = json.dumps({"formError": True})

                # Make sure the response targets the modal content
                response['HX-Retarget'] = self.get_modal_target()

                # Clear the flag after handling
                self.form_has_errors = False
            elif self.get_hx_trigger():
                response['HX-Trigger'] = self.get_hx_trigger()

            return response
        else:
            return TemplateResponse(
                request=self.request, template=template_name, context=context
            )
