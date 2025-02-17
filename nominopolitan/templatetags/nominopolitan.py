from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import FieldDoesNotExist
from django.conf import settings


import logging
log = logging.getLogger("nominopolitan")

register = template.Library()

def action_links(view, object):

    # FRAMEWORK_STYLES = {
    #     'bulma': {
    #         'base': 'button is-small',
    #         'actions': {
    #             'View': 'is-info',
    #             'Edit': 'is-link',
    #             'Delete': 'is-danger'
    #         },
    #         'extra_default': 'is-link',
    #         'modal_attrs': '',  # Bulma uses Alpine.js so no additional attributes needed
    #     'filter_attrs': {
    #         'class': 'input is-small',
    #         'style': 'font-size: 0.875rem;'
    #     }
    #     },
    #     'bootstrap5': {
    #         'base': 'btn btn-sm',
    #         'actions': {
    #             'View': 'btn-info',
    #             'Edit': 'btn-primary',
    #             'Delete': 'btn-danger'
    #         },
    #         'extra_default': 'btn-primary',
    #         'modal_attrs': f'data-bs-toggle="modal" data-bs-target="{view.get_modal_id()}"',
    #         'filter_attrs': {
    #             'class': 'form-control-xs small py-1',
    #             'style': 'font-size: 0.875rem;'
    #         }
    #     }
    # }

    framework = getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bulma')
    styles = view.get_framework_styles()[framework]

    prefix = view.get_prefix()
    # below takes account of use_htmx, use_modal
    use_htmx = view.get_use_htmx()
    use_modal = view.get_use_modal()

    default_target = view.get_htmx_target() # this will be prepended with a #

    # Standard actions with Bulma button classes
    actions = [
        (url, name, styles['actions'][name], default_target, False, styles["modal_attrs"])  # View button
        for url, name in [
            (
                view.safe_reverse(f"{prefix}-detail", kwargs={"pk": object.pk}),
                "View",
            ),
            (
                view.safe_reverse(f"{prefix}-update", kwargs={"pk": object.pk}),
                "Edit",
            ),
            (
                view.safe_reverse(f"{prefix}-delete", kwargs={"pk": object.pk}),
                "Delete",
            ),
        ]
        if url is not None
    ]

    # Add extra actions if defined
    extra_actions = getattr(view, "extra_actions", [])
    for action in extra_actions:
        url = view.safe_reverse(
            action["url_name"],
            kwargs={"pk": object.pk} if action.get("needs_pk", True) else None,
        )
        if url is not None:
            htmx_target = action.get("htmx_target", default_target)
            if htmx_target and not htmx_target.startswith("#"):
                htmx_target = f"#{htmx_target}"
            button_class = action.get("button_class", styles['extra_default'])
            
            # Add display_modal check
            show_modal = action.get("display_modal", view.get_use_modal())
            modal_attrs = styles["modal_attrs"] if show_modal else " "
            
            actions.append((
                url, 
                action["text"], 
                button_class, 
                htmx_target, 
                action.get("hx_post", False),
                modal_attrs
            ))

    # set up links for all actions (regular and extra)
    # note for future - could simplify by just conditionally adding hx-disable if not use_htmx
    links = [
        f"<div class='btn-group btn-group-sm'>" +
        " ".join([
            f"<a href='{url}' class='{styles['base']} {button_class}' "
            + (f"hx-{'post' if hx_post else 'get'}='{url}' " if use_htmx else "")
            + (f"hx-target='{target}' " if use_htmx else "")
            + (f"hx-replace-url='true' hx-push-url='true' " if use_htmx and not view.get_use_modal() else "")
            + (f"{modal_attrs} " if use_modal else "")
            + f">{anchor_text}</a>"
            for url, anchor_text, button_class, target, hx_post, modal_attrs in actions
        ]) +
        "</div>"
    ]

    return mark_safe(" ".join(links))


@register.inclusion_tag(f"nominopolitan/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bootstrap')}/partial/detail.html")
def object_detail(object, view):
    """
    Display both fields and properties for an object detail view
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
        f"nominopolitan/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'bootstrap')}/partial/list.html", 
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

    # Headers for fields - get the related model's verbose_name for relation fields
    field_headers = []
    for f in fields:
        field_headers.append(f.replace('_', ' ').title())

    # Headers for properties with proper capitalization
    property_headers = [prop.replace("_", " ").title() for prop in properties]

    # Combine headers
    headers = field_headers + property_headers

    object_list = [
        {
            "object": object,
            "fields": [
                (
                    # override default to set value = str()
                    str(getattr(object, f))
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

    return {
        "headers": headers,
        "object_list": object_list,
    }

@register.simple_tag
def get_proper_elided_page_range(paginator, number, on_each_side=1, on_ends=1):
    """Return a list of page numbers with proper elision"""
    page_range = paginator.get_elided_page_range(
        number=number,
        on_each_side=1,
        on_ends=1
    )
    return page_range



