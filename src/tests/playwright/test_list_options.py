"""Playwright coverage for the list-options column chooser."""

from __future__ import annotations

import re

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def open_column_chooser(page):
    """Open the compact list-column chooser."""

    trigger = page.locator("[data-powercrud-list-columns='true'] summary")
    expect(trigger).to_be_visible()
    trigger.click()
    panel = page.locator("[data-powercrud-list-columns='true'] .dropdown-content")
    expect(panel).to_be_visible()
    return panel


def test_book_list_column_chooser_saves_and_resets_columns(
    page, books_url, sample_books, sample_genre
):
    """Anonymous users should be able to save current columns and reset to defaults."""

    sample_books[0].genres.add(sample_genre)

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    trigger = page.locator("[data-powercrud-list-columns='true'] summary")
    expect(trigger).to_contain_text(re.compile(r"Cols\s+9/12"))
    expect(page.locator("td[data-field-name='isbn']").first).to_be_visible()
    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='uneditable_field']")).to_have_count(0)

    panel = open_column_chooser(page)
    expect(panel.get_by_text("* = Default")).to_be_visible()
    panel.locator("input[name='visible_columns'][value='uneditable_field']").check()
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        panel.get_by_role("button", name="Save").click()
    expect(trigger).to_contain_text(re.compile(r"Cols\s+10/12"))
    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='genres']").first).to_contain_text(
        sample_genre.name
    )
    expect(page.locator("td[data-field-name='uneditable_field']").first).to_be_visible()

    page.reload()
    page.wait_for_load_state("networkidle")
    expect(page.locator("td[data-field-name='uneditable_field']").first).to_be_visible()

    panel = open_column_chooser(page)
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        panel.get_by_role("button", name="Reset").click()
    expect(trigger).to_contain_text(re.compile(r"Cols\s+9/12"))
    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='uneditable_field']")).to_have_count(0)
    expect(page.locator("td[data-field-name='isbn']").first).to_be_visible()


test_book_list_column_chooser_saves_and_resets_columns = pytest.mark.playwright_smoke(
    test_book_list_column_chooser_saves_and_resets_columns
)


def test_book_list_column_chooser_guards_last_visible_column(
    page, books_url, sample_books
):
    """Users should not be able to uncheck the final visible data column."""

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    panel = open_column_chooser(page)
    checked_values = panel.locator(
        "input[name='visible_columns'][type='checkbox']:checked"
    ).evaluate_all("(elements) => elements.map((element) => element.value)")
    assert "title" in checked_values, (
        "The default BookCRUDView columns should include title so the last-column guard can be exercised."
    )

    for value in checked_values:
        if value != "title":
            panel.locator(f"input[name='visible_columns'][value='{value}']").uncheck()

    title_checkbox = panel.locator("input[name='visible_columns'][value='title']")
    expect(title_checkbox).to_be_checked()
    expect(title_checkbox).to_have_attribute("aria-disabled", "true")
    title_checkbox.click(force=True)
    expect(title_checkbox).to_be_checked()


def test_book_list_column_controls_fit_table_or_viewport(
    page, books_url, sample_books
):
    """The right-aligned view controls should not overshoot the table/page edge."""

    page.set_viewport_size({"width": 640, "height": 720})

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    metrics = page.evaluate(
        """
        () => {
            const controls = document.querySelector('[data-powercrud-view-controls]');
            const table = document.querySelector('#filtered_results table');
            const controlsRect = controls.getBoundingClientRect();
            const tableRect = table.getBoundingClientRect();
            const viewportRight = document.documentElement.clientWidth;
            return {
                controlsRight: controlsRect.right,
                expectedRight: Math.min(tableRect.right, viewportRight),
            };
        }
        """
    )
    assert metrics["controlsRight"] <= metrics["expectedRight"] + 2, (
        "View controls should align within the narrower of the table edge or viewport edge."
    )

    panel = open_column_chooser(page)
    panel_box = panel.bounding_box()
    assert panel_box is not None, "Column chooser panel should have a rendered box."
    assert panel_box["x"] >= -2, "Column chooser panel should not spill off the left viewport edge."
    assert panel_box["x"] + panel_box["width"] <= 642, (
        "Column chooser panel should not spill off the right viewport edge."
    )

    page.get_by_role("button", name=re.compile("filters", re.I)).click()
    add_filter_container = page.locator("#filterCollapse [data-powercrud-add-filter-container]")
    expect(add_filter_container).to_be_visible()
    expect(page.locator("[data-powercrud-filter-toolbar] [data-powercrud-add-filter-container]")).to_have_count(0)

    filter_panel_box = page.locator("#filterCollapse").bounding_box()
    assert filter_panel_box is not None, "Expanded filter panel should have a rendered box."
    panel_metrics = page.evaluate(
        """
        () => {
            const panel = document.querySelector('#filterCollapse');
            const table = document.querySelector('#filtered_results table');
            const panelRect = panel.getBoundingClientRect();
            const tableRect = table.getBoundingClientRect();
            const viewportRight = document.documentElement.clientWidth;
            return {
                panelRight: panelRect.right,
                expectedRight: Math.min(tableRect.right, viewportRight),
            };
        }
        """
    )
    assert panel_metrics["panelRight"] <= panel_metrics["expectedRight"] + 2, (
        "Expanded filter panel should align within the narrower of the table edge or viewport edge."
    )


def test_book_list_wrapped_view_controls_align_left(
    page, books_url, sample_books
):
    """Wrapped view controls should align left instead of hanging from the right edge."""

    page.set_viewport_size({"width": 760, "height": 720})

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    page.evaluate(
        """
        () => {
            const actionControls = document.querySelector('[data-powercrud-action-controls]');
            const extraButton = document.createElement('a');
            extraButton.href = '#';
            extraButton.className = 'btn btn-primary';
            extraButton.textContent = 'Artificially wide toolbar action';
            actionControls.appendChild(extraButton);
            window.dispatchEvent(new Event('resize'));
        }
        """
    )
    page.wait_for_function(
        """
        () => document
            .querySelector('[data-powercrud-list-toolbar]')
            ?.getAttribute('data-powercrud-toolbar-wrapped') === 'true'
        """
    )
    metrics = page.evaluate(
        """
        () => {
            const toolbar = document.querySelector('[data-powercrud-list-toolbar]');
            const controls = document.querySelector('[data-powercrud-view-controls]');
            const toolbarRect = toolbar.getBoundingClientRect();
            const controlsRect = controls.getBoundingClientRect();
            return {
                toolbarLeft: toolbarRect.left,
                controlsLeft: controlsRect.left,
            };
        }
        """
    )
    assert abs(metrics["controlsLeft"] - metrics["toolbarLeft"]) <= 2, (
        "Wrapped view controls should align with the left edge of the list toolbar."
    )
