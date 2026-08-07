"""User-visible coverage for configurable row-actions columns."""

from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]


def scroll_table_horizontally(page, *, to_end: bool = True) -> None:
    """Move the table-owned horizontal scroll surface to a logical extreme."""
    page.locator("[data-powercrud-table-scroll='true']").evaluate(
        "(element, end) => { element.scrollLeft = end ? element.scrollWidth : 0; }",
        to_end,
    )


def test_sticky_end_actions_and_more_menu_remain_usable_after_horizontal_scroll(
    page, books_url, sample_books
):
    del sample_books
    page.set_viewport_size({"width": 640, "height": 720})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    scroll_table_horizontally(page)

    actions_header = page.locator(
        "thead [data-powercrud-row-actions-column='true']"
    )
    more_trigger = page.locator(
        "[data-powercrud-row-actions-trigger='true']"
    ).first
    expect(actions_header).to_be_in_viewport()
    expect(more_trigger).to_be_in_viewport()

    more_trigger.click()
    panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(panel).to_be_visible()
    panel.get_by_text("Normal Edit", exact=True).click()
    expect(page.locator("#powercrudBaseModal")).to_be_visible()


def test_annotated_book_actions_render_between_selection_and_data_columns(
    page, annotated_books_url, sample_books
):
    del sample_books
    page.goto(annotated_books_url)
    page.wait_for_load_state("networkidle")

    first_row = page.locator("tbody tr[data-inline-row='true']").first
    cells = first_row.locator("td")
    expect(cells.nth(0).locator("[data-powercrud-row-select='true']")).to_be_visible()
    expect(cells.nth(1)).to_have_attribute(
        "data-powercrud-row-actions-column", "true"
    )
    expect(cells.nth(2)).to_have_attribute("data-field-name", "title")


def test_start_sticky_actions_remain_usable_with_selection_enabled(
    page, authors_url, sample_author
):
    del sample_author
    page.set_viewport_size({"width": 480, "height": 720})
    page.goto(authors_url)
    page.wait_for_load_state("networkidle")

    assert page.locator("[data-powercrud-row-select='true']").count() > 0, (
        "The Author sample should keep selection enabled beside its start-positioned actions."
    )
    scroll_table_horizontally(page)

    actions_header = page.locator(
        "thead [data-powercrud-row-actions-column='true']"
    )
    action_link = page.locator(
        "tbody [data-powercrud-row-actions-column='true'] a"
    ).first
    expect(actions_header).to_be_in_viewport()
    expect(action_link).to_be_in_viewport()
    action_link.click()
    expect(page.locator("#powercrudBaseModal")).to_be_visible()


def test_inline_save_and_cancel_remain_usable_after_horizontal_scroll(
    page, books_url, sample_books
):
    target_book = sample_books[0]
    page.set_viewport_size({"width": 640, "height": 720})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    row = page.locator("tbody tr[data-inline-row='true']", has_text=target_book.title)
    row.locator("[data-inline-field='title']").click()
    active_row = page.locator("tbody tr[data-inline-active='true']")
    expect(active_row).to_be_visible()
    scroll_table_horizontally(page)

    cancel = active_row.locator("[data-inline-cancel]")
    expect(cancel).to_be_in_viewport()
    cancel.click()
    expect(page.locator("tbody tr[data-inline-active='true']")).to_have_count(0)
    expect(page.locator("tbody tr", has_text=target_book.title)).to_be_visible()

    scroll_table_horizontally(page, to_end=False)
    row = page.locator("tbody tr[data-inline-row='true']", has_text=target_book.title)
    row.locator("[data-inline-field='title']").click()
    active_row = page.locator("tbody tr[data-inline-active='true']")
    updated_title = "Sticky inline action saved"
    active_row.locator("input[name='title']").fill(updated_title)
    scroll_table_horizontally(page)

    save = active_row.locator("[data-inline-save]")
    expect(save).to_be_in_viewport()
    save.click()
    expect(page.locator("tbody tr", has_text=updated_title)).to_be_visible()
