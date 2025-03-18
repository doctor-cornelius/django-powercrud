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

from typing import Any, Dict, List, Optional, Tuple
import re  # Add this import at the top with other imports

from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import FieldDoesNotExist
from django.conf import settings


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
    framework: str = getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bootstrap5')
    styles: Dict[str, Any] = view.get_framework_styles()[framework]

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
        log.debug(f"Extra action: {action}, url: {url}")
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
        f"<div class='btn-group btn-group-sm'>" +
        " ".join([
            f"<a href='{url}' class='{styles['base']}{styles['extra_actions_button_padding']} {button_class}' style='{styles['button_style']}' "
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


@register.inclusion_tag(f"nominopolitan/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bootstrap5')}/partial/detail.html")
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
        f"nominopolitan/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bootstrap5')}/partial/list.html", 
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

    # Create tuples of (display_name, field_name) for each field
    headers = []
    for f in fields:
        field = view.model._meta.get_field(f)
        display_name = field.verbose_name.title() if field.verbose_name else f.replace('_', ' ').title()
        headers.append((display_name, f))

    # Add properties with proper display names
    for prop in properties:
        display_name = prop.replace('_', ' ').title()
        headers.append((display_name, prop))

    object_list = [
        {
            "object": object,
            "fields": [
                (
                    str(getattr(object, f).strftime('%d/%m/%Y'))
                    if object._meta.get_field(f).get_internal_type() == 'DateField' and getattr(object, f) is not None
                    else str(getattr(object, f))
                    if object._meta.get_field(f).is_relation
                    else object._meta.get_field(f).value_to_string(object)
                )
                for f in fields
            ]
            + [str(getattr(object, prop)) for prop in properties],
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
        "headers": headers,  # Now contains tuples of (display_name, field_name)
        "object_list": object_list,
        "current_sort": current_sort,
        "filter_params": filter_params.urlencode(),  # Add filter parameters to context
        "use_htmx": use_htmx,
        "original_target": original_target,
        "table_pixel_height_other_page_elements": view.get_table_pixel_height_other_page_elements(),
        "table_max_height": view.get_table_max_height(),
        "htmx_target": htmx_target,
        "request": request,
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
    framework: str = getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bootstrap5')
    styles: Dict[str, Any] = view.get_framework_styles()[framework]
    
    use_htmx: bool = view.get_use_htmx()
    use_modal: bool = view.get_use_modal()

    extra_buttons: List[Dict[str, Any]] = getattr(view, "extra_buttons", [])
    
    buttons: List[str] = []
    for button in extra_buttons:
        display_modal = button.get("display_modal", False) and use_modal
        modal_attrs = ""

        url: Optional[str] = view.safe_reverse(
            button["url_name"],
            kwargs={} if not button.get("needs_pk", False) else None
        )
        if url is not None:
            htmx_attrs = ""
            if use_htmx:
                if display_modal:
                    htmx_target = view.get_modal_target()
                    modal_attrs = styles.get("modal_attrs", "")
                else:
                    htmx_target = button.get("htmx_target", "")
                    if htmx_target and not htmx_target.startswith("#"):
                        htmx_target = f"#{htmx_target}"
                htmx_attrs = (
                    f'hx-get="{url}" hx-target="{htmx_target}" '
                    f'{("hx-replace-url=\"true\" hx-push-url=\"true\" " if use_htmx and not display_modal else "")}'
                )                
            
            button_class = button.get("button_class", styles['extra_default'])
            
            buttons.append(
                f'<a href="{url}" '
                f'class="{styles["base"]} {button_class} {button.get("extra_class_attrs", "")}" '
                f'{button.get("extra_attrs", "")}'
                f'style="{styles["button_style"]}" '
                f'{htmx_attrs} {modal_attrs}>'
                f'{button["text"]}</a>'
            )

    if buttons:
        return mark_safe(" ".join(buttons))
    return ""


