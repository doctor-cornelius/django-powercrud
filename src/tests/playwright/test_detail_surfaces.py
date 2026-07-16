import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]


def test_detail_renders_in_page_and_modal(page, books_url, sample_books):
    """Detail content should render through current-page and modal list links."""
    book = sample_books[0]
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    row = page.locator("tbody tr", has_text=book.title)
    expect(row).to_be_visible()
    row.locator('td[data-field-name="pages"] a').click()

    page.wait_for_url(f"**/bigbook/{book.pk}/")
    expect(page.locator("h2.card-title")).to_contain_text(book.title)
    expect(page.locator("table")).to_contain_text(book.author.name)
    expect(page.locator("table")).to_contain_text(str(book.pages))

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    row = page.locator("tbody tr", has_text=book.title)
    row.locator(
        'td[data-field-name="a_really_long_property_header_for_title"] a'
    ).click()

    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    expect(modal.locator("#powercrudModalContent h2.card-title")).to_contain_text(
        book.author.name
    )
    expect(modal.locator("#powercrudModalContent table")).to_contain_text(
        book.author.name
    )
