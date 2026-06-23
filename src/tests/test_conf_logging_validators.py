import pytest
from django.test import override_settings

from powercrud.conf import get_powercrud_setting, DEFAULTS
from powercrud.logging import get_logger, BASE_LOGGER_NAME
from powercrud.validators import PowerCRUDMixinValidator


def test_get_powercrud_setting_prefers_user_value():
    with override_settings(
        POWERCRUD_SETTINGS={"TAILWIND_SAFELIST_JSON_LOC": "custom/path"}
    ):
        assert get_powercrud_setting("TAILWIND_SAFELIST_JSON_LOC") == "custom/path"


def test_get_powercrud_setting_falls_back_to_default():
    with override_settings(POWERCRUD_SETTINGS={}):
        assert get_powercrud_setting("CACHE_NAME") == DEFAULTS["CACHE_NAME"]


def test_get_powercrud_setting_uses_bulk_selection_cap_default():
    with override_settings(POWERCRUD_SETTINGS={}):
        assert get_powercrud_setting("BULK_MAX_SELECTED_RECORDS") == 1000, (
            "PowerCRUD should default BULK_MAX_SELECTED_RECORDS to 1000 when the setting is omitted."
        )


def test_get_powercrud_setting_allows_explicit_default_override():
    with override_settings(POWERCRUD_SETTINGS={}):
        assert get_powercrud_setting("UNKNOWN_KEY", default="fallback") == "fallback"


def test_get_logger_uses_namespaced_children():
    logger = get_logger("module.submodule")
    assert logger.name == f"{BASE_LOGGER_NAME}.module.submodule"
    root_logger = get_logger()
    assert root_logger.name == BASE_LOGGER_NAME


def test_validator_rejects_non_string_fields():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(fields=[123])


def test_validator_requires_target_for_htmx():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(use_htmx=True, default_htmx_target=None)


def test_validator_accepts_valid_payload():
    validator = PowerCRUDMixinValidator(
        namespace="sample",
        templates_path="powercrud/daisyUI",
        base_template_path="powercrud/base.html",
        view_help={
            "summary": "About this screen",
            "details": "Use this screen to review active records.",
            "color": "info",
            "min_width": "36rem",
        },
        view_help_default_color="neutral",
        view_help_min_width="42rem",
        use_crispy=False,
        fields=["title"],
        properties=["isbn"],
        exclude=[],
        properties_exclude=[],
        detail_fields=["title"],
        detail_exclude=[],
        detail_properties=["isbn"],
        detail_properties_exclude=[],
        use_modal=False,
        modal_id="modal",
        modal_target="target",
        modal_classes="modal modal-bottom sm:modal-middle",
        modal_box_classes="modal-box w-11/12 max-w-4xl",
        modal_body_classes="py-6",
        bulk_modal_box_classes="modal-box w-11/12 max-w-6xl",
        use_htmx=True,
        default_htmx_target="#content",
        hx_trigger={"refresh": True},
        form_fields=["title"],
        form_fields_exclude=["isbn"],
        table_pixel_height_other_page_elements=0,
        table_max_height=50,
        table_max_col_width=20,
    )
    assert validator.hx_trigger == {"refresh": True}
    assert validator.modal_box_classes == "modal-box w-11/12 max-w-4xl", (
        "Modal class settings should be valid PowerCRUD configuration options."
    )
    assert validator.view_help == {
        "summary": "About this screen",
        "details": "Use this screen to review active records.",
        "default_open": False,
        "color": "info",
        "min_width": "36rem",
    }, "View help should normalize an omitted default_open value to False."
    assert validator.view_help_default_color == "neutral", (
        "View help should accept daisyUI semantic default colors."
    )
    assert validator.view_help_min_width == "42rem", (
        "View help should accept a safe default minimum width."
    )


