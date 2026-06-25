from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


def _validate_non_empty_string(value: str, field_name: str, class_name: str) -> None:
    """Validate a required non-empty string field."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{class_name}.{field_name} must be a non-empty string")


def _validate_optional_method_name(
    value: str | None, field_name: str, class_name: str
) -> None:
    """Validate an optional method-name field without resolving the view method."""
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{class_name}.{field_name} must be a non-empty string")


def _validate_optional_string(
    value: str | None, field_name: str, class_name: str
) -> None:
    """Validate an optional non-empty string field."""
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{class_name}.{field_name} must be a non-empty string")


def _validate_bool(value: bool | None, field_name: str, class_name: str) -> None:
    """Validate an optional boolean field."""
    if value is not None and not isinstance(value, bool):
        raise ValueError(f"{class_name}.{field_name} must be True or False")


def _validate_permission_options(
    *,
    permission: str | None,
    permission_check: str | None,
    permission_behavior: str | None,
    permission_denied_reason: str | None,
    class_name: str,
) -> None:
    """Validate shared permission affordance declaration options."""
    _validate_optional_string(permission, "permission", class_name)
    _validate_optional_method_name(permission_check, "permission_check", class_name)
    _validate_optional_string(
        permission_denied_reason,
        "permission_denied_reason",
        class_name,
    )
    if permission and permission_check:
        raise ValueError(f"{class_name} cannot combine permission with permission_check")
    if permission_behavior is not None:
        _validate_optional_string(permission_behavior, "permission_behavior", class_name)
        if permission_behavior not in {"hide", "disable"}:
            raise ValueError(
                f"{class_name}.permission_behavior must be 'hide' or 'disable'"
            )


def _copy_without_none(values: dict[str, Any]) -> dict[str, Any]:
    """Return a primitive config dict, omitting optional None values."""
    return {key: value for key, value in values.items() if value is not None}


@dataclass(frozen=True)
class PowerAction:
    """Reusable declaration for one row-level ``extra_actions`` item."""

    text: str
    url_name: str
    needs_pk: bool = True
    button_class: str | None = None
    htmx_target: str | None = None
    display_modal: bool | None = None
    modal_box_classes: str | None = None
    hx_post: bool = False
    lock_sensitive: bool = False
    refresh_list_on_modal_close: bool = False
    hidden_if: str | None = None
    hidden_if_mode: str | None = None
    disabled_state: str | None = None
    disabled_state_mode: str | None = None
    disabled_if: str | None = None
    disabled_reason: str | None = None
    permission: str | None = None
    permission_check: str | None = None
    permission_behavior: str | None = None
    permission_denied_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate the declaration shape before it reaches view config."""
        class_name = self.__class__.__name__
        _validate_non_empty_string(self.text, "text", class_name)
        _validate_non_empty_string(self.url_name, "url_name", class_name)
        for field_name in (
            "needs_pk",
            "display_modal",
            "hx_post",
            "lock_sensitive",
            "refresh_list_on_modal_close",
        ):
            _validate_bool(getattr(self, field_name), field_name, class_name)
        for field_name in (
            "hidden_if",
            "disabled_state",
            "disabled_state_mode",
            "disabled_if",
            "disabled_reason",
        ):
            _validate_optional_method_name(
                getattr(self, field_name),
                field_name,
                class_name,
            )
        if self.hidden_if_mode is not None:
            _validate_optional_string(self.hidden_if_mode, "hidden_if_mode", class_name)
            if self.hidden_if_mode not in {"eager", "lazy"}:
                raise ValueError("PowerAction.hidden_if_mode must be 'eager' or 'lazy'")
            if self.hidden_if_mode == "lazy" and not self.hidden_if:
                raise ValueError("PowerAction.hidden_if_mode='lazy' requires hidden_if")
        if self.disabled_state and (self.disabled_if or self.disabled_reason):
            raise ValueError(
                "PowerAction cannot combine disabled_state with disabled_if or disabled_reason"
            )
        if self.disabled_state_mode is not None:
            if self.disabled_state_mode not in {"eager", "lazy"}:
                raise ValueError(
                    "PowerAction.disabled_state_mode must be 'eager' or 'lazy'"
                )
            if self.disabled_state_mode == "lazy" and not self.disabled_state:
                raise ValueError(
                    "PowerAction.disabled_state_mode='lazy' requires disabled_state"
                )
        if self.disabled_reason and not self.disabled_if:
            raise ValueError(
                "PowerAction.disabled_reason requires disabled_if; use disabled_state for a single-hook disabled contract"
            )
        _validate_permission_options(
            permission=self.permission,
            permission_check=self.permission_check,
            permission_behavior=self.permission_behavior,
            permission_denied_reason=self.permission_denied_reason,
            class_name=class_name,
        )

    def with_options(self, **changes: Any) -> "PowerAction":
        """Return a copy of this action with selected options changed."""
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        """Return the primitive ``extra_actions`` dictionary for this action."""
        return _copy_without_none(
            {
                "url_name": self.url_name,
                "text": self.text,
                "needs_pk": self.needs_pk,
                "button_class": self.button_class,
                "htmx_target": self.htmx_target,
                "display_modal": self.display_modal,
                "modal_box_classes": self.modal_box_classes,
                "hx_post": self.hx_post,
                "lock_sensitive": self.lock_sensitive,
                "refresh_list_on_modal_close": self.refresh_list_on_modal_close,
                "hidden_if": self.hidden_if,
                "hidden_if_mode": self.hidden_if_mode,
                "disabled_state": self.disabled_state,
                "disabled_state_mode": self.disabled_state_mode,
                "disabled_if": self.disabled_if,
                "disabled_reason": self.disabled_reason,
                "permission": self.permission,
                "permission_check": self.permission_check,
                "permission_behavior": self.permission_behavior,
                "permission_denied_reason": self.permission_denied_reason,
            }
        )


