from __future__ import annotations

from typing import Any

from django.http import HttpResponseNotAllowed, JsonResponse
from neapolitan.views import Role

from powercrud.row_actions import (
    is_lazy_row_action_state_action,
    resolve_extra_action_runtime_state,
)


class RowActionStateMixin:
    """Serve lazy row-action state for dropdown extra actions."""

    row_action_state_action: str | None = None

    def get_row_action_states_endpoint_name(self) -> str | None:
        """Return the URL name that serves lazy row-action state."""
        return f"{self.get_prefix()}-row-action-states"

    def list(self, request, *args, **kwargs):
        """Route lazy row-action state requests before normal list rendering."""
        if getattr(self, "row_action_state_action", None) == "states":
            return self.handle_row_action_states_request(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Reject mutation-style requests to the lazy row-action state endpoint."""
        if getattr(self, "row_action_state_action", None) == "states":
            return HttpResponseNotAllowed(["GET"])
        return super().post(request, *args, **kwargs)

    def handle_row_action_states_request(self, request, *args, **kwargs):
        """Return lazy disabled-state data for the requested row."""
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])
        if self.get_extra_actions_mode() != "dropdown":
            return JsonResponse(
                {"error": "Lazy row-action state requires dropdown mode."},
                status=400,
            )

        self.request = request
        self.kwargs = kwargs
        obj = self.get_object()
        lock_reason = getattr(obj, "_blocked_reason", None)
        lock_label = getattr(obj, "_blocked_label", None)

        actions: dict[str, dict[str, Any]] = {}
        for index, action in enumerate(getattr(self, "extra_actions", []) or []):
            if not is_lazy_row_action_state_action(action):
                continue
            state = resolve_extra_action_runtime_state(
                view=self,
                object=obj,
                action=action,
                request=request,
                lock_reason=lock_reason,
                lock_label=lock_label,
            )
            actions[str(index)] = {
                "hidden": bool(state["hidden"]),
                "disabled": bool(state["disabled"]),
                "reason": state.get("reason") or None,
            }

        return JsonResponse({"actions": actions})

    def get_row_action_states_url(self, obj: Any) -> str | None:
        """Return the lazy row-action state endpoint URL for one object."""
        endpoint_name = self.get_row_action_states_endpoint_name()
        if not endpoint_name:
            return None
        lookup_field = getattr(self, "lookup_field", "pk")
        lookup_url_kwarg = getattr(self, "lookup_url_kwarg", None) or lookup_field
        return self.safe_reverse(
            endpoint_name,
            kwargs={lookup_url_kwarg: getattr(obj, lookup_field)},
        )

    def get_lazy_row_action_state_enabled(self) -> bool:
        """Return whether lazy row-action state is active for this view."""
        if getattr(self, "role", None) != Role.LIST:
            return False
        if self.get_extra_actions_mode() != "dropdown":
            return False
        return any(
            is_lazy_row_action_state_action(action)
            for action in getattr(self, "extra_actions", []) or []
        )
