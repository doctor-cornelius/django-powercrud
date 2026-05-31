import pytest

from powercrud.actions import PowerAction, PowerButton


def test_poweraction_to_dict_exposes_primitive_extra_action_config():
    action = PowerAction(
        text="Preview",
        url_name="sample:book-detail",
        display_modal=True,
        button_class="btn-secondary",
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


def test_poweraction_rejects_disabled_reason_without_disabled_if():
    with pytest.raises(ValueError, match="disabled_reason requires disabled_if"):
        PowerAction(
            text="Preview",
            url_name="sample:book-detail",
            disabled_reason="get_preview_disabled_reason",
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
