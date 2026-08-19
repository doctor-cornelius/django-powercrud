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


def open_inline_row(page, row, *, field_name: str):
    """Open one list row for inline editing through the named field."""
    row.locator(
        f".inline-edit-trigger[data-inline-field='{field_name}']"
    ).click(force=True)
    active_row = page.locator(
        'tbody tr[data-inline-row="true"][data-inline-active="true"]'
    )
    expect(active_row).to_have_count(1, timeout=15000)
    return active_row


def assert_inline_actions_are_contained(active_row, *, expected_position: str) -> None:
    """Assert compact inline actions stay inside their table column."""
    actions_cell = active_row.locator("[data-inline-actions='true']")
    expect(actions_cell).to_have_attribute(
        "data-powercrud-row-actions-position", expected_position
    )
    metrics = actions_cell.evaluate(
        """
        (cell) => {
            const position = cell.dataset.powercrudRowActionsPosition;
            const adjacentCell = position === 'start'
                ? cell.nextElementSibling
                : cell.previousElementSibling;
            const controls = cell.querySelector('.pc-inline-actions-controls');
            const save = cell.querySelector('[data-inline-save]');
            const cancel = cell.querySelector('[data-inline-cancel]');
            const cellBox = cell.getBoundingClientRect();
            const adjacentBox = adjacentCell.getBoundingClientRect();
            const controlsBox = controls.getBoundingClientRect();
            const saveBox = save.getBoundingClientRect();
            const cancelBox = cancel.getBoundingClientRect();
            const tableBox = cell.closest('table').getBoundingClientRect();
            return {
                position,
                adjacentLeft: adjacentBox.left,
                adjacentRight: adjacentBox.right,
                cellLeft: cellBox.left,
                cellRight: cellBox.right,
                cellWidth: cellBox.width,
                controlsLeft: controlsBox.left,
                controlsRight: controlsBox.right,
                saveLeft: saveBox.left,
                saveRight: saveBox.right,
                cancelLeft: cancelBox.left,
                cancelRight: cancelBox.right,
                tableLeft: tableBox.left,
                tableRight: tableBox.right,
            };
        }
        """
    )
    tolerance = 1
    controls_inside_cell = (
        metrics["controlsLeft"] >= metrics["cellLeft"] - tolerance
        and metrics["controlsRight"] <= metrics["cellRight"] + tolerance
        and metrics["saveLeft"] >= metrics["cellLeft"] - tolerance
        and metrics["saveRight"] <= metrics["cellRight"] + tolerance
        and metrics["cancelLeft"] >= metrics["cellLeft"] - tolerance
        and metrics["cancelRight"] <= metrics["cellRight"] + tolerance
    )
    assert controls_inside_cell, (
        "Inline Save and Cancel controls should remain inside their actions cell. "
        f"Metrics: {metrics}"
    )
    assert (
        metrics["cellLeft"] >= metrics["tableLeft"] - tolerance
        and metrics["cellRight"] <= metrics["tableRight"] + tolerance
    ), f"The active actions cell should remain inside the table. Metrics: {metrics}"
    if expected_position == "start":
        assert metrics["controlsRight"] <= metrics["adjacentLeft"] + tolerance, (
            "Start-positioned inline actions should not overlap the following data cell. "
            f"Metrics: {metrics}"
        )
    else:
        assert metrics["controlsLeft"] >= metrics["adjacentRight"] - tolerance, (
            "End-positioned inline actions should not overlap the preceding data cell. "
            f"Metrics: {metrics}"
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


def test_selection_column_remains_visible_and_usable_after_horizontal_scroll(
    page, books_url, sample_books
):
    """Selection should stay pinned at logical start opposite sticky end actions."""
    target_book = sample_books[0]
    page.set_viewport_size({"width": 640, "height": 720})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    scroll_table_horizontally(page)

    select_all = page.locator(
        "thead [data-powercrud-selection-column='true'] [data-powercrud-select-all='true']"
    )
    row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=target_book.title
    )
    row_checkbox = row.locator(
        "[data-powercrud-selection-column='true'] [data-powercrud-row-select='true']"
    )
    end_actions = row.locator("[data-powercrud-row-actions-position='end']")

    expect(select_all).to_be_in_viewport()
    expect(row_checkbox).to_be_in_viewport()
    expect(end_actions).to_be_in_viewport()

    row_checkbox.click()
    expect(row_checkbox).to_be_checked()


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


def test_annotated_book_icon_only_extra_action_retains_accessible_label(
    page, annotated_books_url, sample_books
):
    """The direct dictionary action should render as an icon-only accessible control."""
    target_book = sample_books[0]
    page.goto(annotated_books_url)
    page.wait_for_load_state("networkidle")

    row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=target_book.title
    )
    open_book = row.get_by_role("link", name="Open Book", exact=True)
    expect(open_book).to_have_attribute("aria-label", "Open Book")
    expect(open_book).to_have_attribute("data-powercrud-tooltip", "semantic")
    expect(open_book.locator("svg")).to_be_visible()
    expect(open_book).to_have_text("")


