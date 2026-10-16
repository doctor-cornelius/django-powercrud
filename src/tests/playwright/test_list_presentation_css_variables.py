"""Browser coverage for pack-owned list presentation variables."""

import pytest
from django.conf import settings
from pytest import approx

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect


pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]

BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def uses_bootstrap_pack() -> bool:
    """Return whether the active browser settings select Bootstrap 5."""
    return settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR


def test_list_presentation_variables_can_be_overridden_from_head(
    page, books_url, sample_books
):
    """Pack defaults and head or list-scoped variable overrides should work."""
    del sample_books
    bootstrap = uses_bootstrap_pack()
    cell_selector = (
        '[data-powercrud-object-list="true"] .table-responsive > .table '
        '> tbody > tr > td'
        if bootstrap
        else ".pc-list-table > tbody > tr > td"
    )
    header_selector = (
        '[data-powercrud-object-list="true"] .table-responsive > .table thead th'
        if bootstrap
        else ".pc-list-table > thead > tr > th"
    )
    filter_control_selector = (
        "#filter-form .pc-bootstrap-filter-field-shell .form-control"
        if bootstrap
        else "#filter-form .filter-field-input input:not([type='checkbox'])"
    )

    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")
    page.locator("[data-powercrud-filter-toggle]").click()
    page.locator("#filter-form").wait_for(state="visible")

    cell = page.locator(cell_selector).first
    header = page.locator(header_selector).first
    action_group = page.locator(".pc-row-actions-desktop").first
    icon_button = action_group.locator(".pc-row-action-icon-button").first
    dropdown_trigger = action_group.locator(".pc-row-actions-trigger").first
    filter_control = page.locator(filter_control_selector).first
    expect(cell).to_be_visible()
    expect(header).to_be_visible()
    expect(action_group).to_be_visible()
    expect(icon_button).to_be_visible()
    expect(dropdown_trigger).to_be_visible()
    expect(filter_control).to_be_visible()

    default_values = page.evaluate(
        """({cellSelector, headerSelector, filterControlSelector, bootstrap}) => {
            const cell = document.querySelector(cellSelector);
            const header = document.querySelector(headerSelector);
            const actions = document.querySelector('.pc-row-actions-desktop');
            const icon = actions.querySelector('.pc-row-action-icon-button');
            const trigger = actions.querySelector('.pc-row-actions-trigger');
            const mobileActions = document.querySelector('.pc-row-actions-mobile');
            const filter = document.querySelector(filterControlSelector);
            const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
            const filterStyle = getComputedStyle(filter);
            const menuItem = actions.querySelector('.pc-row-action-menu-item');
            const textAction = document.createElement('a');
            textAction.className = bootstrap ? 'btn btn-secondary' : 'btn';
            textAction.textContent = 'CSS variable scope probe';
            textAction.dataset.powercrudCssVariableProbe = 'text-action';
            actions.appendChild(textAction);
            const inlineEdit = document.querySelector('.inline-edit-trigger');
            return {
                cellPadding: parseFloat(getComputedStyle(cell).paddingTop),
                cellFontSize: parseFloat(getComputedStyle(cell).fontSize),
                headerPadding: getComputedStyle(header).paddingTop,
                gap: parseFloat(getComputedStyle(actions).gap),
                mobileGap: parseFloat(getComputedStyle(mobileActions).gap),
                iconPadding: parseFloat(getComputedStyle(icon).paddingLeft),
                triggerPadding: parseFloat(getComputedStyle(trigger).paddingLeft),
                filterHeight: parseFloat(bootstrap ? filterStyle.minHeight : filterStyle.height),
                filterFontSize: parseFloat(filterStyle.fontSize),
                rootFontSize,
                menuPadding: menuItem ? getComputedStyle(menuItem).paddingLeft : null,
                textActionPadding: getComputedStyle(textAction).paddingLeft,
                inlineEditPadding: inlineEdit ? getComputedStyle(inlineEdit).paddingRight : null,
            };
        }""",
        {
            "cellSelector": cell_selector,
            "headerSelector": header_selector,
            "filterControlSelector": filter_control_selector,
            "bootstrap": bootstrap,
        },
    )

    cell_default = (
        default_values["rootFontSize"] * 0.2
        if bootstrap
        else default_values["cellFontSize"] * 0.15
    )
    assert default_values["cellPadding"] == approx(cell_default, abs=0.01), (
        "Body cells should retain their pack's vertical padding by default: "
        f"{default_values}"
    )
    assert default_values["gap"] == approx(
        default_values["rootFontSize"] * 0.125, abs=0.01
    ), f"Desktop row actions should retain their 0.125rem gap: {default_values}"
    assert default_values["mobileGap"] == approx(
        default_values["rootFontSize"] * 0.125, abs=0.01
    ), f"Mobile row actions should retain their 0.125rem gap: {default_values}"
    assert default_values["iconPadding"] == approx(
        default_values["rootFontSize"] * 0.25, abs=0.01
    ), f"Icon actions should retain their 0.25rem horizontal padding: {default_values}"
    assert default_values["triggerPadding"] == approx(
        default_values["rootFontSize"] * 0.25, abs=0.01
    ), f"The dropdown trigger should retain its 0.25rem horizontal padding: {default_values}"
    assert default_values["filterHeight"] == approx(
        default_values["rootFontSize"] * 2, abs=0.01
    ), f"Filter controls should retain their 2rem height or minimum height: {default_values}"
    assert default_values["filterFontSize"] == approx(
        default_values["rootFontSize"] * 0.8125, abs=0.01
    ), f"Filter controls should retain their 0.8125rem font size: {default_values}"
    assert default_values["menuPadding"] is not None, (
        f"The row-action menu should expose a menu item for spacing checks: {default_values}"
    )

    page.add_style_tag(
        content="""
        :root {
            --pc-list-cell-padding-block: 7px;
            --pc-row-actions-gap: 9px;
            --pc-row-action-padding-inline: 11px;
            --pc-filter-control-height: 42px;
            --pc-filter-font-size: 15px;
            --pc-inline-icon-buffer: 3ch;
        }
        """
    )
    root_values = page.evaluate(
        """({cellSelector, filterControlSelector, bootstrap}) => {
            const cell = document.querySelector(cellSelector);
            const actions = document.querySelector('.pc-row-actions-desktop');
            const icon = actions.querySelector('.pc-row-action-icon-button');
            const trigger = actions.querySelector('.pc-row-actions-trigger');
            const mobileActions = document.querySelector('.pc-row-actions-mobile');
            const filter = document.querySelector(filterControlSelector);
            const filterStyle = getComputedStyle(filter);
            const menuItem = actions.querySelector('.pc-row-action-menu-item');
            const textAction = actions.querySelector('[data-powercrud-css-variable-probe="text-action"]');
            const inlineEdit = document.querySelector('.inline-edit-trigger');
            return {
                cell: getComputedStyle(cell).paddingTop,
                gap: getComputedStyle(actions).gap,
                mobileGap: getComputedStyle(mobileActions).gap,
                iconPadding: getComputedStyle(icon).paddingLeft,
                triggerPadding: getComputedStyle(trigger).paddingLeft,
                filterHeight: bootstrap ? filterStyle.minHeight : filterStyle.height,
                filterFontSize: filterStyle.fontSize,
                headerPadding: getComputedStyle(document.querySelector('thead th')).paddingTop,
                menuPadding: getComputedStyle(menuItem).paddingLeft,
                textActionPadding: getComputedStyle(textAction).paddingLeft,
                inlineEditBuffer: inlineEdit ? getComputedStyle(inlineEdit).getPropertyValue('--pc-inline-icon-buffer').trim() : null,
                inlineEditPadding: inlineEdit ? getComputedStyle(inlineEdit).paddingRight : null,
            };
        }""",
        {
            "cellSelector": cell_selector,
            "filterControlSelector": filter_control_selector,
            "bootstrap": bootstrap,
        },
    )
    assert root_values["cell"] == "7px", f"Head CSS should set body-cell padding: {root_values}"
    assert root_values["gap"] == "9px" and root_values["mobileGap"] == "9px", (
        f"Head CSS should set desktop and mobile action gaps: {root_values}"
    )
    assert root_values["iconPadding"] == "11px" and root_values["triggerPadding"] == "11px", (
        f"Head CSS should set icon and trigger padding: {root_values}"
    )
    assert root_values["filterHeight"] == "42px" and root_values["filterFontSize"] == "15px", (
        f"Head CSS should set filter control dimensions and typography: {root_values}"
    )
    assert root_values["headerPadding"] == default_values["headerPadding"], (
        f"Body-cell padding must not change header-cell padding: {root_values}"
    )
    assert root_values["menuPadding"] == default_values["menuPadding"], (
        f"Row-action padding must not change menu-item spacing: {root_values}"
    )
    assert root_values["textActionPadding"] == default_values["textActionPadding"], (
        f"Icon-action padding must not change text-action spacing: {root_values}"
    )
    if not bootstrap:
        assert root_values["inlineEditBuffer"] == "3ch", (
            f"Head CSS should override the DaisyUI inline-edit buffer: {root_values}"
        )
        assert float(root_values["inlineEditPadding"].removesuffix("px")) > float(
            default_values["inlineEditPadding"].removesuffix("px")
        ), f"Head CSS should increase the DaisyUI inline-edit icon clearance: {root_values}"

    page.add_style_tag(
        content="""
        [data-powercrud-object-list="true"] {
            --pc-list-cell-padding-block: 5px;
            --pc-row-actions-gap: 6px;
            --pc-row-action-padding-inline: 8px;
            --pc-filter-control-height: 36px;
            --pc-filter-font-size: 14px;
            --pc-inline-icon-buffer: 4ch;
        }
        """
    )
    scoped_values = page.evaluate(
        """({cellSelector, filterControlSelector, bootstrap}) => {
            const cell = document.querySelector(cellSelector);
            const actions = document.querySelector('.pc-row-actions-desktop');
            const icon = actions.querySelector('.pc-row-action-icon-button');
            const trigger = actions.querySelector('.pc-row-actions-trigger');
            const mobileActions = document.querySelector('.pc-row-actions-mobile');
            const filter = document.querySelector(filterControlSelector);
            const filterStyle = getComputedStyle(filter);
            const menuItem = actions.querySelector('.pc-row-action-menu-item');
            const textAction = actions.querySelector('[data-powercrud-css-variable-probe="text-action"]');
            const inlineEdit = document.querySelector('.inline-edit-trigger');
            return {
                cell: getComputedStyle(cell).paddingTop,
                gap: getComputedStyle(actions).gap,
                mobileGap: getComputedStyle(mobileActions).gap,
                iconPadding: getComputedStyle(icon).paddingLeft,
                triggerPadding: getComputedStyle(trigger).paddingLeft,
                filterHeight: bootstrap ? filterStyle.minHeight : filterStyle.height,
                filterFontSize: filterStyle.fontSize,
                menuPadding: getComputedStyle(menuItem).paddingLeft,
                textActionPadding: getComputedStyle(textAction).paddingLeft,
                inlineEditBuffer: inlineEdit ? getComputedStyle(inlineEdit).getPropertyValue('--pc-inline-icon-buffer').trim() : null,
                inlineEditPadding: inlineEdit ? getComputedStyle(inlineEdit).paddingRight : null,
            };
        }""",
        {
            "cellSelector": cell_selector,
            "filterControlSelector": filter_control_selector,
            "bootstrap": bootstrap,
        },
    )
    assert scoped_values["cell"] == "5px", f"List CSS should override body-cell padding: {scoped_values}"
    assert scoped_values["gap"] == "6px" and scoped_values["mobileGap"] == "6px", (
        f"List CSS should override desktop and mobile action gaps: {scoped_values}"
    )
    assert scoped_values["iconPadding"] == "8px" and scoped_values["triggerPadding"] == "8px", (
        f"List CSS should override icon and trigger padding: {scoped_values}"
    )
    assert scoped_values["filterHeight"] == "36px" and scoped_values["filterFontSize"] == "14px", (
        f"List CSS should override filter control dimensions and typography: {scoped_values}"
    )
    assert scoped_values["menuPadding"] == default_values["menuPadding"], (
        f"List-scoped row-action padding must not change menu-item spacing: {scoped_values}"
    )
    assert scoped_values["textActionPadding"] == default_values["textActionPadding"], (
        f"List-scoped icon-action padding must not change text-action spacing: {scoped_values}"
    )
    if not bootstrap:
        assert scoped_values["inlineEditBuffer"] == "4ch", (
            f"List CSS should override the DaisyUI inline-edit buffer: {scoped_values}"
        )
        assert float(scoped_values["inlineEditPadding"].removesuffix("px")) > float(
            root_values["inlineEditPadding"].removesuffix("px")
        ), f"List CSS should increase the DaisyUI inline-edit icon clearance: {scoped_values}"
