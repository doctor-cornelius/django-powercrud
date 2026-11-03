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
from neapolitan.views import Role
from powercrud.query_params import build_navigation_query_string
from powercrud.template_packs import (
    ServerAdapterContext,
    get_selected_template_pack,
    get_template_pack_server_adapter,
)
from .config_mixin import get_template_name, resolve_config

def _template_candidates(template_names):
    """Return a flat list for one or many ordered template candidates."""
    if isinstance(template_names, str):
        return [template_names]
    return list(template_names)


def _with_template_fragment(template_names, fragment):
    """Append a fragment to candidates that do not already specify one."""
    return [
        template_name
        if "#" in template_name
        else f"{template_name}#{fragment}"
        for template_name in _template_candidates(template_names)
    ]


class HtmxMixin:
    """
    Provides htmx (including modal) and other styling functionality for powercrud views.
    """

    def get_framework_styles(self):
        """
        Get selected-pack presentation through the public server adapter.

        Returns:
            dict: Framework-specific style configurations
        """
        context = ServerAdapterContext(
            modal_id=self.get_modal_id(),
            modal_target_id=self.get_modal_target(),
            use_htmx=self.get_use_htmx(),
            use_modal=self.get_use_modal(),
        )
        presentation = get_template_pack_server_adapter().get_presentation(context)
        actions = presentation.actions
        return {
            get_selected_template_pack().identity: {
                "base": actions.base_classes,
                "actions": {
                    "View": actions.role_classes.get("view", ""),
                    "Edit": actions.role_classes.get("edit", ""),
                    "Delete": actions.role_classes.get("delete", ""),
                },
                "action_group_item": actions.group_item_classes,
                "extra_default": actions.extra_default_classes,
                "list_cell_link_class": actions.list_cell_link_classes,
                "modal_attrs": 'data-powercrud-modal-trigger="true"',
            }
        }

    def get_original_target(self):
        """
        Retrieve the original HTMX target from the session.

        This method is called in get_context_data() to provide the original target
        in the context for templates.

        Returns:
            str or None: The original HTMX target or None if not set
        """
        return resolve_config(self).default_htmx_target

    def get_use_htmx(self):
        """
        Determine if HTMX should be used.

        This method is called in multiple places, including get_context_data(),
        get_htmx_target(), and get_use_modal(), to check if HTMX functionality
        should be enabled.

        Returns:
            bool: True if HTMX should be used, False otherwise
        """
        return bool(resolve_config(self).use_htmx_enabled)

    def get_use_modal(self):
        """
        Determine if modal functionality should be used.

        This method is called in get_context_data() to set the 'use_modal' context
        variable for templates. It requires HTMX to be enabled.

        Returns:
            bool: True if modal should be used and HTMX is enabled, False otherwise
        """
        return bool(resolve_config(self).use_modal_enabled)

    def get_modal_id(self):
        """
        Get the ID for the modal element.

        This method is called in get_framework_styles() to set the modal attributes

        Returns:
            str: The modal ID with a '#' prefix
        """
        return f"#{resolve_config(self).modal_id_resolved}"

    def get_modal_target(self):
        """
        Get the target element ID for the modal content.

        This method is called in get_htmx_target() when use_modal is True to
        determine where to render the modal content.

        Returns:
            str: The modal target ID with a '#' prefix
        """
        return f"#{resolve_config(self).modal_target_resolved}"

    def get_modal_classes(self) -> str:
        """
        Return CSS classes for the PowerCRUD modal dialog element.
        """
        return str(resolve_config(self).modal_classes_resolved)

    def get_modal_box_classes(self) -> str:
        """
        Return CSS classes for the PowerCRUD modal box element.
        """
        return str(resolve_config(self).modal_box_classes_resolved)

    def get_modal_body_classes(self) -> str:
        """
        Return CSS classes for the PowerCRUD modal body wrapper.
        """
        return str(resolve_config(self).modal_body_classes_resolved)

    def get_bulk_modal_box_classes(self) -> str:
        """
        Return CSS classes for the modal box used by the built-in bulk edit action.
        """
        return str(resolve_config(self).bulk_modal_box_classes_resolved)

    def get_modal_presentation(self) -> dict:
        """Return the normalized portable presentation for ordinary modals."""
        return dict(resolve_config(self).modal_presentation_resolved)

    def get_bulk_modal_presentation(self) -> dict:
        """Return the normalized portable presentation for bulk-edit modals."""
        return dict(resolve_config(self).bulk_modal_presentation_resolved)

    def get_modal_uses_legacy_classes(self) -> bool:
        """Return whether deprecated modal class settings control this view."""
        return bool(resolve_config(self).modal_uses_legacy_classes)

    def get_modal_context(self) -> dict[str, object]:
        """
        Return template context values needed to render and target the modal shell.
        """
        return {
            "modal_id": self.get_modal_id()[1:],
            "modal_target": self.get_modal_target()[1:],
            "modal_classes": self.get_modal_classes(),
            "modal_box_classes": self.get_modal_box_classes(),
            "modal_body_classes": self.get_modal_body_classes(),
            "bulk_modal_box_classes": self.get_bulk_modal_box_classes(),
            "modal_presentation": self.get_modal_presentation(),
            "bulk_modal_presentation": self.get_bulk_modal_presentation(),
            "modal_presentation_attrs": resolve_config(self).modal_presentation_attrs,
            "bulk_modal_presentation_attrs": resolve_config(
                self
            ).bulk_modal_presentation_attrs,
            "modal_uses_legacy_classes": resolve_config(
                self
            ).modal_uses_legacy_classes,
        }

    def get_hx_trigger(self):
        """
        Get the HX-Trigger value for HTMX responses.

        This method is called in render_to_response() to set the HX-Trigger header
        for HTMX responses. It handles string, numeric, and dictionary values for
        the hx_trigger attribute.

        Returns:
            str or None: The HX-Trigger value as a JSON string, or None if not applicable
        """
        cfg = resolve_config(self)
        if not self.get_use_htmx() or not cfg.hx_trigger:
            return None

        if isinstance(cfg.hx_trigger, (str, int, float)):
            # Convert simple triggers to JSON format
            # 'messagesChanged' becomes '{"messagesChanged":true}'
            return json.dumps({str(cfg.hx_trigger): True})
        elif isinstance(cfg.hx_trigger, dict):
            # Validate all keys are strings
            if not all(isinstance(k, str) for k in cfg.hx_trigger.keys()):
                raise TypeError("HX-Trigger dict keys must be strings")
            return json.dumps(cfg.hx_trigger)
        else:
            raise TypeError(
                "hx_trigger must be either a string or dict with string keys"
            )

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
        elif resolve_config(self).use_modal_enabled:
            htmx_target = self.get_modal_target()
        elif hasattr(self.request, "htmx") and self.request.htmx.target:
            # return the target of the original list request
            htmx_target = self.get_original_target()
        else:
            htmx_target = resolve_config(
                self
            ).default_htmx_target  # Default target for htmx requests

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

            response["HX-Trigger"] = json.dumps(trigger_data)

            # Make sure the response targets the modal content
            if self.get_modal_target():
                response["HX-Retarget"] = self.get_modal_target()

        # For successful form submissions
        elif context and context.get("success") is True:
            # Create success trigger
            trigger_data = {
                "formSubmitSuccess": True,
                "modalFormSuccess": True,
                "refreshList": True,
                "refreshUrl": self.request.path,
            }

            # If there's an existing HX-Trigger, merge with it
            existing_trigger = self.get_hx_trigger()
            if existing_trigger:
                existing_data = json.loads(existing_trigger)
                trigger_data.update(existing_data)

            response["HX-Trigger"] = json.dumps(trigger_data)

        # For other cases, just use the existing HX-Trigger if any
        elif self.get_hx_trigger():
            response["HX-Trigger"] = self.get_hx_trigger()

        return response

    def render_to_response(self, context={}):
        """
        Render the response, handling both HTMX and regular requests.
        Ensure modal context is maintained when forms have errors.
        """
        # Check if this is a form with errors being redisplayed
        form_has_errors = hasattr(self, "form_has_errors") and self.form_has_errors

        if self.request.htmx:
            if self.request.headers.get("X-Redisplay-Object-List"):
                template_names = get_template_name(
                    resolve_config(self), "object_list.html"
                )
            else:
                template_names = self.get_template_names()

            fragment = (
                "filtered_results"
                if self.request.headers.get("X-Filter-Sort-Request")
                else "pcrud_content"
            )
            template_names = _with_template_fragment(template_names, fragment)

            response = render(
                request=self.request,
                template_name=template_names,
                context=context,
            )

            # Only set HX-Push-Url for GET requests and when role is LIST
            if self.request.method == "GET" and self.role == Role.LIST:
                canonical_query = build_navigation_query_string(self.request.GET)
                if canonical_query:
                    canonical_url = f"{self.request.path}?{canonical_query}"
                else:
                    canonical_url = self.request.path
                response["HX-Push-Url"] = canonical_url

            # Add HX-Trigger for modal if form has errors and modal should be used
            if form_has_errors and self.get_use_modal():
                # Single, simplified trigger
                response["HX-Trigger"] = json.dumps({"formError": True})

                # Make sure the response targets the modal content
                response["HX-Retarget"] = self.get_modal_target()

                # Clear the flag after handling
                self.form_has_errors = False
            elif self.get_hx_trigger():
                response["HX-Trigger"] = self.get_hx_trigger()

            return response
        else:
            return TemplateResponse(
                request=self.request,
                template=_template_candidates(self.get_template_names()),
                context=context,
            )
