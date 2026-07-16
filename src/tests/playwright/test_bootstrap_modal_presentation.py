"""Bootstrap-specific modal lifecycle coverage for the selected sample pack."""

from datetime import date
import re

import pytest

pytest.importorskip("playwright.sync_api")
from django.conf import settings
from playwright.sync_api import expect

from sample.models import Book


BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.skipif(
        settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") != BOOTSTRAP_SELECTOR,
        reason="Bootstrap modal presentation coverage requires the Bootstrap settings overlay.",
    ),
]


def test_bootstrap_preview_modal_opens_and_closes_without_browser_errors(
    page, books_url, sample_author
):
    """A legacy DaisyUI modal class must not replace Bootstrap's dialog structure."""
    preview_book = Book.objects.create(
        title="Hidden Preview Bootstrap Modal",
        author=sample_author,
        published_date=date(2025, 1, 1),
        bestseller=False,
        isbn="9780000007001",
        pages=321,
        description="A browser regression fixture for the Bootstrap modal lifecycle.",
    )
    console_errors = []
    page_errors = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    page.get_by_role("link", name=preview_book.title, exact=True).last.click()
    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_have_class(re.compile(r"(?:^|\s)show(?:\s|$)"), timeout=15000)
    expect(modal.locator(".modal-dialog")).to_have_count(1)
    expect(modal.locator("#powercrudModalContent")).to_contain_text(sample_author.name)

    modal.get_by_role("button", name="Close").click()
    expect(modal).not_to_be_visible()
    expect(page.locator("body")).not_to_have_class(
        re.compile(r"(?:^|\s)modal-open(?:\s|$)")
    )
    assert not console_errors, (
        f"Bootstrap preview modal emitted browser console errors: {console_errors}"
    )
    assert not page_errors, (
        f"Bootstrap preview modal emitted page errors: {page_errors}"
    )


def test_bootstrap_modal_uses_the_fragment_operation_heading(
    page, books_url, sample_books, sample_manager_page
):
    """Bootstrap modal chrome must not duplicate the loaded fragment heading."""

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Create book", exact=True).click()

    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    expect(modal.get_by_role("heading", name="Create book", exact=True)).to_be_visible()
    expect(modal.locator(".modal-header .modal-title")).to_have_class(
        re.compile(r"(?:^|\s)visually-hidden(?:\s|$)")
    )
    title_metrics = modal.locator(".modal-header .modal-title").evaluate(
        """element => {
            const rect = element.getBoundingClientRect();
            return {width: rect.width, height: rect.height};
        }"""
    )
    assert title_metrics["width"] <= 1 and title_metrics["height"] <= 1, (
        "The generic Bootstrap modal title must not create a second visible heading. "
        f"Metrics: {title_metrics}"
    )


def test_bootstrap_filter_controls_and_favourites_are_interactive(
    page, books_url, sample_books, sample_manager_page
):
    """Bootstrap list controls should open and enhance their interactive surfaces."""

    del sample_books, sample_manager_page

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    filter_toggle = page.locator("#filterToggleBtn")
    filter_icon = filter_toggle.locator(
        "[data-powercrud-filter-toggle-icon-outline='true']"
    )
    expect(filter_icon).to_be_visible()

    filter_toggle.click()
    add_filter = page.locator("#add-filter-select")
    expect(add_filter).to_be_attached()
    expect(page.locator(".powercrud-bootstrap-tomselect").first).to_be_visible()
    assert add_filter.evaluate("element => Boolean(element.tomselect)"), (
        "The visible Bootstrap add-filter selector should be enhanced with Tom Select."
    )

    favourites_trigger = page.locator(
        "[data-powercrud-filter-favourites-trigger='true']:visible"
    ).first
    favourites_icon = favourites_trigger.locator(
        "[data-powercrud-filter-favourites-icon-outline='true']"
    )
    expect(favourites_icon).to_be_visible()

    favourites_trigger.click(force=True)
    favourites_panel = page.locator(".pc-bootstrap-favourites-panel").last
    expect(favourites_panel).to_be_visible()
