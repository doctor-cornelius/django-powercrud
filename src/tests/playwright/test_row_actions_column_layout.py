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


def test_powerfield_books_contrast_all_actions_on_the_sticky_end(
    page, powerfield_books_url, sample_books
):
    """PowerField Books should demonstrate the compact menu at the opposite edge."""
    del sample_books
    page.set_viewport_size({"width": 640, "height": 720})
    page.goto(powerfield_books_url)
    page.wait_for_load_state("networkidle")

    scroll_table_horizontally(page)
    header = page.locator("thead [data-powercrud-row-actions-column='true']")
    expect(header.locator(".sr-only, .visually-hidden")).to_have_text("Actions")

    trigger = page.get_by_role("button", name="Actions", exact=True).first
    trigger.scroll_into_view_if_needed()
    expect(trigger).to_be_in_viewport()
    trigger.click()

    panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(panel).to_be_visible()
    native_actions = panel.locator(
        "[data-powercrud-row-actions-standard-group='true'] a"
    )
    expect(native_actions).to_have_count(3)
    for index in range(3):
        expect(native_actions.nth(index).locator("svg")).to_be_visible()
    native_actions.first.hover()
    expect(page.get_by_role("tooltip").filter(has_text="View")).to_be_visible()
    expect(panel.get_by_role("link", name="Normal Edit", exact=True)).to_be_visible()


def test_start_sticky_actions_remain_usable_with_selection_enabled(
    page, authors_url, sample_author
):
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
    row = page.locator("tbody tr[data-inline-row='true']", has_text=sample_author.name)
    actions_trigger = row.get_by_role("button", name="Actions", exact=True)
    expect(actions_header).to_be_in_viewport()
    expect(actions_trigger).to_be_in_viewport()

    actions_trigger.click()
    panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(panel).to_be_visible()
    assert panel.locator(
        "[data-powercrud-row-actions-standard-group='true'] a"
    ).evaluate_all("links => links.map(link => link.getAttribute('aria-label'))") == [
        "View",
        "Edit",
        "Delete",
    ], "The Author menu should put its permitted native actions in the centred icon row."
    assert panel.locator(
        "[data-powercrud-row-action-kind='extra'] a"
    ).all_inner_texts() == [
        "Home",
        "View Again",
    ], "The Author menu should keep configured extras as labelled rows below the native icon row."

    panel.get_by_role("link", name="View", exact=True).click()
    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    modal.locator("[aria-label='Close modal'], [aria-label='Close']").first.click()
    expect(modal).not_to_be_visible()

    actions_trigger.click()
    panel.get_by_role("link", name="View Again", exact=True).click()
    expect(modal).to_be_visible()
    modal.locator("[aria-label='Close modal'], [aria-label='Close']").first.click()
    expect(modal).not_to_be_visible()

    actions_trigger.click()
    panel.get_by_role("link", name="Delete", exact=True).click()
    expect(modal).to_be_visible()
    expect(modal).to_contain_text("Are you sure you want to delete")


def test_start_sticky_all_actions_return_after_inline_save_and_cancel(
    page, authors_url, sample_author
):
    """Author inline controls and the restored menu should survive HTMX swaps."""
    page.set_viewport_size({"width": 480, "height": 720})
    page.goto(authors_url)
    page.wait_for_load_state("networkidle")

    row = page.locator("tbody tr[data-inline-row='true']", has_text=sample_author.name)
    row.locator("[data-inline-field='name']").click()
    active_row = page.locator("tbody tr[data-inline-active='true']")
    scroll_table_horizontally(page)

    cancel = active_row.locator("[data-inline-cancel]")
    expect(cancel).to_be_in_viewport()
    cancel.click()
    expect(page.locator("tbody tr[data-inline-active='true']")).to_have_count(0)

    row = page.locator("tbody tr[data-inline-row='true']", has_text=sample_author.name)
    row.locator("[data-inline-field='name']").click()
    active_row = page.locator("tbody tr[data-inline-active='true']")
    updated_name = "Inline Unified Actions Author"
    active_row.locator("input[name='name']").fill(updated_name)
    scroll_table_horizontally(page)

    save = active_row.locator("[data-inline-save]")
    expect(save).to_be_in_viewport()
    save.click()
    updated_row = page.locator("tbody tr[data-inline-row='true']", has_text=updated_name)
    expect(updated_row).to_be_visible()
    restored_trigger = updated_row.get_by_role("button", name="Actions", exact=True)
    expect(restored_trigger).to_be_in_viewport()
    restored_trigger.click()
    expect(page.locator("[data-powercrud-row-actions-floating-panel='true']")).to_be_visible()


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
