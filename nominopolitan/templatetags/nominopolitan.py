"""
This module contains custom template tags for the Nominopolitan package.

It includes functions for generating action links, displaying object details,
and rendering object lists with customized formatting.

Key components:
- action_links: Generates HTML for action buttons (View, Edit, Delete, etc.)
- object_detail: Renders details of an object, including fields and properties
- object_list: Creates a list view of objects with customized field display
- get_proper_elided_page_range: Generates a properly elided page range for pagination

The module adapts to different CSS frameworks and supports HTMX and modal functionality.
"""

from datetime import date, datetime  # Import both date and datetime classes
from typing import Any, Dict, List, Optional, Tuple
import re  # Add this import at the top with other imports

from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import FieldDoesNotExist
from django.conf import settings
from django.db import models 

import logging
log = logging.getLogger("nominopolitan")

register = template.Library()

def action_links(view: Any, object: Any) -> str:
    """
    Generate HTML for action links (buttons) for a given object.

    Args:
        view: The view instance
        object: The object for which actions are being generated

    Returns:
        str: HTML string of action buttons
    """
    framework: str = getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'daisyui')
    styles: Dict[str, Any] = view.get_framework_styles()[framework]
    action_button_classes = view.get_action_button_classes()

    prefix: str = view.get_prefix()
    use_htmx: bool = view.get_use_htmx()
    use_modal: bool = view.get_use_modal()

    default_target: str = view.get_htmx_target() # this will be prepended with a #

    # Standard actions with framework-specific button classes
    actions: List[Tuple[str, str, str, str, bool, str]] = [
        (url, name, styles['actions'][name], default_target, False, use_modal, styles["modal_attrs"])
        for url, name in [
            (view.safe_reverse(f"{prefix}-detail", kwargs={"pk": object.pk}), "View"),
            (view.safe_reverse(f"{prefix}-update", kwargs={"pk": object.pk}), "Edit"),
            (view.safe_reverse(f"{prefix}-delete", kwargs={"pk": object.pk}), "Delete"),
        ]
        if url is not None
    ]

    # Add extra actions if defined
    extra_actions: List[Dict[str, Any]] = getattr(view, "extra_actions", [])
    for action in extra_actions:
        url: Optional[str] = view.safe_reverse(
            action["url_name"],
            kwargs={"pk": object.pk} if action.get("needs_pk", True) else None,
        )
        # log.debug(f"Extra action: {action}, url: {url}")
        if url is not None:
            htmx_target: str = action.get("htmx_target", default_target)
            if htmx_target and not htmx_target.startswith("#"):
                htmx_target = f"#{htmx_target}"
            button_class: str = action.get("button_class", styles['extra_default'])
            
            display_modal = action.get("display_modal", use_modal)
            show_modal: bool = display_modal if use_modal else False
            modal_attrs: str = styles["modal_attrs"] if show_modal else " "
            
            actions.append((
                url, 
                action["text"], 
                button_class, 
                htmx_target, 
                action.get("hx_post", False),
                show_modal,
                modal_attrs
            ))

    # set up links for all actions (regular and extra)
    # note for future - could simplify by just conditionally adding hx-disable if not use_htmx
    links: List[str] = [
        f"<div class='join'>" +
        " ".join([
            f"<a href='{url}' class='{styles['base']} join-item {button_class} {action_button_classes}' "
            + (f"hx-{'post' if hx_post else 'get'}='{url}' " if use_htmx else "")
            + (f"hx-target='{target}' " if use_htmx else "")
            + (f"hx-replace-url='true' hx-push-url='true' " if use_htmx and not show_modal else "")
            + (f"{modal_attrs} " if show_modal else "")
            + f">{anchor_text}</a>"
            for url, anchor_text, button_class, target, hx_post, show_modal, modal_attrs in actions
        ]) +
        "</div>"
    ]

    return mark_safe(" ".join(links))


@register.inclusion_tag(f"nominopolitan/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'daisyui')}/partial/detail.html")
def object_detail(object, view):
    """
    Display both fields and properties for an object detail view.

    Args:
        object: The object to display
        view: The view instance

    Returns:
        dict: Context for rendering the detail template
    """
    def iter():
        # Handle regular fields
        for f in view.detail_fields:
            field = object._meta.get_field(f)
            if field.is_relation:
                value = str(getattr(object, f))
            else:
                value = field.value_to_string(object)
            yield (field.verbose_name, value)

        # Handle properties
        for prop in view.detail_properties:
            value = str(getattr(object, prop))
            name = prop.replace('_', ' ').title()
            yield (name, value)

    return {
        "object": iter(),
    }


@register.inclusion_tag(
        f"nominopolitan/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'daisyui')}/partial/list.html", 
        takes_context=True
        )