def test_validator_accepts_open_view_help():
    validator = PowerCRUDMixinValidator(
        view_help={
            "summary": "About this screen",
            "details": "Review active records.\n\nUse bulk actions carefully.",
            "default_open": True,
            "color": "#0ea5e9",
        }
    )

    assert validator.view_help["default_open"] is True, (
        "The validator should preserve an explicit view_help default_open=True."
    )
    assert validator.view_help["color"] == "#0ea5e9", (
        "The validator should preserve a valid hex view_help color override."
    )


@pytest.mark.parametrize(
    "view_help",
    [
        {},
        {"details": "Useful help."},
        {"summary": "About"},
        {"summary": "   ", "details": "Useful help."},
        {"summary": "About", "details": "   "},
        {"summary": "About", "details": "Useful help.", "tone": "info"},
        {"summary": "About", "details": "Useful help.", "default_open": "yes"},
        {"summary": "About", "details": "Useful help.", "color": "magenta"},
        {"summary": "About", "details": "Useful help.", "color": "rgb(1, 2, 3)"},
        {"summary": "About", "details": "Useful help.", "min_width": "calc(100%)"},
    ],
)
def test_validator_rejects_invalid_view_help(view_help):
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(view_help=view_help)


@pytest.mark.parametrize("color", ["base", "primary", "info", "#abc", "#aabbcc"])
def test_validator_accepts_view_help_default_colors(color):
    validator = PowerCRUDMixinValidator(view_help_default_color=color)

    assert validator.view_help_default_color == color.lower(), (
        "View help should accept base, daisyUI semantic, and hex default colors."
    )


@pytest.mark.parametrize("color", ["magenta", "rgb(1, 2, 3)", ""])
def test_validator_rejects_invalid_view_help_default_color(color):
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(view_help_default_color=color)


@pytest.mark.parametrize("min_width", ["32rem", "640px", "48ch", "80%"])
def test_validator_accepts_view_help_min_width(min_width):
    validator = PowerCRUDMixinValidator(view_help_min_width=min_width)

    assert validator.view_help_min_width == min_width, (
        "View help should accept safe CSS size values for the minimum width."
    )


@pytest.mark.parametrize("min_width", ["calc(100% - 1rem)", "wide", ""])
def test_validator_rejects_invalid_view_help_min_width(min_width):
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(view_help_min_width=min_width)


def test_validator_accepts_list_cell_link_default_open_in():
    validator = PowerCRUDMixinValidator(list_cell_link_default_open_in="modal")

    assert validator.list_cell_link_default_open_in == "modal", (
        "The validator should accept supported list-cell link default opening modes."
    )


def test_validator_defaults_list_cell_link_default_open_in_to_new():
    validator = PowerCRUDMixinValidator()

    assert validator.list_cell_link_default_open_in == "new", (
        "Omitted list_cell_link_default_open_in should validate to the package default new browser context."
    )


def test_validator_defaults_paginate_by_to_package_page_size():
    validator = PowerCRUDMixinValidator()

    assert validator.paginate_by == 25, (
        "Omitted paginate_by should validate to PowerCRUD's package default page size."
    )


def test_validator_rejects_invalid_list_cell_link_default_open_in():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(list_cell_link_default_open_in="popup")


def test_validator_rejects_bad_hx_trigger():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(use_htmx=False, hx_trigger={1: "value"})


def test_validator_rejects_bad_form_fields():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(form_fields=[1, 2, 3])


def test_validator_rejects_invalid_bulk_fields():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(bulk_fields=[123])


def test_validator_rejects_invalid_dropdown_sort_options():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(dropdown_sort_options={"author": 1})


