from __future__ import annotations

from uuid import uuid4
from urllib.parse import urlparse

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import Page, expect

INLINE_ROW_SELECTOR = 'tr[data-inline-row="true"]'
INLINE_ACTIVE_SELECTOR = f'{INLINE_ROW_SELECTOR}[data-inline-active="true"]'

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


@pytest.fixture
def inline_ready_books(sample_books, sample_genre):
    """Ensure each sample book has at least one genre so inline saves can succeed."""
    for book in sample_books:
        book.genres.set([sample_genre])
    return sample_books


def open_books_page(page: Page, books_url: str) -> None:
    page.goto(f"{books_url}?page_size=all")
    page.wait_for_load_state("networkidle")
    expect(page.locator("table[data-inline-enabled='true']")).to_be_visible()


def watch_inline_event(page: Page, event_name: str) -> None:
    page.evaluate(
        """
        (name) => {
            window.__pcInlineEvents = window.__pcInlineEvents || {};
            window.__pcInlineEvents[name] = null;
            document.body.addEventListener(
                name,
                event => {
                    const detail = event.detail && event.detail.value ? event.detail.value : event.detail;
                    window.__pcInlineEvents[name] = detail || {};
                },
                { once: true }
            );
        }
        """,
        event_name,
    )


def wait_for_inline_event(page: Page, event_name: str):
    page.wait_for_function(
        """
        (name) => {
            return (
                window.__pcInlineEvents &&
                Object.prototype.hasOwnProperty.call(window.__pcInlineEvents, name) &&
                window.__pcInlineEvents[name] !== null
            );
        }
        """,
        arg=event_name,
    )
    return page.evaluate(
        "(name) => window.__pcInlineEvents[name]",
        event_name,
    )


def build_inline_row_path(books_url: str, pk: int) -> str:
    parsed = urlparse(books_url)
    base_path = parsed.path.rstrip("/")
    return f"{base_path}/{pk}/inline-row/"


def get_inline_row(page: Page, row_path: str):
    row = page.locator(
        f'{INLINE_ROW_SELECTOR}[data-inline-row-url="{row_path}"]'
    )
    expect(row).to_be_visible()
    return row


def open_inline_row(page: Page, *, row=None, row_index: int = 0, field_name: str = "title"):
    if row is None:
        row = page.locator(INLINE_ROW_SELECTOR).nth(row_index)
    expect(row).to_be_visible()
    trigger = row.locator(f".inline-edit-trigger[data-inline-field='{field_name}']")
    trigger.click(force=True)
    active_row = page.locator(INLINE_ACTIVE_SELECTOR)
    expect(active_row).to_have_count(1, timeout=15000)
    return active_row


def test_inline_edit_happy_path(page: Page, books_url: str, inline_ready_books):
    book = inline_ready_books[0]
    row_path = build_inline_row_path(books_url, book.pk)
    open_books_page(page, books_url)
    watch_inline_event(page, "inline-row-saved")

    active_row = open_inline_row(page, row=get_inline_row(page, row_path))
    new_title = f"Inline Edited {uuid4().hex[:6]}"
    title_input = active_row.locator("input[name='title']")
    title_input.fill(new_title)

    active_row.locator("[data-inline-save]").click()

    payload = wait_for_inline_event(page, "inline-row-saved")
    assert payload.get("pk") == book.pk

    expect(page.locator(INLINE_ACTIVE_SELECTOR)).to_have_count(0)
    display_row = get_inline_row(page, row_path)
    expect(display_row.locator("td[data-field-name='title']")).to_contain_text(new_title)

    book.refresh_from_db()
    assert book.title == new_title


def test_inline_edit_validation_error_recovers(page: Page, books_url: str, inline_ready_books):
    book = inline_ready_books[0]
    row_path = build_inline_row_path(books_url, book.pk)
    open_books_page(page, books_url)
    watch_inline_event(page, "inline-row-error")

    active_row = open_inline_row(page, row=get_inline_row(page, row_path))
    title_input = active_row.locator("input[name='title']")
    title_input.fill("")

    active_row.locator("[data-inline-save]").click()
    error_payload = wait_for_inline_event(page, "inline-row-error")
    assert error_payload.get("pk") == book.pk

    active_row = page.locator(INLINE_ACTIVE_SELECTOR)
    expect(active_row).to_have_count(1)
    expect(active_row.locator(".text-error")).to_contain_text("This field is required")

    recovery_title = f"Recovered Title {uuid4().hex[:6]}"
    title_input = active_row.locator("input[name='title']")
    title_input.fill(recovery_title)

    watch_inline_event(page, "inline-row-saved")
    active_row.locator("[data-inline-save]").click()
    wait_for_inline_event(page, "inline-row-saved")

    expect(page.locator(INLINE_ACTIVE_SELECTOR)).to_have_count(0)
    refreshed_row = get_inline_row(page, row_path)
    expect(refreshed_row.locator("td[data-field-name='title']")).to_contain_text(recovery_title)

    book.refresh_from_db()
    assert book.title == recovery_title


def test_inline_edit_guard_focuses_active_row(page: Page, books_url: str, inline_ready_books):
    assert len(inline_ready_books) >= 2, "Guard test needs at least two rows"

    open_books_page(page, books_url)

    first_book = inline_ready_books[0]
    second_book = inline_ready_books[1]
    first_row_path = build_inline_row_path(books_url, first_book.pk)
    second_row_path = build_inline_row_path(books_url, second_book.pk)

    active_row = open_inline_row(page, row=get_inline_row(page, first_row_path))
    first_row_id = active_row.get_attribute("id")
    assert first_row_id

    second_row = get_inline_row(page, second_row_path)
    trigger = second_row.locator(".inline-edit-trigger[data-inline-field='title']")
    trigger.click()

    expect(page.locator(INLINE_ACTIVE_SELECTOR)).to_have_count(1)
    page.wait_for_function(
        """
        (rowId) => {
            const active = document.activeElement;
            if (!active) {
                return false;
            }
            const host = active.closest('tr[data-inline-row="true"]');
            return Boolean(host && host.id === rowId);
        }
        """,
        arg=first_row_id,
    )

    page.locator(f"#{first_row_id} [data-inline-cancel]").click()
    expect(page.locator(INLINE_ACTIVE_SELECTOR)).to_have_count(0)

    active_row = open_inline_row(page, row=get_inline_row(page, second_row_path))
    second_active_id = active_row.get_attribute("id")
    assert second_active_id and second_active_id != first_row_id
    expect(active_row.locator("input[name='title']")).to_be_visible()
