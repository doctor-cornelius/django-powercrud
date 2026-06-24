from __future__ import annotations

from typing import Any


LAZY_DISABLED_STATE_UNAVAILABLE_MESSAGE = "Unable to validate current availability."


def is_lazy_disabled_state_action(action: dict[str, Any]) -> bool:
    """Return True when a row action opts into lazy disabled-state resolution."""
    return action.get("disabled_state_mode", "eager") == "lazy"


def resolve_named_view_method(view: Any, method_name: str | None) -> Any:
    """Resolve a named method on the view, returning None when unavailable."""
    if not method_name:
        return None
    resolver = getattr(view, method_name, None)
    if callable(resolver):
        return resolver
    return None


def resolve_extra_action_disabled_state(
    *,
    view: Any,
    object: Any,
    action: dict[str, Any],
    request: Any,
    lock_reason: str | None,
    lock_label: str | None,
) -> tuple[bool, str | None]:
    """Determine whether an extra action should render disabled and why."""
    disable = bool(lock_reason and action.get("lock_sensitive", False))
    disabled_reason = lock_label if disable else None

    disabled_state_name = action.get("disabled_state")
    if disabled_state_name:
        disabled_state = resolve_named_view_method(view, disabled_state_name)
        if disabled_state is not None:
            try:
                state_reason = disabled_state(object, request)
            except Exception:
                state_reason = None
            if isinstance(state_reason, str) and state_reason.strip():
                return True, state_reason

    disabled_if_name = action.get("disabled_if")
    if disabled_if_name:
        disabled_if = resolve_named_view_method(view, disabled_if_name)
        if disabled_if is not None:
            try:
                custom_disabled = bool(disabled_if(object, request))
            except Exception:
                custom_disabled = False
            if custom_disabled:
                disable = True
                disabled_reason_name = action.get("disabled_reason")
                disabled_reason_resolver = resolve_named_view_method(
                    view, disabled_reason_name
                )
                if disabled_reason_resolver is not None:
                    try:
                        disabled_reason = disabled_reason_resolver(object, request)
                    except Exception:
                        disabled_reason = None

    return disable, disabled_reason


def resolve_extra_action_permission_state(
    *,
    view: Any,
    object: Any,
    action: dict[str, Any],
    request: Any,
) -> tuple[bool, bool, str | None]:
    """Determine whether permission config should hide or disable an extra action."""
    permission = action.get("permission")
    permission_check_name = action.get("permission_check")
    if not permission and not permission_check_name:
        return False, False, None

    allowed = False
    if permission:
        permission_resolver = getattr(view, "has_power_permission", None)
        if callable(permission_resolver):
            try:
                allowed = bool(permission_resolver(permission, request, obj=object))
            except Exception:
                allowed = False
    elif permission_check_name:
        permission_check = resolve_named_view_method(view, permission_check_name)
        if permission_check is not None:
            try:
                allowed = bool(permission_check(request, object))
            except Exception:
                allowed = False

    if allowed:
        return False, False, None

    disabled_reason = action.get("permission_denied_reason")
    if not isinstance(disabled_reason, str) or not disabled_reason.strip():
        disabled_reason = None

    if action.get("permission_behavior", "hide") == "disable":
        return False, True, disabled_reason
    return True, False, None


def resolve_extra_action_hidden_state(
    *,
    view: Any,
    object: Any,
    action: dict[str, Any],
    request: Any,
) -> bool:
    """Determine whether an extra action should be hidden for a row."""
    hidden_if_name = action.get("hidden_if")
    if not hidden_if_name:
        return False
    hidden_if = resolve_named_view_method(view, hidden_if_name)
    if hidden_if is None:
        return False
    try:
        return bool(hidden_if(object, request))
    except Exception:
        return False


def resolve_extra_action_runtime_state(
    *,
    view: Any,
    object: Any,
    action: dict[str, Any],
    request: Any,
    lock_reason: str | None,
    lock_label: str | None,
) -> dict[str, Any]:
    """Resolve hidden and disabled state for one row action."""
    hide_permission, disable_permission, permission_disabled_reason = (
        resolve_extra_action_permission_state(
            view=view,
            object=object,
            action=action,
            request=request,
        )
    )
    if hide_permission:
        return {"hidden": True, "disabled": True, "reason": None}

    if not disable_permission and resolve_extra_action_hidden_state(
        view=view,
        object=object,
        action=action,
        request=request,
    ):
        return {"hidden": True, "disabled": True, "reason": None}

    if disable_permission:
        return {
            "hidden": False,
            "disabled": True,
            "reason": permission_disabled_reason,
        }

    disabled, reason = resolve_extra_action_disabled_state(
        view=view,
        object=object,
        action=action,
        request=request,
        lock_reason=lock_reason,
        lock_label=lock_label,
    )
    return {"hidden": False, "disabled": disabled, "reason": reason}
