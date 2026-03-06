import re
from datetime import date

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from sample.models import Author, Book, Genre

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


def test_bulk_edit_refresh_reapplies_active_filters(
    page, books_url, sample_author, sample_genre, sample_books
):
    target_book = sample_books[0]
    target_book.genres.add(sample_genre)

    other_author = Author.objects.create(
        name="Playwright Other Author",
        bio="",
        birth_date=None,
    )
    other_genre = Genre.objects.create(
        name="Playwright Other Genre",
        description="Used to prove filtered refresh stays scoped",
    )
    other_author.genres.add(other_genre)
    other_book = Book.objects.create(
        title="Outside Filter Book",
        author=other_author,
        published_date=date(2024, 2, 1),
        bestseller=False,
        isbn="9785555555500",
        pages=123,
        description="Should disappear once author filter is applied",
    )
    other_book.genres.add(other_genre)

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    author_filter = page.locator("#filter-form select[name='author']")
    author_filter.select_option(str(sample_author.pk))

    page.wait_for_load_state("networkidle")
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)

    checkbox = page.locator("input.row-select-checkbox").first
    checkbox.check()

    bulk_container = page.locator("#bulk-actions-container").first
    expect(bulk_container).to_be_visible()
    bulk_container.get_by_role("link", name=re.compile("bulk edit", re.I)).click()

    modal = page.locator("#powercrudBaseModal")
    form = modal.locator("#bulk-edit-form")
    expect(form).to_be_visible()

    form.locator("input.field-toggle[value='bestseller']").check()
    form.locator("select[name='bestseller']").select_option("true")
    form.get_by_role("button", name=re.compile("apply changes", re.I)).click()

    expect(modal).not_to_be_visible()
    page.wait_for_load_state("networkidle")

    filtered_results = page.locator("#filtered_results")
    expect(filtered_results).to_contain_text(target_book.title)
    expect(filtered_results).not_to_contain_text(other_book.title)

    target_book.refresh_from_db()
    assert (
        target_book.bestseller is True
    ), "Bulk edit should update the filtered record while keeping the filtered list scoped to the active author."
