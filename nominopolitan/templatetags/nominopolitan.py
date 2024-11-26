from django import template
from django.utils.safestring import mark_safe

import logging
log = logging.getLogger("nominopolitan")

register = template.Library()


def action_links(view, object):
    prefix = view.get_prefix()
    # below takes account of use_htmx, use_modal and htmx_crud_target
    default_target = view.get_htmx_target() # this will be prepended with a #

    # Standard actions with Bulma button classes
    actions = [
        (
            (url, name, "is-info", default_target)  # View button
            if name == "View"
            else (
                (url, name, "is-link", default_target)  # Edit button
                if name == "Edit"
                else (url, name, "is-danger", default_target)  # Delete button
            )
        )
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
            # Use action's htmx_target if specified, otherwise use default
            htmx_target = action.get("htmx_target", default_target)
            if htmx_target and not htmx_target.startswith("#"):
                htmx_target = f"#{htmx_target}"
            button_class = action.get("button_class", "is-link")
            actions.append((url, action["text"], button_class, htmx_target))

    if default_target:
        links = [
            (
                f"<a href='{url}' class='button is-small {button_class}' "
                f"hx-get='{url}' hx-target='{target}' "
                f"{f'hx-replace-url=\"true\" hx-push-url=\"true\"' if not view.get_use_modal() else ''}"
                f">"
                f"{anchor_text}</a>"
            )
            for url, anchor_text, button_class, target in actions
        ]
    else:
        links = [
            f"<a href='{url}' class='button is-small {button_class}'>{anchor_text}</a>"
            for url, anchor_text, button_class, _ in actions
        ]

    return mark_safe(" ".join(links))


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

    # log.debug(f"object_list: {object_list}")

    return {
        "headers": headers,
        "object_list": object_list,
    }
