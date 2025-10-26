import re
from uuid import uuid4

import pytest
from playwright.sync_api import expect

from sample.models import Book

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def test_create_book_via_modal(page, books_url, sample_author):
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    expect(page.get_by_role("heading", name=re.compile("book", re.I))).to_be_visible()

    create_link = page.get_by_role("link", name=re.compile("create", re.I))
    expect(create_link).to_be_visible()
    create_link.click()

    modal = page.locator("#powercrudBaseModal")
    form = None
    if modal.count() and modal.is_visible():
        modal_content = modal.locator("#powercrudModalContent")
        form = modal_content.locator("form")
        expect(form).to_be_visible()
    else:
        page.wait_for_url(re.compile(r"/sample/bigbook/(new|create)/"))
        form = page.locator("form").first

    title = f"Playwright Title {uuid4().hex[:6]}"
    isbn = f"978{uuid4().hex[:10]}"

    form.locator("input[name='title']").fill(title)
    form.locator("select[name='author']").select_option(str(sample_author.pk))
    form.locator("input[name='published_date']").fill("2025-01-01")
    form.locator("input[name='isbn']").fill(isbn)
    form.locator("input[name='pages']").fill("321")
    description = form.locator("textarea[name='description']")
    if description.count() > 0:
        description.fill("Created via Playwright")

    form.get_by_role("button", name=re.compile("save", re.I)).click()

    if modal.count():
        expect(modal).not_to_be_visible()
        page.wait_for_load_state("networkidle")

    expect(page.locator("table")).to_contain_text(title)

    assert Book.objects.filter(title=title, author=sample_author).exists()