def test_validator_accepts_dropdown_sort_options():
    validator = PowerCRUDMixinValidator(
        namespace="sample",
        templates_path="powercrud/daisyUI",
        base_template_path="powercrud/base.html",
        use_crispy=False,
        fields=["title"],
        properties=["isbn"],
        exclude=[],
        properties_exclude=[],
        detail_fields=["title"],
        detail_exclude=[],
        detail_properties=["isbn"],
        detail_properties_exclude=[],
        use_modal=False,
        modal_id="modal",
        modal_target="target",
        use_htmx=False,
        form_fields=["title"],
        form_fields_exclude=[],
        table_pixel_height_other_page_elements=0,
        table_max_height=50,
        table_max_col_width=20,
        dropdown_sort_options={"author": "-name"},
    )
    assert validator.dropdown_sort_options == {"author": "-name"}


def test_validator_rejects_invalid_column_sort_fields_override():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(column_sort_fields_override={"author": 1})


def test_validator_accepts_column_sort_fields_override():
    validator = PowerCRUDMixinValidator(
        column_sort_fields_override={"author": "author__name"},
    )
    assert validator.column_sort_fields_override == {"author": "author__name"}


def test_validator_accepts_show_bulk_selection_meta_toggle():
    validator = PowerCRUDMixinValidator(show_bulk_selection_meta=False)
    assert validator.show_bulk_selection_meta is False, (
        "Validator should accept show_bulk_selection_meta boolean toggles for view configuration."
    )


def test_validator_rejects_invalid_extra_actions_mode():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(extra_actions_mode="menu")


def test_validator_accepts_extra_actions_mode():
    validator = PowerCRUDMixinValidator(extra_actions_mode="dropdown")
    assert validator.extra_actions_mode == "dropdown", (
        "Validator should accept the dropdown extra-actions rendering mode for row action overflow."
    )


def test_validator_accepts_extra_actions_dropdown_upward_bottom_rows():
    validator = PowerCRUDMixinValidator(
        extra_actions_dropdown_open_upward_bottom_rows=0
    )
    assert validator.extra_actions_dropdown_open_upward_bottom_rows == 0, (
        "Validator should accept a zero bottom-row threshold so projects can disable upward-opening dropdowns."
    )


def test_validator_rejects_negative_extra_actions_dropdown_upward_bottom_rows():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(extra_actions_dropdown_open_upward_bottom_rows=-1)


def test_validator_rejects_invalid_filter_null_fields_exclude():
    """Reject non-string entries for nullable-filter exclusions."""
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(filter_null_fields_exclude=[123])


def test_validator_accepts_filter_null_fields_exclude():
    """Accept string field names for nullable-filter exclusions."""
    validator = PowerCRUDMixinValidator(filter_null_fields_exclude=["birth_date"])
    assert (
        validator.filter_null_fields_exclude == ["birth_date"]
    ), "Validator should preserve string field names for filter_null_fields_exclude."


def test_validator_rejects_invalid_field_queryset_dependencies():
    with pytest.raises(ValueError):
        PowerCRUDMixinValidator(field_queryset_dependencies={"genres": "author"})


def test_validator_accepts_field_queryset_dependencies():
    validator = PowerCRUDMixinValidator(
        field_queryset_dependencies={
            "genres": {
                "depends_on": ["author"],
                "filter_by": {"authors": "author"},
            }
        }
    )
    assert validator.field_queryset_dependencies == {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
        }
    }, "Validator should preserve declarative field queryset dependency mappings."


def test_validator_accepts_static_only_field_queryset_dependencies():
    validator = PowerCRUDMixinValidator(
        field_queryset_dependencies={
            "author": {
                "static_filters": {"name__startswith": "A"},
                "order_by": "name",
            }
        }
    )
    assert validator.field_queryset_dependencies == {
        "author": {
            "static_filters": {"name__startswith": "A"},
            "order_by": "name",
        }
    }, "Validator should preserve static-only field queryset dependency mappings."


def test_validator_accepts_searchable_selects_toggle():
    validator = PowerCRUDMixinValidator(searchable_selects=False)
    assert (
        validator.searchable_selects is False
    ), "Validator should accept searchable_selects boolean toggles for view configuration."