@dataclass(frozen=True)
class PowerButton:
    """Reusable declaration for one toolbar-level ``extra_buttons`` item."""

    text: str
    url_name: str
    needs_pk: bool = False
    button_class: str | None = None
    htmx_target: str | None = None
    display_modal: bool = False
    modal_box_classes: str | None = None
    refresh_list_on_modal_close: bool = False
    extra_attrs: str | None = None
    extra_class_attrs: str | None = None
    uses_selection: bool = False
    selection_min_count: int = 0
    selection_min_behavior: str = "allow"
    selection_min_reason: str | None = None
    permission: str | None = None
    permission_check: str | None = None
    permission_behavior: str | None = None
    permission_denied_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate the declaration shape before it reaches view config."""
        class_name = self.__class__.__name__
        _validate_non_empty_string(self.text, "text", class_name)
        _validate_non_empty_string(self.url_name, "url_name", class_name)
        for field_name in (
            "needs_pk",
            "display_modal",
            "refresh_list_on_modal_close",
            "uses_selection",
        ):
            _validate_bool(getattr(self, field_name), field_name, class_name)
        try:
            selection_min_count = int(self.selection_min_count)
        except (TypeError, ValueError) as exc:
            raise ValueError("PowerButton.selection_min_count must be an integer") from exc
        if selection_min_count < 0:
            raise ValueError("PowerButton.selection_min_count must be >= 0")
        object.__setattr__(self, "selection_min_count", selection_min_count)
        if self.selection_min_behavior not in {"allow", "disable"}:
            raise ValueError(
                "PowerButton.selection_min_behavior must be 'allow' or 'disable'"
            )
        if self.uses_selection and self.needs_pk:
            raise ValueError(
                "PowerButton cannot set needs_pk=True when uses_selection=True"
            )
        _validate_permission_options(
            permission=self.permission,
            permission_check=self.permission_check,
            permission_behavior=self.permission_behavior,
            permission_denied_reason=self.permission_denied_reason,
            class_name=class_name,
        )

    def with_options(self, **changes: Any) -> "PowerButton":
        """Return a copy of this button with selected options changed."""
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        """Return the primitive ``extra_buttons`` dictionary for this button."""
        values: dict[str, Any] = {
            "url_name": self.url_name,
            "text": self.text,
            "needs_pk": self.needs_pk,
            "button_class": self.button_class,
            "htmx_target": self.htmx_target,
            "display_modal": self.display_modal,
            "modal_box_classes": self.modal_box_classes,
            "refresh_list_on_modal_close": self.refresh_list_on_modal_close,
            "extra_attrs": self.extra_attrs,
            "extra_class_attrs": self.extra_class_attrs,
            "uses_selection": self.uses_selection,
            "permission": self.permission,
            "permission_check": self.permission_check,
            "permission_behavior": self.permission_behavior,
            "permission_denied_reason": self.permission_denied_reason,
        }
        has_selection_options = (
            self.selection_min_count != 0
            or self.selection_min_behavior != "allow"
            or self.selection_min_reason is not None
        )
        if self.uses_selection or has_selection_options:
            values.update(
                {
                    "selection_min_count": self.selection_min_count,
                    "selection_min_behavior": self.selection_min_behavior,
                    "selection_min_reason": self.selection_min_reason,
                }
            )
        return _copy_without_none(values)


__all__ = ["PowerAction", "PowerButton"]
