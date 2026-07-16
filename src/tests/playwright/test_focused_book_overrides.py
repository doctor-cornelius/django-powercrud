"""Browser coverage for the sample's focused Book template overrides."""

import re
from datetime import date

import pytest

pytest.importorskip("playwright.sync_api")
from django.conf import settings
from playwright.sync_api import expect

from sample.models import Book


FOCUSED_PRESENTATION = "Standard DaisyUI + Book overrides"

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.skipif(
        getattr(settings, "SAMPLE_PRESENTATION", None) != FOCUSED_PRESENTATION,
        reason="Focused-override browser proof runs only under focused settings.",
    ),
]


def _assert_focused_components(page):
    """Assert that every agreed focused component is present without local scripts."""
    expect(
        page.locator('[data-sample-focused-component="list-actions"]')
    ).to_be_visible()
    expect(
        page.locator('#filterToggleBtn[data-sample-focused-component="filter-trigger"]')
    ).to_be_visible()
    expect(
        page.locator(
            '#filtered_results thead[data-sample-focused-component="table-header"]'
        )
    ).to_be_visible()
    expect(
        page.locator(
            '[data-powercrud-pagination="true"][data-sample-focused-component="pagination"]'
        )
    ).to_be_visible()
    expect(page.locator('[data-sample-focused-component] script')).to_have_count(0)


def test_focused_book_overrides_survive_htmx_sorting_and_pagination(
    page, books_url, sample_author, sample_books
):
    """Focused Book templates should survive list swaps using the shared runtime."""
    del sample_books
    for number in range(7):
        Book.objects.create(
            title=f"Focused Browser Book {number}",
            author=sample_author,
            published_date=date(2024, 5, number + 1),
            bestseller=False,
            isbn=f"978000001{number:04d}",
            pages=200 + number,
            description="Created to exercise focused Book template overrides.",
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

    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")
    _assert_focused_components(page)

    title_header = page.get_by_role("columnheader").filter(has_text="Title").first
    with page.expect_request(
        lambda request: request.headers.get("x-filter-sort-request") == "true"
    ):
        title_header.dispatch_event("click")
    expect(page).to_have_url(re.compile(r"[?&]sort=title(?:&|$)"))
    _assert_focused_components(page)

    pagination = page.get_by_role("navigation", name=re.compile("page navigation", re.I))
    with page.expect_request(
        lambda request: request.headers.get("x-filter-sort-request") == "true"
    ):
        pagination.get_by_role("link", name="Next", exact=True).click()
    expect(page).to_have_url(re.compile(r"[?&]page=2(?:&|$)"))
    _assert_focused_components(page)

    assert not console_errors, (
        "Focused Book list interactions should not emit browser console errors: "
        f"{console_errors}"
    )
    assert not page_errors, (
        "Focused Book list interactions should not emit page errors: "
        f"{page_errors}"
    )
