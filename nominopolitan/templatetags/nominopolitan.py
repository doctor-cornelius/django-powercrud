from django import template
from django.utils.safestring import mark_safe

import logging
log = logging.getLogger("nominopolitan")

register = template.Library()

def action_links(view, object):
    prefix = view.get_prefix()
    use_htmx = getattr(view, "use_htmx", False)
    htmx_target = view.request.htmx.target if use_htmx and view.request.htmx else None

    actions = [
        (url, name)
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
    # links = [f"<a href='{url}'>{anchor_text}</a>" for url, anchor_text in actions]
    links = [
        (f"<a href='{url}' {f'hx-get={url} hx-target=#{htmx_target} hx-replace-url="true" hx-push-url="true"' 
                            if use_htmx 
                            else ''}>{anchor_text}</a>")
        for url, anchor_text in actions
    ]

    return mark_safe(" | ".join(links))


@register.inclusion_tag(f"nominopolitan/partial/detail.html")
def object_detail(object, fields):
    """
    Override default to set value = str()
    instead of value_to_string(). This allows related fields
    to be displayed correctly (not just the id)
    """
    def iter():
        for f in fields:
            field = object._meta.get_field(f)
            if field.is_relation:
                # override default to set value = str()
                value = str(getattr(object, f))
            else:
                value = field.value_to_string(object)
            yield (field.verbose_name, value)

    return {"object": iter()}


@register.inclusion_tag("nominopolitan/partial/list.html")
def object_list(objects, view):
    """
    Override default to set value = str()
    instead of value_to_string(). This allows related fields
    to be displayed correctly (not just the id)
    """
    fields = view.fields
    properties = getattr(view, "properties", [])

    # Headers for fields
    field_headers = [objects[0]._meta.get_field(f).verbose_name for f in fields]

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
