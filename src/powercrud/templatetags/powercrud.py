"""
This module contains custom template tags for the powercrud package.

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
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import FieldDoesNotExist
from django.conf import settings
from django.db import models 

from powercrud.conf import get_powercrud_setting
from powercrud.logging import get_logger

log = get_logger(__name__)

register = template.Library()


def _coerce_pk(value):
    """
    Helper to extract a string identifier from common Django form values.
    """
    if value is None:
        return None
    for attr in ("pk", "value", "id"):
        if hasattr(value, attr):
            try:
                return str(getattr(value, attr))
            except Exception:
                continue
    try:
        return str(value)
    except Exception:
        return None


@register.filter
def to_string_list(value):
    """
    Convert iterables of model instances / form values into a list of string PKs.
    Handles Django QuerySets, ModelChoiceIteratorValue objects, and plain scalars.
    """
    if value in (None, ""):
        return []
    # Treat single scalar as one-item list
    if isinstance(value, (str, bytes)):
        return [value]
    try:
        iterator = list(value)
    except TypeError:
        coerced = _coerce_pk(value)
        return [coerced] if coerced is not None else []
    result = []
    for item in iterator:
        coerced = _coerce_pk(item)
        if coerced is not None:
            result.append(coerced)
    return result


def _should_center_field(model_field: models.Field) -> bool:
    """
    Return True when the column should default to centered alignment.
    Treat text-like, dropdown (FK), and M2M fields as left-aligned.
    """
    if not model_field:
        return False
    if getattr(model_field, "many_to_many", False):
        return False
    if model_field.is_relation:
        return False

    field_type = model_field.get_internal_type()
    text_types = {
        "CharField",
        "TextField",
        "SlugField",
        "EmailField",
        "URLField",
    }
    if field_type in text_types:
        return False
    # Default to centered for numerics, booleans, and other non-text columns.
    return True

@register.filter
def get_form_field(form, field_name):
    """
    Safely fetch a bound form field by name.
    Returns None if the field does not exist.
    """
    if not form or not field_name:
        return None
    try:
        return form[field_name]
    except KeyError:
        return None

def action_links(view: Any, object: Any) -> str:
    """
    Generate HTML for action links (buttons) for a given object.

    Args:
        view: The view instance
        object: The object for which actions are being generated

    Returns:
        str: HTML string of action buttons
    """
    framework: str = get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')
    styles: Dict[str, Any] = view.get_framework_styles()[framework]
    action_button_classes = view.get_action_button_classes()

    prefix: str = view.get_prefix()
    use_htmx: bool = view.get_use_htmx()
    use_modal: bool = view.get_use_modal()

    default_target: str = view.get_htmx_target() # this will be prepended with a #

    # Standard actions with framework-specific button classes
    lock_reason = getattr(object, "_blocked_reason", None)
    lock_label = getattr(object, "_blocked_label", None)

    actions: List[Tuple[str, str, str, str, bool, str, bool]] = []
    standard_actions = [
        ("View", view.safe_reverse(f"{prefix}-detail", kwargs={"pk": object.pk})),
        ("Edit", view.safe_reverse(f"{prefix}-update", kwargs={"pk": object.pk})),
        ("Delete", view.safe_reverse(f"{prefix}-delete", kwargs={"pk": object.pk})),
    ]
    for name, url in standard_actions:
        if url is None:
            continue
        disable = bool(lock_reason and name in {"Edit", "Delete"})
        actions.append(
            (
                url,
                name,
                styles['actions'][name],
                default_target,
                False,
                use_modal,
                styles["modal_attrs"],
                disable,
            )
        )

    # Add extra actions if defined
    extra_actions: List[Dict[str, Any]] = getattr(view, "extra_actions", [])
    for action in extra_actions:
        url: Optional[str] = view.safe_reverse(
            action["url_name"],
            kwargs={"pk": object.pk} if action.get("needs_pk", True) else None,
        )

        if url is not None:
            htmx_target: str = action.get("htmx_target", default_target)
            if htmx_target and not htmx_target.startswith("#"):
                htmx_target = f"#{htmx_target}"
            button_class: str = action.get("button_class", styles['extra_default'])
            
            display_modal = action.get("display_modal", use_modal)
            show_modal: bool = display_modal if use_modal else False
            modal_attrs: str = styles["modal_attrs"] if show_modal else " "
            
            # Append current query string for modal actions
            query_string = ''
            if show_modal and hasattr(view.request, 'GET') and view.request.GET:
                query_string = '?' + view.request.GET.urlencode()
            
            disable_extra = bool(lock_reason and action.get("lock_sensitive", False))

            actions.append((
                url + query_string if show_modal else url, 
                action["text"], 
                button_class, 
                htmx_target, 
                action.get("hx_post", False),
                show_modal,
                modal_attrs,
                disable_extra,
            ))

    # set up links for all actions (regular and extra)
    links: List[str] = [
        "<div class='join'>" +
        " ".join([
            # Append query string for modal actions (edit/create)
            f"<a href='{url if not show_modal else url + ('?' + view.request.GET.urlencode() if view.request.GET else '')}' "
            f"class='{styles['base']} join-item {button_class} {action_button_classes}{' btn-disabled opacity-50 pointer-events-none' if disable else ''}' "
            + (f"hx-{'post' if hx_post else 'get'}='{url if not show_modal else url + ('?' + view.request.GET.urlencode() if view.request.GET else '')}' " if use_htmx else "")
            + (f"hx-target='{target}' " if use_htmx else "")
            + ("hx-replace-url='true' hx-push-url='true' " if use_htmx and not show_modal else "")
            + (f"{modal_attrs} " if show_modal else "")
            + (f"aria-disabled='true' data-tippy-content='{lock_label}' " if disable and lock_label else "")
            + f"data-inline-action='{anchor_text.lower()}'"
            + f">{anchor_text}</a>"
            for url, anchor_text, button_class, target, hx_post, show_modal, modal_attrs, disable in actions
        ]) +
        "</div>"
    ]

    return mark_safe(" ".join(links))


@register.inclusion_tag(f"powercrud/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}/partial/detail.html")
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
        f"powercrud/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}/partial/list.html", 
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

    inline_config = context.get('inline_edit') or {}
    inline_enabled = bool(inline_config.get('enabled'))
    inline_fields = inline_config.get('fields') or []
    inline_fields = set(inline_fields)
    inline_row_endpoint = inline_config.get('row_endpoint_name')
    inline_dependencies = inline_config.get('dependencies') or {}

    # Check if bulk edit is enabled
    enable_bulk_edit = hasattr(view, 'get_bulk_edit_enabled') and view.get_bulk_edit_enabled()
    
    # Get currently selected IDs from session if bulk edit is enabled
    request = context.get('request') or getattr(view, 'request', None)
    selected_ids = []
    if request and enable_bulk_edit and hasattr(view, 'get_selected_ids_from_session'):
        selected_ids = view.get_selected_ids_from_session(request)
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

    object_list = []
    for obj in objects:
        row_id = getattr(view, "get_inline_row_id", None)
        if callable(row_id):
            row_id = row_id(obj)
        else:
            row_id = None

        inline_row_url = None
        if inline_enabled and inline_row_endpoint:
            inline_row_url = view.safe_reverse(inline_row_endpoint, kwargs={"pk": obj.pk})

        inline_blocked_reason = None
        inline_blocked_label = None
        inline_blocked_meta = {}
        inline_allowed = False

        if inline_enabled and inline_row_url:
            lock_checker = getattr(view, "is_inline_row_locked", None)
            is_locked = False
            if callable(lock_checker):
                try:
                    is_locked = bool(lock_checker(obj))
                except Exception:
                    is_locked = False

            can_inline_callable = getattr(view, "can_inline_edit", None)
            can_inline = inline_enabled
            if callable(can_inline_callable) and request is not None:
                try:
                    can_inline = bool(can_inline_callable(obj, request))
                except Exception:
                    can_inline = False
            elif not callable(can_inline_callable):
                can_inline = inline_enabled
            else:
                can_inline = False

            if is_locked:
                lock_details = {}
                lock_detail_getter = getattr(view, "get_inline_lock_details", None)
                if callable(lock_detail_getter):
                    try:
                        lock_details = lock_detail_getter(obj) or {}
                    except Exception:
                        lock_details = {}
                inline_blocked_meta = lock_details
                inline_blocked_reason = "locked"
                inline_blocked_label = lock_details.get("label") or _("Inline editing blocked – record is locked.")
            elif not can_inline:
                inline_blocked_reason = "forbidden"
                inline_blocked_label = _("Inline editing not permitted for this row.")
            else:
                inline_allowed = True

        # Attach inline metadata to the object for downstream helpers (e.g., action_links)
        setattr(obj, "_blocked_reason", inline_blocked_reason)
        setattr(obj, "_blocked_label", inline_blocked_label)

        record = {
            "object": obj,
            "id": str(obj.pk),  # Add ID for selection tracking
            "is_selected": str(obj.pk) in selected_ids if enable_bulk_edit else False,  # Check if this object is selected
            "row_id": row_id,
            "inline_url": inline_row_url,
            "inline_allowed": inline_allowed,
            "inline_blocked_reason": inline_blocked_reason,
            "inline_blocked_label": inline_blocked_label,
            "inline_blocked_meta": inline_blocked_meta,
            "cells": [],
            "fields": [],
            "actions": action_links(view, obj),
        }

        for f in fields:
            model_field = obj._meta.get_field(f)
            if model_field.many_to_many:
                display_value = ", ".join(str(item) for item in getattr(obj, f).all())
            elif model_field.get_internal_type() == 'BooleanField':
                value = getattr(obj, f)
                if value is True:
                    display_value = mark_safe(TICK_SVG)
                elif value is False:
                    display_value = mark_safe(CROSS_SVG)
                else:
                    display_value = ''
            elif model_field.get_internal_type() == 'DateField' and getattr(obj, f) is not None:
                display_value = getattr(obj, f).strftime('%d/%m/%Y')
            elif model_field.is_relation:
                display_value = str(getattr(obj, f))
            else:
                display_value = model_field.value_to_string(obj)

            cell_align = "center" if _should_center_field(model_field) else "left"

            record["cells"].append({
                "name": f,
                "value": display_value,
                "is_property": False,
                "is_inline_editable": inline_enabled and f in inline_fields,
                "dependency": inline_dependencies.get(f),
                "align": cell_align,
            })
            record["fields"].append(display_value)

        for prop in properties:
            prop_value = getattr(obj, prop)
            if isinstance(getattr(obj.__class__, prop), property) and prop_value is True:
                display_value = mark_safe(TICK_SVG)
            elif isinstance(getattr(obj.__class__, prop), property) and prop_value is False:
                display_value = mark_safe(CROSS_SVG)
            elif isinstance(prop_value, (date, datetime)) and prop_value is not None:
                display_value = prop_value.strftime('%d/%m/%Y')
            else:
                display_value = str(prop_value)

            record["cells"].append({
                "name": prop,
                "value": display_value,
                "is_property": True,
                "is_inline_editable": inline_enabled and prop in inline_fields,
                "dependency": inline_dependencies.get(prop),
                "align": "left",
            })
            record["fields"].append(display_value)

        object_list.append(record)

    request = context.get('request')
    current_sort = request.GET.get('sort', '') if request else ''
    
    # Get all current filter parameters
    filter_params = request.GET.copy() if request else {}
    if 'sort' in filter_params:
        filter_params.pop('sort')
    if 'page' in filter_params:
        filter_params.pop('page')

    # Only keep the last value for each key to avoid duplicate params in URLs
    clean_params = {}
    for k in filter_params:
        clean_params[k] = filter_params.getlist(k)[-1]
    filter_params = filter_params.__class__('', mutable=True)
    for k, v in clean_params.items():
        filter_params[k] = v
    
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
        # add bulk selection context
        "selected_ids": selected_ids,
        # Add bulk edit related context
        "enable_bulk_edit": enable_bulk_edit,
        "selected_count": len(selected_ids) if enable_bulk_edit else 0,
        "model_name": view.model.__name__.lower() if hasattr(view, 'model') else '',
        "selection_key_suffix": selection_key_suffix,
        "inline_edit": inline_config,
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
    framework: str = get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')
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

            new_button = (
                f'<a href="{url}" '
                f'class="{extra_class_attrs} {styles["base"]} {extra_button_classes} {button_class}" '
                f'{extra_attrs} {htmx_attrs_str} '
                f'{modal_attrs}>'
                f'{button["text"]}</a>'                
            )

            buttons.append(
                new_button
            )

    if buttons:
        return mark_safe(" ".join(buttons))
    return ""


@register.simple_tag(takes_context=True)
def get_powercrud_session_data(context, key):
    """
    Get a value from the powercrud session data for the current model.
    
    Usage in template:
    {% get_powercrud_session_data 'original_template' as template_name %}
    """
    request = context.get('request')
    view = context.get('view')
    
    if not request or not view:
        return None
        
    powercrud_data = request.session.get('powercrud', {})
    model_key = view.get_model_session_key()
    model_data = powercrud_data.get(model_key, {})
    
    return model_data.get(key)
