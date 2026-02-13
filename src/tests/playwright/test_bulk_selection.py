import re

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def test_bulk_selection_toggle(page, books_url, sample_books):
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    checkbox = page.locator("input.row-select-checkbox").first
    expect(checkbox).to_be_visible()
    checkbox.check()

    # HTMX briefly duplicates the container during swaps, so always pin to the first match.
    bulk_container = page.locator("#bulk-actions-container").first
    expect(bulk_container).to_be_visible()
    expect(page.locator("#selected-items-counter")).to_have_text("1")

    bulk_container.locator("button", has_text="Clear Selection").click()

    expect(page.locator("#selected-items-counter")).to_have_text("0")
    expect(page.locator("#bulk-actions-container").first).to_have_class(
        re.compile(r"\bhidden\b")
    )
