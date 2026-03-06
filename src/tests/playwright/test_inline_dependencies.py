from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Page, expect

from sample.models import Author, Book, Genre

INLINE_ROW_SELECTOR = 'tr[data-inline-row="true"]'
INLINE_ACTIVE_SELECTOR = f'{INLINE_ROW_SELECTOR}[data-inline-active="true"]'

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


@pytest.fixture
def inline_dependency_books(db):
    author_a = Author.objects.create(name="Author Alpha", bio="", birth_date=None)
    author_b = Author.objects.create(name="Author Beta", bio="", birth_date=None)

    genre_a = Genre.objects.create(name="Genre Alpha", description="")
    genre_b = Genre.objects.create(name="Genre Beta", description="")
    author_a.genres.add(genre_a)
    author_b.genres.add(genre_b)

    focus_book = Book.objects.create(
        title="Dependency Focus Book",
        author=author_a,
        published_date=date(2024, 2, 1),
        bestseller=False,
        isbn="9789999900001",
        pages=100,
        description="Inline dependency focus",
    )
    focus_book.genres.set([genre_a])

    Book.objects.create(
        title="Dependency Seed Book",
        author=author_b,
        published_date=date(2024, 2, 2),
        bestseller=False,
        isbn="9789999900002",
        pages=110,
        description="Seeds author->genre mapping",
    ).genres.set([genre_b])

    return {
        "focus_book": focus_book,
        "author_b": author_b,
        "genre_a": genre_a,
        "genre_b": genre_b,
    }


def build_inline_row_path(books_url: str, pk: int) -> str:
    parsed = urlparse(books_url)
    base_path = parsed.path.rstrip("/")
    return f"{base_path}/{pk}/inline-row/"


def open_books_page(page: Page, books_url: str) -> None:
    page.goto(f"{books_url}?page_size=all")
    page.wait_for_load_state("networkidle")
    expect(page.locator("table[data-inline-enabled='true']")).to_be_visible()


def get_inline_row(page: Page, row_path: str):
    row = page.locator(f'{INLINE_ROW_SELECTOR}[data-inline-row-url="{row_path}"]')
    expect(row).to_be_visible()
    return row


def open_inline_row(page: Page, row, field_name: str = "author"):
    row_id = row.get_attribute("id")
    trigger = row.locator(f".inline-edit-trigger[data-inline-field='{field_name}']")
    trigger.click(force=True)
    if row_id:
        swapped_row = page.locator(f"#{row_id}")
        expect(swapped_row.locator("[data-inline-save]")).to_have_count(1, timeout=15000)
        return swapped_row
    active_row = page.locator(INLINE_ACTIVE_SELECTOR)
    expect(active_row).to_have_count(1, timeout=15000)
    return active_row


def test_inline_dependency_refreshes_genre_options_without_save(
    page: Page, books_url: str, inline_dependency_books
):
    focus_book = inline_dependency_books["focus_book"]
    author_b = inline_dependency_books["author_b"]
    genre_a_name = inline_dependency_books["genre_a"].name
    genre_b_name = inline_dependency_books["genre_b"].name
    row_path = build_inline_row_path(books_url, focus_book.pk)

    open_books_page(page, books_url)
    active_row = open_inline_row(page, row=get_inline_row(page, row_path))

    author_select = active_row.locator("select[name='author']")
    ts_wrapper = active_row.locator("select[name='author'] + .ts-wrapper")
    if ts_wrapper.count() > 0:
        author_select.evaluate(
            """
            (el, value) => {
                if (!el.tomselect) {
                    throw new Error("Expected TomSelect instance for inline dependency test.");
                }
                el.tomselect.setValue(String(value));
            }
            """,
            str(author_b.pk),
        )
    else:
        author_select.select_option(str(author_b.pk))

    # Wait until dependency refresh replaces the child select with constrained choices.
    row_id = active_row.get_attribute("id")
    assert row_id, "Active inline row should expose a stable id for dependency refresh assertions."

    page.wait_for_function(
        """
        ({rowId, wanted, unwanted}) => {
            const row = document.getElementById(rowId);
            if (!row) {
                return false;
            }
            const select = row.querySelector('select[name="genres"]');
            if (!select || select.disabled) {
                return false;
            }
            const options = Array.from(select.options).map(option => option.textContent.trim());
            return options.includes(wanted) && !options.includes(unwanted);
        }
        """,
        arg={
            "rowId": row_id,
            "wanted": genre_b_name,
            "unwanted": genre_a_name,
        },
        timeout=15000,
    )

    genre_options = (
        active_row.locator("select[name='genres'] option").all_text_contents()
    )
    option_set = {text.strip() for text in genre_options if text.strip()}
    assert (
        genre_b_name in option_set
    ), "Dependent genre options should include values mapped to the selected author."
    assert (
        genre_a_name not in option_set
    ), "Dependent genre options should exclude values from the previously selected author."
