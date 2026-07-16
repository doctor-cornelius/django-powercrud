from urllib.parse import urljoin

import pytest
from django.conf import settings
from django.urls import reverse

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from sample.models import Book

BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def detail_heading(page):
    """Return the pack-appropriate full-page delete heading."""
    if settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR:
        return page.get_by_role("heading", level=1)
    return page.locator("h2.card-title")

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]


def test_delete_renders_and_submits_in_page_and_modal(page, books_url, sample_books):
    """Delete confirmation should work as a full page and through the shared modal."""
    page_book, modal_book = sample_books
    page_delete_url = urljoin(
        books_url,
        reverse("sample:bigbook-delete", kwargs={"pk": page_book.pk}),
    )

    page.goto(page_delete_url)
    expect(page.get_by_text("Are you sure you want to delete")).to_be_visible()
    if settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR:
        expect(page.get_by_text(page_book.title, exact=True)).to_be_visible()
    else:
        expect(detail_heading(page)).to_contain_text(page_book.title)
    page.get_by_role("button", name="Delete").click()

    page.wait_for_url("**/bigbook/")
    expect(page.locator("table")).not_to_contain_text(page_book.title)
    assert not Book.objects.filter(pk=page_book.pk).exists(), (
        "Normal delete submission should remove the selected book."
    )

    row = page.locator("tbody tr", has_text=modal_book.title)
    expect(row).to_be_visible()
    row.get_by_role("link", name="Delete").click()

    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    expect(modal.locator("#powercrudModalContent")).to_contain_text(modal_book.title)
    modal.get_by_role("button", name="Delete").click()

    expect(modal).not_to_be_visible()
    expect(page.locator("body")).not_to_contain_text(modal_book.title)
    expect(page.get_by_text("There are no books. Create one now?")).to_be_visible()
    assert not Book.objects.filter(pk=modal_book.pk).exists(), (
        "Modal HTMX delete submission should remove the selected book."
    )