def test_dropdown_mode_collapses_native_and_extra_actions_on_narrow_viewports(
    page, books_url, sample_books
):
    """The desktop extras-only layout should become one all-actions menu."""
    target_book = sample_books[0]
    page.set_viewport_size({"width": 480, "height": 720})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=target_book.title
    )
    desktop_actions = row.locator(
        "[data-powercrud-row-actions-responsive='desktop']"
    )
    mobile_actions = row.locator(
        "[data-powercrud-row-actions-responsive='mobile']"
    )
    expect(desktop_actions).to_be_hidden()
    expect(mobile_actions).to_be_visible()
    expect(mobile_actions.get_by_role("button")).to_have_count(1)

    mobile_actions.get_by_role("button", name="Actions", exact=True).click()
    panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(panel).to_be_visible()
    labels = panel.locator("li > a").all_inner_texts()
    assert labels[:2] == ["View", "Edit"] and labels[-1] == "Delete", (
        "The narrow Book menu should place native View/Edit first and Delete last."
    )
    assert "Normal Edit" in labels, (
        "The narrow Book menu should include extras that remain desktop-menu-only at wider widths."
    )

    panel.get_by_role("link", name="Normal Edit", exact=True).click()
    expect(page.locator("#powercrudBaseModal")).to_be_visible()


def test_button_mode_collapses_pinned_actions_on_narrow_viewports(
    page, profiles_url, sample_profile
):
    """A visible native button should move behind the responsive kebab."""
    page.set_viewport_size({"width": 480, "height": 720})
    page.goto(profiles_url)
    page.wait_for_load_state("networkidle")

    row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=sample_profile.nickname
    )
    expect(
        row.locator("[data-powercrud-row-actions-responsive='desktop']")
    ).to_be_hidden()
    mobile_actions = row.locator(
        "[data-powercrud-row-actions-responsive='mobile']"
    )
    expect(mobile_actions).to_be_visible()

    trigger = mobile_actions.get_by_role("button", name="Actions", exact=True)
    scroll_table_horizontally(page)
    expect(trigger).to_be_in_viewport()
    trigger.click()
    panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(panel).to_be_visible()
    assert panel.locator("li > a").all_inner_texts() == ["Edit"], (
        "Button mode should move its permitted pinned native action into the narrow menu."
    )

    panel.get_by_role("link", name="Edit", exact=True).click()
    expect(page.locator("#powercrudBaseModal")).to_be_visible()


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
    native_actions = panel.locator("[data-powercrud-row-action-kind='standard'] a")
    expect(native_actions).to_have_count(3)
    for index in range(3):
        expect(native_actions.nth(index).locator("svg")).to_be_visible()
    expect(native_actions.first).to_have_text("View")
    normal_edit = panel.get_by_role("link", name="Normal Edit", exact=True)
    expect(normal_edit).to_be_visible()
    expect(normal_edit.locator("svg")).to_be_visible()


def test_inline_actions_stay_inside_configured_table_edge(
    page, powerfield_books_url, annotated_books_url, sample_books
):
    """Both action-column positions should contain Save and Cancel controls."""
    target_book = sample_books[0]
    page.set_viewport_size({"width": 640, "height": 720})
    page.goto(powerfield_books_url)
    page.wait_for_load_state("networkidle")

    row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=target_book.title
    )
    active_row = open_inline_row(page, row, field_name="title")
    scroll_table_horizontally(page)
    assert_inline_actions_are_contained(active_row, expected_position="end")

    active_row.locator("[data-inline-cancel]").click()
    expect(
        page.locator('tbody tr[data-inline-row="true"][data-inline-active="true"]')
    ).to_have_count(0)
    display_row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=target_book.title
    )
    expect(
        display_row.get_by_role("button", name="Actions", exact=True)
    ).to_be_visible()

    page.goto(annotated_books_url)
    page.wait_for_load_state("networkidle")

    row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=target_book.title
    )
    active_row = open_inline_row(page, row, field_name="pages")
    assert_inline_actions_are_contained(active_row, expected_position="start")

    active_row.locator("[data-inline-save]").click()
    expect(
        page.locator('tbody tr[data-inline-row="true"][data-inline-active="true"]')
    ).to_have_count(0)
    display_row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=target_book.title
    )
    expect(
        display_row.get_by_role("link", name="Open Book", exact=True)
    ).to_be_visible()


def test_async_extras_only_dropdown_uses_its_custom_icon_gutter(
    page, async_task_records_url, sample_async_task_record
):
    """An extras-only menu should gain a gutter from its configured custom SVG."""
    page.goto(async_task_records_url)
    page.wait_for_load_state("networkidle")

    row = page.locator(
        "tbody tr[data-inline-row='true']", has_text=sample_async_task_record.task_name
    )
    row.get_by_role("button", name="Actions", exact=True).click()
    panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(panel).to_be_visible()
    action = panel.get_by_role("link", name="View Progress", exact=True)
    expect(action).to_be_visible()
    expect(panel.locator(".pc-row-action-menu-icon")).to_have_count(1)
    expect(action.locator("svg")).to_be_visible()


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
    row_checkbox = row.locator("[data-powercrud-row-select='true']")
    expect(row_checkbox).to_be_in_viewport()

    actions_trigger.click()
    panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(panel).to_be_visible()
    assert panel.locator("li > a").all_inner_texts() == [
        "View",
        "Edit",
        "Home",
        "View Again",
        "Delete",
    ], "The Author menu should keep Delete last in one ordered, labelled action list."

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
