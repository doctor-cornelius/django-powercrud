"""System checks for the optional PowerCRUD favourites contrib app."""

from __future__ import annotations

from django.apps import apps
from django.core.checks import Warning, register

from .services import get_unavailable_favourites_route_names


@register()
def check_favourites_url_configuration(app_configs=None, **kwargs):
    """Warn when the favourites contrib app is installed without its shared routes."""

    del app_configs, kwargs

    if not apps.is_installed("powercrud.contrib.favourites"):
        return []

    unavailable_routes = get_unavailable_favourites_route_names()
    if not unavailable_routes:
        return []

    unavailable_routes_list = ", ".join(unavailable_routes)
    return [
        Warning(
            "PowerCRUD favourites is installed but its shared URLs are not mounted.",
            hint=(
                "Mount include('powercrud.urls', namespace='powercrud') in your project "
                "URLconf. Favourites will stay disabled until the shared PowerCRUD routes "
                f"are reversible. Missing routes: {unavailable_routes_list}."
            ),
            id="powercrud.W001",
        )
    ]