def object_list(context, objects, view):
    """
    Override default to set value = str()
    instead of value_to_string(). This allows related fields
    to be displayed correctly (not just the id)
    """
    fields = view.fields
    properties = getattr(view, "properties", []) or []

    # Check if bulk edit is enabled
    enable_bulk_edit = hasattr(view, 'get_bulk_edit_enabled') and view.get_bulk_edit_enabled()
    
    # Get currently selected IDs from session if bulk edit is enabled
    request = context.get('request')
    selected_ids = []
    if request and enable_bulk_edit:
        selected_ids = request.session.get('nominopolitan_bulk_selected', [])
        # Convert to strings for comparison
        selected_ids = [str(id) for id in selected_ids]

    # Get selection key suffix if available
    selection_key_suffix = ""
    if enable_bulk_edit and hasattr(view, 'get_bulk_selection_key_suffix'):
        selection_key_suffix = view.get_bulk_selection_key_suffix()

    # Create tuples of (display_name, field_name, is_sortable) for each field
    headers = []
    for f in fields:
        try:
            field = view.model._meta.get_field(f)
            # Handle M2M fields differently
            if hasattr(field, 'remote_field') and field.remote_field and isinstance(field.remote_field, models.ManyToManyRel):
                display_name = field.remote_field.model._meta.verbose_name_plural.title()
            else:
                display_name = field.verbose_name.title() if hasattr(field, 'verbose_name') and field.verbose_name else f.replace('_', ' ').title()
            headers.append((display_name, f, True))  # Regular fields are sortable
        except Exception as e:
            log.warning(f"Error processing field {f}: {str(e)}")
            # Fallback to basic field name formatting
            headers.append((f.replace('_', ' ').title(), f, True))

    # Add properties with proper display names (not sortable)
    for prop in properties:
        # Try to get short_description from property
        prop_obj = getattr(view.model, prop, None)
        if prop_obj and hasattr(prop_obj.fget, 'short_description') and prop_obj.fget.short_description:
            display_name = prop_obj.fget.short_description
        else:
            display_name = prop.replace('_', ' ').title()
        headers.append((display_name, prop, False))  # Properties are not sortable

    TICK_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="green" class="size-4 inline-block"><path fill-rule="evenodd" d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm3.844-8.791a.75.75 0 0 0-1.188-.918l-3.7 4.79-1.649-1.833a.75.75 0 1 0-1.114 1.004l2.25 2.5a.75.75 0 0 0 1.15-.043l4.25-5.5Z" clip-rule="evenodd" /></svg>'
    CROSS_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="crimson" class="size-4 inline-block"><path fill-rule="evenodd" d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm2.78-4.22a.75.75 0 0 1-1.06 0L8 9.06l-1.72 1.72a.75.75 0 1 1-1.06-1.06L6.94 8 5.22 6.28a.75.75 0 0 1 1.06-1.06L8 6.94l1.72-1.72a.75.75 0 1 1 1.06 1.06L9.06 8l1.72 1.72a.75.75 0 0 1 0 1.06Z" clip-rule="evenodd" /></svg>'

    object_list = [
        {
            "object": object,
            "id": str(object.pk),  # Add ID for selection tracking
            "is_selected": str(object.pk) in selected_ids if enable_bulk_edit else False,  # Check if this object is selected
            "fields": [
                (
                    # M2M field
                    ", ".join(str(obj) for obj in getattr(object, f).all()) if object._meta.get_field(f).many_to_many
                    # boolean True
                    else mark_safe(TICK_SVG) if object._meta.get_field(f).get_internal_type() == 'BooleanField' and getattr(object, f) is True
                    # boolean False
                    else mark_safe(CROSS_SVG) if object._meta.get_field(f).get_internal_type() == 'BooleanField' and getattr(object, f) is False
                    # date type
                    else str(getattr(object, f).strftime('%d/%m/%Y')) if object._meta.get_field(f).get_internal_type() == 'DateField' and getattr(object, f) is not None
                    # related field
                    else str(getattr(object, f)) if object._meta.get_field(f).is_relation
                    # any other type gets applied as string
                    else object._meta.get_field(f).value_to_string(object)
                )
                for f in fields
            ]
            # properties
            + [
                # boolean True
                mark_safe(TICK_SVG)
                    if isinstance(getattr(object.__class__, prop), property) and getattr(object, prop) is True
                # boolean False
                else mark_safe(CROSS_SVG)
                    if isinstance(getattr(object.__class__, prop), property) and getattr(object, prop) is False
                # date type
                else str(getattr(object, prop).strftime('%d/%m/%Y'))
                    if isinstance(getattr(object, prop), (date, datetime)) and getattr(object, prop) is not None
                # any other type gets applied as string
                else str(getattr(object, prop))
                for prop in properties
            ],
            "actions": action_links(view, object),
        }
        for object in objects
    ]

    request = context.get('request')
    current_sort = request.GET.get('sort', '') if request else ''
    
    # Get all current filter parameters
    filter_params = request.GET.copy() if request else {}
    if 'sort' in filter_params:
        filter_params.pop('sort')
    if 'page' in filter_params:
        filter_params.pop('page')
    
    use_htmx = context.get('use_htmx', view.get_use_htmx())
    original_target = context.get('original_target', view.get_original_target())
    htmx_target = context.get('htmx_target', view.get_htmx_target())

    return {
        "headers": headers,  # Now contains tuples of (display_name, field_name, is_sortable)
        "object_list": object_list,
        "current_sort": current_sort,
        "filter_params": filter_params.urlencode(),  # Add filter parameters to context
        "use_htmx": use_htmx,
        "original_target": original_target,
        "table_pixel_height_other_page_elements": view.get_table_pixel_height_other_page_elements(),
        "table_max_height": view.get_table_max_height(),
        "table_classes": view.get_table_classes(),
        "htmx_target": htmx_target,
        "request": request,
        # Add bulk edit related context
        "enable_bulk_edit": enable_bulk_edit,
        "selected_count": len(selected_ids) if enable_bulk_edit else 0,
        "model_name": view.model.__name__.lower() if hasattr(view, 'model') else '',
        "selection_key_suffix": selection_key_suffix,
    }

