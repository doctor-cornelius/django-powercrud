import re

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect


pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def test_row_actions_menu_stays_visible_for_top_and_bottom_rows(
    page, books_url, sample_books
):
    """Keep floating row-action menus fully visible on short pages."""
    del sample_books

    page.goto(f"{books_url}?page_size=2")
    page.wait_for_load_state("networkidle")

    row_action_triggers = page.locator("[data-powercrud-row-actions-trigger='true']")
    expect(row_action_triggers).to_have_count(2)

    for index in range(2):
        row_action_triggers.nth(index).dispatch_event("click")

        floating_panel = page.locator(
            "[data-powercrud-row-actions-floating-panel='true']"
        )
        expect(floating_panel).to_be_visible()
        expect(floating_panel).to_contain_text("Normal Edit")
        expect(floating_panel).to_contain_text("Description Preview")

        panel_box = floating_panel.bounding_box()
        viewport = page.viewport_size

        assert panel_box is not None, (
            f"Expected floating row-actions panel for visible row index {index} to expose a measurable bounding box."
        )
        assert viewport is not None, (
            "Expected Playwright to provide a viewport size so row-actions visibility can be verified."
        )
        assert panel_box["y"] >= -1, (
            "Expected floating row-actions panel for visible row index "
            f"{index} to stay inside the top of the viewport, but its top was {panel_box['y']}."
        )
        assert panel_box["y"] + panel_box["height"] <= viewport["height"] + 1, (
            "Expected floating row-actions panel to stay inside the bottom of the viewport "
            f"for visible row index {index}, but its bottom was {panel_box['y'] + panel_box['height']} while the viewport height was {viewport['height']}."
        )


test_row_actions_menu_stays_visible_for_top_and_bottom_rows = pytest.mark.playwright_smoke(
    test_row_actions_menu_stays_visible_for_top_and_bottom_rows
)


def test_row_actions_floating_panel_modal_action_uses_cloned_trigger_classes(
    page, books_url, sample_books
):
    """A modal action clicked from the cloned floating panel should keep its trigger metadata."""

    target_book = sample_books[0]
    target_book.description = "Description Preview Playwright Body"
    target_book.save(update_fields=["description"])

    page.goto(f"{books_url}?page_size=2")
    page.wait_for_load_state("networkidle")

    page.locator("[data-powercrud-row-actions-trigger='true']").first.dispatch_event("click")
    floating_panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(floating_panel).to_be_visible()
    floating_panel.get_by_role("link", name="Description Preview").click()

    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    expect(modal.locator("#powercrudModalContent")).to_contain_text("Description Preview")
    expect(modal.locator("#powercrudModalContent")).to_contain_text(target_book.description)
    expect(modal.locator("[data-powercrud-modal-box]")).to_have_class(
        re.compile(r"\bmax-w-5xl\b")
    )
    expect(floating_panel).not_to_be_visible()
