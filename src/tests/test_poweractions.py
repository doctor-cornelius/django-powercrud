import pytest

from powercrud.actions import PowerAction, PowerButton


def test_poweraction_to_dict_exposes_primitive_extra_action_config():
    action = PowerAction(
        text="Preview",
        url_name="sample:book-detail",
        display_modal=True,
        button_class="btn-secondary",
        hidden_if="should_hide_preview",
        disabled_state="get_preview_disabled_state",
    )

    assert action.to_dict() == {
        "url_name": "sample:book-detail",
        "text": "Preview",
        "needs_pk": True,
        "button_class": "btn-secondary",
        "display_modal": True,
        "hx_post": False,
        "lock_sensitive": False,
        "refresh_list_on_modal_close": False,
        "hidden_if": "should_hide_preview",
        "disabled_state": "get_preview_disabled_state",
    }, "PowerAction should compile to the primitive extra_actions dictionary shape."


def test_poweraction_with_options_returns_changed_copy_without_mutating_original():
    original = PowerAction(
        text="Preview",
        url_name="sample:book-detail",
        display_modal=True,
        modal_box_classes="modal-box max-w-5xl",
    )

    copied = original.with_options(
        text="Timeline",
        url_name="sample:book-timeline",
    )

    assert copied is not original, "with_options should return a new PowerAction."
    assert original.text == "Preview", "with_options should not mutate the source action."
    assert copied.to_dict()["text"] == "Timeline", (
        "with_options should apply the requested action changes."
    )
    assert copied.to_dict()["modal_box_classes"] == "modal-box max-w-5xl", (
        "with_options should preserve unchanged action options."
    )


def test_poweraction_rejects_mixed_disabled_state_styles():
    with pytest.raises(ValueError, match="disabled_state"):
        PowerAction(
            text="Preview",
            url_name="sample:book-detail",
            disabled_state="get_preview_disabled_state",
            disabled_if="is_preview_disabled",
        )


def test_poweraction_rejects_invalid_hidden_if_method_name():
    """Reject non-string PowerAction hidden_if declarations."""
    with pytest.raises(ValueError, match="hidden_if"):
        PowerAction(
            text="Preview",
            url_name="sample:book-detail",
            hidden_if=True,
        )


def test_poweraction_rejects_disabled_reason_without_disabled_if():
    with pytest.raises(ValueError, match="disabled_reason requires disabled_if"):
        PowerAction(
            text="Preview",
            url_name="sample:book-detail",
            disabled_reason="get_preview_disabled_reason",
        )


def test_poweraction_to_dict_exposes_permission_affordance_config():
    """Expose permission affordance settings in the primitive action dictionary."""
    action = PowerAction(
        text="Submit",
        url_name="sample:book-submit",
        permission_check="can_submit_book",
        permission_behavior="disable",
        permission_denied_reason="You cannot submit this book.",
    )

    assert action.to_dict()["permission_check"] == "can_submit_book", (
        "PowerAction should expose permission_check in the primitive dictionary."
    )
    assert action.to_dict()["permission_behavior"] == "disable", (
        "PowerAction should expose explicit permission behavior."
    )
    assert (
        action.to_dict()["permission_denied_reason"] == "You cannot submit this book."
    ), "PowerAction should expose the permission-denied reason."


def test_poweraction_rejects_mixed_permission_declarations():
    """Reject ambiguous PowerAction permission declarations."""
    with pytest.raises(ValueError, match="permission"):
        PowerAction(
            text="Submit",
            url_name="sample:book-submit",
            permission="sample.submit_book",
            permission_check="can_submit_book",
        )


def test_poweraction_rejects_invalid_permission_behavior():
    """Reject unknown PowerAction permission behavior values."""
    with pytest.raises(ValueError, match="permission_behavior"):
        PowerAction(
            text="Submit",
            url_name="sample:book-submit",
            permission="sample.submit_book",
            permission_behavior="show",
        )


