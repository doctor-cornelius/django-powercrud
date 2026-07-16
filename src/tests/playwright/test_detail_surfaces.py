import pytest
from django.conf import settings

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]

BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def detail_heading(page):
    """Return the pack-appropriate full-page detail heading."""
    if settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR:
        return page.get_by_role("heading", level=1)
    return page.locator("h2.card-title")


def test_detail_renders_in_page_and_modal(page, books_url, sample_books):
    """Detail content should render through current-page and modal list links."""
    book = sample_books[0]
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    row = page.locator("tbody tr", has_text=book.title)
    expect(row).to_be_visible()
    row.locator('td[data-field-name="pages"] a').click()

    page.wait_for_url(f"**/bigbook/{book.pk}/")
    expect(detail_heading(page)).to_contain_text(book.title)
    details = page.locator("table") if settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") != BOOTSTRAP_SELECTOR else page.locator("main")
    expect(details).to_contain_text(book.author.name)
    expect(details).to_contain_text(str(book.pages))

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    row = page.locator("tbody tr", has_text=book.title)
    row.locator(
        'td[data-field-name="a_really_long_property_header_for_title"] a'
    ).click()

    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    modal_heading = modal.locator("#powercrudModalContent h2.card-title")
    if settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR:
        modal_heading = modal.locator("#powercrudModalContent")
    expect(modal_heading).to_contain_text(
        book.author.name
    )
    modal_details = modal.locator("#powercrudModalContent table")
    if settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR:
        modal_details = modal.locator("#powercrudModalContent")
    expect(modal_details).to_contain_text(
        book.author.name
    )
