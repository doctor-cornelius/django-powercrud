"""Playwright coverage for the list-options column chooser."""

from __future__ import annotations

import re
from datetime import date

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from sample.models import Book

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def open_column_chooser(page):
    """Open the compact list-column chooser."""

    trigger = page.locator("[data-powercrud-list-columns='true'] summary")
    expect(trigger).to_be_visible()
    trigger.click()
    panel = page.locator("[data-powercrud-list-columns-floating-panel='true']")
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
    expect(trigger).to_contain_text(re.compile(r"Cols\s+9/13"))
    expect(page.locator("td[data-field-name='isbn']").first).to_be_visible()
    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='uneditable_field']")).to_have_count(0)

    panel = open_column_chooser(page)
    expect(panel.get_by_text("* = Default")).to_be_visible()
    panel.locator("input[name='visible_columns'][value='uneditable_field']").check()
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        panel.get_by_role("button", name="Save").click()
    expect(trigger).to_contain_text(re.compile(r"Cols\s+10/13"))
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
    expect(trigger).to_contain_text(re.compile(r"Cols\s+9/13"))
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


def test_book_list_column_chooser_discards_unsaved_draft_on_close(
    page, books_url, sample_books
):
    """Closing the chooser should restore checkbox state to the rendered/saved columns."""

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    panel = open_column_chooser(page)
    uneditable_checkbox = panel.locator(
        "input[name='visible_columns'][value='uneditable_field']"
    )
    expect(uneditable_checkbox).not_to_be_checked()
    uneditable_checkbox.check()
    expect(uneditable_checkbox).to_be_checked()

    page.locator("[data-powercrud-list-columns='true'] summary").click()
    panel = open_column_chooser(page)
    expect(
        panel.locator("input[name='visible_columns'][value='uneditable_field']")
    ).not_to_be_checked()

    isbn_checkbox = panel.locator("input[name='visible_columns'][value='isbn']")
    expect(isbn_checkbox).to_be_checked()
    isbn_checkbox.uncheck()
    expect(isbn_checkbox).not_to_be_checked()

    page.locator("body").click(position={"x": 5, "y": 5})
    panel = open_column_chooser(page)
    expect(panel.locator("input[name='visible_columns'][value='isbn']")).to_be_checked()


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


def test_book_list_wide_table_scroll_stays_inside_table_wrapper(
    page, books_url, sample_books
):
    """Wide-table horizontal scroll should not move the list toolbar or page chrome."""

    page.set_viewport_size({"width": 640, "height": 720})

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    metrics = page.evaluate(
        """
        () => {
            const root = document.querySelector('[data-powercrud-object-list="true"]');
            const toolbar = document.querySelector('[data-powercrud-list-toolbar="true"]');
            const tableWrapper = document.querySelector('#filtered_results .table-max-height');
            const table = tableWrapper?.querySelector('table');
            const rootRectBefore = root.getBoundingClientRect();
            const toolbarRectBefore = toolbar.getBoundingClientRect();
            const tableRectBefore = table.getBoundingClientRect();
            const scrollDelta = Math.min(160, tableWrapper.scrollWidth - tableWrapper.clientWidth);

            tableWrapper.scrollLeft = scrollDelta;

            const rootRectAfter = root.getBoundingClientRect();
            const toolbarRectAfter = toolbar.getBoundingClientRect();
            const tableRectAfter = table.getBoundingClientRect();

            return {
                rootClientWidth: root.clientWidth,
                rootScrollWidth: root.scrollWidth,
                rootLeftBefore: rootRectBefore.left,
                rootLeftAfter: rootRectAfter.left,
                toolbarLeftBefore: toolbarRectBefore.left,
                toolbarLeftAfter: toolbarRectAfter.left,
                tableWrapperClientWidth: tableWrapper.clientWidth,
                tableWrapperScrollLeft: tableWrapper.scrollLeft,
                tableWrapperScrollWidth: tableWrapper.scrollWidth,
                tableLeftBefore: tableRectBefore.left,
                tableLeftAfter: tableRectAfter.left,
            };
        }
        """
    )

    assert metrics["tableWrapperScrollWidth"] > metrics["tableWrapperClientWidth"], (
        f"The table wrapper should own horizontal overflow. Metrics: {metrics}"
    )
    assert metrics["tableWrapperScrollLeft"] > 0, (
        f"The table wrapper should be horizontally scrollable. Metrics: {metrics}"
    )
    assert metrics["rootScrollWidth"] <= metrics["rootClientWidth"] + 2, (
        f"The object-list root should not expose page-level horizontal overflow. Metrics: {metrics}"
    )
    assert abs(metrics["rootLeftAfter"] - metrics["rootLeftBefore"]) <= 1, (
        f"Scrolling the table should not move the object-list root. Metrics: {metrics}"
    )
    assert abs(metrics["toolbarLeftAfter"] - metrics["toolbarLeftBefore"]) <= 1, (
        f"Scrolling the table should not move the list toolbar. Metrics: {metrics}"
    )
    assert metrics["tableLeftAfter"] < metrics["tableLeftBefore"], (
        f"Only the table contents should move when the table wrapper scrolls. Metrics: {metrics}"
    )