def test_powerbutton_to_dict_exposes_primitive_extra_button_config():
    button = PowerButton(
        text="Selected Summary",
        url_name="sample:book-selected-summary",
        display_modal=True,
        uses_selection=True,
        selection_min_count=1,
        selection_min_behavior="disable",
        selection_min_reason="Select at least one book first.",
    )

    assert button.to_dict() == {
        "url_name": "sample:book-selected-summary",
        "text": "Selected Summary",
        "needs_pk": False,
        "display_modal": True,
        "refresh_list_on_modal_close": False,
        "uses_selection": True,
        "selection_min_count": 1,
        "selection_min_behavior": "disable",
        "selection_min_reason": "Select at least one book first.",
    }, "PowerButton should compile to the primitive extra_buttons dictionary shape."


def test_powerbutton_to_dict_omits_non_selection_default_thresholds():
    button = PowerButton(
        text="Approvals Queue",
        url_name="sample:book-list",
        button_class="btn-outline",
        display_modal=False,
        htmx_target="content",
    )

    button_dict = button.to_dict()

    assert button_dict["uses_selection"] is False, (
        "Plain PowerButton declarations should still expose the normalized selection flag."
    )
    assert "selection_min_count" not in button_dict, (
        "Plain PowerButton declarations should not serialize generated selection defaults."
    )
    assert "selection_min_behavior" not in button_dict, (
        "Plain PowerButton declarations should not look like threshold-configured buttons."
    )
    assert "selection_min_reason" not in button_dict, (
        "Plain PowerButton declarations should omit empty threshold reason metadata."
    )


def test_powerbutton_with_options_returns_changed_copy_without_mutating_original():
    original = PowerButton(
        text="Home",
        url_name="home",
        button_class="btn-success",
        htmx_target="content",
    )

    copied = original.with_options(
        text="Home in Modal!",
        display_modal=True,
        button_class="btn-warning",
    )

    assert copied is not original, "with_options should return a new PowerButton."
    assert original.display_modal is False, (
        "with_options should not mutate the source button."
    )
    assert copied.to_dict()["display_modal"] is True, (
        "with_options should apply the requested button changes."
    )
    assert copied.to_dict()["htmx_target"] == "content", (
        "with_options should preserve unchanged button options."
    )


def test_powerbutton_rejects_selection_button_with_pk_url():
    with pytest.raises(ValueError, match="needs_pk=True"):
        PowerButton(
            text="Selected Summary",
            url_name="sample:book-selected-summary",
            needs_pk=True,
            uses_selection=True,
        )


def test_powerbutton_normalizes_selection_min_count_to_int():
    button = PowerButton(
        text="Selected Summary",
        url_name="sample:book-selected-summary",
        selection_min_count="2",
    )

    assert button.to_dict()["selection_min_count"] == 2, (
        "PowerButton should normalize selection_min_count the same way view config does."
    )


def test_powerbutton_to_dict_exposes_permission_affordance_config():
    """Expose permission affordance settings in the primitive button dictionary."""
    button = PowerButton(
        text="Admin Review",
        url_name="sample:book-admin-review",
        permission="sample.manage_books",
        permission_behavior="hide",
    )

    assert button.to_dict()["permission"] == "sample.manage_books", (
        "PowerButton should expose permission strings in the primitive dictionary."
    )
    assert button.to_dict()["permission_behavior"] == "hide", (
        "PowerButton should expose explicit permission behavior."
    )


def test_powerbutton_rejects_mixed_permission_declarations():
    """Reject ambiguous PowerButton permission declarations."""
    with pytest.raises(ValueError, match="permission"):
        PowerButton(
            text="Admin Review",
            url_name="sample:book-admin-review",
            permission="sample.manage_books",
            permission_check="can_manage_books",
        )


def test_powerbutton_rejects_invalid_permission_behavior():
    """Reject unknown PowerButton permission behavior values."""
    with pytest.raises(ValueError, match="permission_behavior"):
        PowerButton(
            text="Admin Review",
            url_name="sample:book-admin-review",
            permission="sample.manage_books",
            permission_behavior="show",
        )