@register.simple_tag
def get_proper_elided_page_range(paginator, number, on_each_side=1, on_ends=1):
    """
    Return a list of page numbers with proper elision for pagination.

    Args:
        paginator: The Django Paginator instance
        number: The current page number
        on_each_side: Number of pages to show on each side of the current page
        on_ends: Number of pages to show at the beginning and end of the range

    Returns:
        list: A list of page numbers and ellipsis characters
    """
    page_range = paginator.get_elided_page_range(
        number=number,
        on_each_side=1,
        on_ends=1
    )
    return page_range

@register.simple_tag
def extra_buttons(view: Any) -> str:
    """
    Generate HTML for extra buttons in the list view header.

    Args:
        view: The view instance

    Returns:
        str: HTML string of extra buttons
    """
    framework: str = getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'daisyui')
    styles: Dict[str, Any] = view.get_framework_styles()[framework]

    use_htmx: bool = view.get_use_htmx()
    use_modal: bool = view.get_use_modal()

    extra_buttons: List[Dict[str, Any]] = getattr(view, "extra_buttons", [])
    extra_button_classes = view.get_extra_button_classes()
    
    buttons: List[str] = []
    for button in extra_buttons:
        display_modal = button.get("display_modal", False) and use_modal
        modal_attrs = ""
        extra_attrs = button.get("extra_attrs", "")
        extra_class_attrs = button.get("extra_class_attrs", "")

        url: Optional[str] = view.safe_reverse(
            button["url_name"],
            kwargs={} if not button.get("needs_pk", False) else None
        )
        if url is not None:
            htmx_attrs = []
            if use_htmx:
                if display_modal:
                    htmx_target = view.get_modal_target()
                    modal_attrs = styles.get("modal_attrs", "")
                else:
                    htmx_target = button.get("htmx_target", "")
                    if htmx_target and not htmx_target.startswith("#"):
                        htmx_target = f"#{htmx_target}"
                
                htmx_attrs.append(f'hx-get="{url}"')
                if htmx_target:
                    htmx_attrs.append(f'hx-target="{htmx_target}"')
                if use_htmx and not display_modal:
                    htmx_attrs.append('hx-replace-url="true"')
                    htmx_attrs.append('hx-push-url="true"')
                
            htmx_attrs_str = " ".join(htmx_attrs)
            
            button_class = button.get("button_class", styles['extra_default'])

            # log.debug(f"extra_attrs: {extra_attrs}, htmx_attrs: {htmx_attrs}, modal_attrs: {modal_attrs}")

            new_button = (
                f'<a href="{url}" '
                f'class="{extra_class_attrs} {styles["base"]} {extra_button_classes} {button_class}" '
                f'{extra_attrs} {htmx_attrs_str} '
                f'{modal_attrs}>'
                f'{button["text"]}</a>'                
            )

            # log.debug(f"new_button: {new_button}")

            buttons.append(
                new_button
            )

    if buttons:
        return mark_safe(" ".join(buttons))
    return ""


@register.simple_tag(takes_context=True)
def get_nominopolitan_session_data(context, key):
    """
    Get a value from the nominopolitan session data for the current model.
    
    Usage in template:
    {% get_nominopolitan_session_data 'original_template' as template_name %}
    """
    request = context.get('request')
    view = context.get('view')
    
    if not request or not view:
        return None
        
    nominopolitan_data = request.session.get('nominopolitan', {})
    model_key = view.get_model_session_key()
    model_data = nominopolitan_data.get(model_key, {})
    
    return model_data.get(key)