def test_book_list_column_chooser_escapes_overflow_wrapper(
    page, books_url, sample_books
):
    """The floating column chooser should not be clipped by an overflow shell."""

    page.set_viewport_size({"width": 900, "height": 640})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    page.evaluate(
        """
        () => {
            const content = document.querySelector('#content');
            content.style.width = '620px';
            content.style.height = '220px';
            content.style.overflow = 'auto';
            content.style.position = 'relative';
        }
        """
    )

    panel = open_column_chooser(page)
    metrics = page.evaluate(
        """
        () => {
            const content = document.querySelector('#content');
            const panel = document.querySelector('[data-powercrud-list-columns-floating-panel="true"]');
            const contentRect = content.getBoundingClientRect();
            const panelRect = panel.getBoundingClientRect();
            const probeX = panelRect.left + (panelRect.width / 2);
            const probeY = Math.min(panelRect.bottom - 8, window.innerHeight - 8);
            const probedElement = document.elementFromPoint(probeX, probeY);
            return {
                contentBottom: contentRect.bottom,
                panelBottom: panelRect.bottom,
                panelContainsProbe: panel.contains(probedElement),
            };
        }
        """
    )

    assert metrics["panelBottom"] > metrics["contentBottom"] + 16, (
        "Column chooser should extend beyond the constrained content wrapper."
    )
    assert metrics["panelContainsProbe"], (
        "Column chooser should remain hit-testable where an overflow wrapper would otherwise clip it."
    )
    expect(panel.get_by_text("Title*", exact=True)).to_be_visible()


def test_book_list_pagination_centres_on_table_width(
    page, books_url, sample_author, sample_books, sample_manager_page
):
    """Pagination controls should stay centered within the rendered table footprint."""

    for idx in range(2, 12):
        Book.objects.create(
            title=f"Pagination Center Book {idx}",
            author=sample_author,
            published_date=date(2024, 5, (idx % 28) + 1),
            bestseller=False,
            isbn=f"97877779{idx:02d}00",
            pages=200 + idx,
            description="Created to exercise pagination positioning",
        )

    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    expect(page.locator("[data-powercrud-pagination='true']")).to_be_visible()
    wide_metrics = page.evaluate(
        """
        () => {
            const table = document.querySelector('#filtered_results table');
            const tableWrapper = document.querySelector('#filtered_results .table-max-height');
            const pagination = document.querySelector('[data-powercrud-pagination="true"]');
            const tableRect = table.getBoundingClientRect();
            const tableWrapperRect = tableWrapper.getBoundingClientRect();
            const paginationRect = pagination.getBoundingClientRect();
            return {
                tableCenter: tableRect.left + (tableRect.width / 2),
                tableWrapperCenter: tableWrapperRect.left + (tableWrapperRect.width / 2),
                paginationCenter: paginationRect.left + (paginationRect.width / 2),
            };
        }
        """
    )
    assert (
        abs(wide_metrics["paginationCenter"] - wide_metrics["tableWrapperCenter"]) <= 4
    ), (
        "Pagination should initially be centered on the visible table wrapper when "
        "the table overflows horizontally."
    )

    panel = open_column_chooser(page)
    checked_values = panel.locator(
        "input[name='visible_columns'][type='checkbox']:checked"
    ).evaluate_all("(elements) => elements.map((element) => element.value)")
    assert "title" in checked_values, (
        "The sample column set should include title for the narrow-table pagination check."
    )
    for value in checked_values:
        if value != "title":
            panel.locator(f"input[name='visible_columns'][value='{value}']").uncheck()

    with page.expect_response(re.compile(r"/sample/bigbook/")):
        panel.get_by_role("button", name="Save").click()
    expect(page.locator("[data-powercrud-list-columns='true'] summary")).to_contain_text(
        re.compile(r"Cols\s+1/13")
    )

    narrow_metrics = page.evaluate(
        """
        () => {
            const table = document.querySelector('#filtered_results table');
            const pagination = document.querySelector('[data-powercrud-pagination="true"]');
            const tableRect = table.getBoundingClientRect();
            const paginationRect = pagination.getBoundingClientRect();
            return {
                tableCenter: tableRect.left + (tableRect.width / 2),
                paginationCenter: paginationRect.left + (paginationRect.width / 2),
            };
        }
        """
    )
    assert abs(narrow_metrics["paginationCenter"] - narrow_metrics["tableCenter"]) <= 4, (
        "Pagination should remain centered on the table after the table narrows."
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

    panel = open_column_chooser(page)
    page.wait_for_function(
        """
        () => document
            .querySelector('[data-powercrud-list-columns="true"]')
            ?.getAttribute('data-powercrud-list-columns-placement') === 'start'
        """
    )
    panel_box = panel.bounding_box()
    assert panel_box is not None, "Wrapped column chooser panel should have a rendered box."
    assert panel_box["x"] >= -2, (
        "Wrapped column chooser panel should flip open to the right instead of spilling off the left viewport edge."
    )
    expect(panel.get_by_text("Title*", exact=True)).to_be_visible()
