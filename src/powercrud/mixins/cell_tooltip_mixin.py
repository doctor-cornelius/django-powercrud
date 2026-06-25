from __future__ import annotations

from typing import Any

from django.http import HttpResponseNotAllowed, JsonResponse

from powercrud.cell_tooltips import (
    normalize_list_cell_tooltip_specs,
    resolve_list_cell_tooltip,
)


class CellTooltipMixin:
    """Serve lazy list-cell semantic tooltip content."""

    cell_tooltip_action: str | None = None

    def get_list_cell_tooltip_endpoint_name(self) -> str | None:
        """Return the URL name that serves lazy list-cell tooltip content."""
        return f"{self.get_prefix()}-cell-tooltip"

    def list(self, request, *args, **kwargs):
        """Route lazy tooltip requests before normal list rendering."""
        if getattr(self, "cell_tooltip_action", None) == "content":
            return self.handle_list_cell_tooltip_request(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Reject mutation-style requests to the lazy tooltip endpoint."""
        if getattr(self, "cell_tooltip_action", None) == "content":
            return HttpResponseNotAllowed(["GET"])
        return super().post(request, *args, **kwargs)

    def handle_list_cell_tooltip_request(self, request, *args, **kwargs):
        """Return lazy tooltip content for one configured row cell."""
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])

        self.request = request
        self.kwargs = kwargs
        field_name = kwargs.get("field_name")
        specs = normalize_list_cell_tooltip_specs(self.get_list_cell_tooltip_fields())
        spec = specs.get(field_name)
        if spec is None or spec.mode != "lazy":
            return JsonResponse(
                {"error": "Lazy tooltip is not configured for this field."},
                status=404,
            )

        obj = self.get_object()
        properties = set(getattr(self, "properties", []) or [])
        tooltip_text = resolve_list_cell_tooltip(
            view=self,
            obj=obj,
            field_name=field_name,
            is_property=field_name in properties,
            request=request,
            hook_name=spec.hook,
        )
        return JsonResponse({"tooltip": tooltip_text})

    def get_list_cell_tooltip_url(self, obj: Any, field_name: str) -> str | None:
        """Return the lazy tooltip endpoint URL for one object/field pair."""
        endpoint_name = self.get_list_cell_tooltip_endpoint_name()
        if not endpoint_name:
            return None
        lookup_field = getattr(self, "lookup_field", "pk")
        lookup_url_kwarg = getattr(self, "lookup_url_kwarg", None) or lookup_field
        return self.safe_reverse(
            endpoint_name,
            kwargs={
                lookup_url_kwarg: getattr(obj, lookup_field),
                "field_name": field_name,
            },
        )
