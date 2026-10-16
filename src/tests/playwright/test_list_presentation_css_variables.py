"""Browser coverage for downstream DaisyUI list presentation variables."""

import pytest
from pytest import approx

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect


pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]


def test_list_presentation_variables_can_be_overridden_from_head(
    page, books_url, sample_books
):
    """DaisyUI list spacing variables should inherit from app CSS and list wrappers."""
    del sample_books
    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    cell = page.locator(".pc-list-table > tbody > tr > td").first
    action_group = page.locator(".pc-row-actions-desktop").first
    icon_button = action_group.locator(".pc-row-action-icon-button").first
    dropdown_trigger = action_group.locator(".pc-row-actions-trigger").first
    expect(cell).to_be_visible()
    expect(action_group).to_be_visible()
    expect(icon_button).to_be_visible()
    expect(dropdown_trigger).to_be_visible()

    default_values = page.evaluate(
        """
        () => {
            const cell = document.querySelector('.pc-list-table > tbody > tr > td');
            const actions = document.querySelector('.pc-row-actions-desktop');
            const icon = actions.querySelector('.pc-row-action-icon-button');
            const trigger = actions.querySelector('.pc-row-actions-trigger');
            return {
                cellPadding: parseFloat(getComputedStyle(cell).paddingTop),
                cellFontSize: parseFloat(getComputedStyle(cell).fontSize),
                gap: parseFloat(getComputedStyle(actions).gap),
                iconPadding: parseFloat(getComputedStyle(icon).paddingLeft),
                triggerPadding: parseFloat(getComputedStyle(trigger).paddingLeft),
                rootFontSize: parseFloat(getComputedStyle(document.documentElement).fontSize),
            };
        }
        """
    )
    assert default_values["cellPadding"] == approx(
        default_values["cellFontSize"] * 0.15, abs=0.01
    ), f"Table cells should retain their 0.15em vertical padding by default: {default_values}"
    assert default_values["gap"] == approx(
        default_values["rootFontSize"] * 0.125, abs=0.01
    ), f"Row actions should retain their 0.125rem gap by default: {default_values}"
    assert default_values["iconPadding"] == approx(
        default_values["rootFontSize"] * 0.25, abs=0.01
    ), f"Row-action icon buttons should retain their 0.25rem padding by default: {default_values}"
    assert default_values["triggerPadding"] == approx(
        default_values["rootFontSize"] * 0.25, abs=0.01
    ), f"The dropdown trigger should retain its 0.25rem padding by default: {default_values}"

    page.add_style_tag(
        content="""
        :root {
            --pc-list-cell-padding-block: 7px;
            --pc-row-actions-gap: 9px;
            --pc-row-action-padding-inline: 11px;
        }
        """
    )

    root_values = page.evaluate(
        """
        () => {
            const cell = document.querySelector('.pc-list-table > tbody > tr > td');
            const actions = document.querySelector('.pc-row-actions-desktop');
            const icon = actions.querySelector('.pc-row-action-icon-button');
            const trigger = actions.querySelector('.pc-row-actions-trigger');
            return {
                cell: getComputedStyle(cell).paddingTop,
                gap: getComputedStyle(actions).gap,
                iconPadding: getComputedStyle(icon).paddingLeft,
                triggerPadding: getComputedStyle(trigger).paddingLeft,
            };
        }
        """
    )
    assert root_values == {
        "cell": "7px",
        "gap": "9px",
        "iconPadding": "11px",
        "triggerPadding": "11px",
    }, f"Head stylesheet values should override DaisyUI list defaults: {root_values}"

    page.add_style_tag(
        content="""
        [data-powercrud-object-list="true"] {
            --pc-list-cell-padding-block: 5px;
            --pc-row-actions-gap: 6px;
            --pc-row-action-padding-inline: 8px;
        }
        """
    )
    scoped_values = page.evaluate(
        """
        () => {
            const cell = document.querySelector('.pc-list-table > tbody > tr > td');
            const actions = document.querySelector('.pc-row-actions-desktop');
            const icon = actions.querySelector('.pc-row-action-icon-button');
            const trigger = actions.querySelector('.pc-row-actions-trigger');
            return {
                cell: getComputedStyle(cell).paddingTop,
                gap: getComputedStyle(actions).gap,
                iconPadding: getComputedStyle(icon).paddingLeft,
                triggerPadding: getComputedStyle(trigger).paddingLeft,
            };
        }
        """
    )
    assert scoped_values == {
        "cell": "5px",
        "gap": "6px",
        "iconPadding": "8px",
        "triggerPadding": "8px",
    }, f"List-scoped values should override page defaults: {scoped_values}"
