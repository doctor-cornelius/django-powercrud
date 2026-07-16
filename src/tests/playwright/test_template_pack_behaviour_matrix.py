"""Shared browser behaviour matrix for selectable template packs."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest

pytest.importorskip("playwright.sync_api")
from django.conf import settings
from django.contrib.auth import get_user_model
from playwright.sync_api import expect

from powercrud.contrib.favourites.models import SavedFilterFavourite
from sample.models import Book
from sample.views import BookCRUDView


pytestmark = [pytest.mark.playwright, pytest.mark.django_db]

BOOK_VIEW_KEY = f"{BookCRUDView.__module__}.{BookCRUDView.__name__}"
HTMX_TEST_BUNDLE_PATH = (
    Path(__file__).resolve().parents[3]
    / "node_modules"
    / "htmx.org"
    / "dist"
    / "htmx.min.js"
)
BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def _install_htmx_before_navigation(page) -> None:
    """Make shared HTMX interactions deterministic when the test asset mode omits it."""
    assert HTMX_TEST_BUNDLE_PATH.exists(), (
        f"Expected local HTMX bundle at '{HTMX_TEST_BUNDLE_PATH}'."
    )
    page.add_init_script(path=str(HTMX_TEST_BUNDLE_PATH))


def _ensure_htmx(page) -> None:
    """Inject and process HTMX if the active browser asset mode did not expose it."""
    if page.evaluate("() => Boolean(window.htmx)"):
        return
    page.add_script_tag(path=str(HTMX_TEST_BUNDLE_PATH))
    page.evaluate("() => window.htmx && window.htmx.process(document.body)")
    assert page.evaluate("() => Boolean(window.htmx)"), (
        "The shared browser matrix requires HTMX to execute the public interactions."
    )


def _open_columns(page):
    """Open the presentation-independent list column chooser."""
    trigger = page.locator("[data-powercrud-list-columns='true'] summary")
    expect(trigger).to_be_visible()
    trigger.click()
    panel = page.locator("[data-powercrud-list-columns-floating-panel='true']").last
    expect(panel).to_be_visible()
    return panel


def _open_favourites(page):
    """Open the shared saved-favourites control using its stable runtime hook."""
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_be_visible()
    trigger.click(force=True)
    panel = page.locator("[data-powercrud-filter-favourites-floating-panel='true']").last
    expect(panel).to_be_visible()
    return panel


def _select_favourite(panel, name: str) -> None:
    """Select a favourite through native or Tom Select-backed controls."""
    select = panel.locator("select[name='favourite_id']")
    value = select.evaluate(
        """
        (element, label) => {
            const option = Array.from(element.options).find(
                candidate => candidate.textContent.trim() === label
            );
            return option ? String(option.value) : '';
        }
        """,
        name,
    )
    assert value, f"Expected shared favourite '{name}' in the rendered picker."
    select.evaluate(
        """
        (element, nextValue) => {
            if (element.tomselect) {
                element.tomselect.setValue(String(nextValue));
                return;
            }
            element.value = String(nextValue);
            element.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """,
        value,
    )


def test_shared_list_filter_pagination_columns_and_row_actions(page, books_url, sample_author, sample_books):
    """Both packs should retain repeated-init-safe list interactions without errors."""
    del sample_books
    for number in range(7):
        Book.objects.create(
            title=f"Matrix Browser Book {number}",
            author=sample_author,
            published_date=date(2024, 6, number + 1),
            bestseller=False,
            isbn=f"978000003{number:04d}",
            pages=300 + number,
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

    _install_htmx_before_navigation(page)
    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")
    _ensure_htmx(page)
    assert page.evaluate("() => typeof window.initPowercrud === 'function'"), (
        "Each selected pack must retain the stable public runtime entry."
    )
    page.evaluate(
        """
        () => {
            const root = document.querySelector('[data-powercrud-object-list="true"]');
            window.initPowercrud(root);
            window.initPowercrud(root);
            window.initPowercrud(document);
        }
        """
    )

    panel = _open_columns(page)
    panel.locator("input[name='visible_columns'][value='uneditable_field']").check()
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        panel.get_by_role("button", name="Save").click()
    expect(page.locator("td[data-field-name='uneditable_field']").first).to_be_visible()

    title_header = page.get_by_role("columnheader").filter(has_text="Title").first
    sort_target = title_header.locator("a[hx-get]")
    with page.expect_request(
        lambda request: request.headers.get("x-filter-sort-request") == "true"
    ):
        if sort_target.count():
            sort_target.click()
        else:
            title_header.dispatch_event("click")
    expect(page).to_have_url(re.compile(r"[?&]sort=title(?:&|$)"))

    pagination = page.get_by_role("navigation", name=re.compile("page navigation", re.I))
    with page.expect_request(
        lambda request: request.headers.get("x-filter-sort-request") == "true"
    ):
        pagination.get_by_role("link", name="Next", exact=True).click()
    expect(page).to_have_url(re.compile(r"[?&]page=2(?:&|$)"))

    page.locator("#filterToggleBtn").click()
    title_filter = page.locator("#filter-form input[name='title']")
    title_filter.fill("Matrix Browser Book")
    expect(page.locator("#filtered_results")).to_contain_text("Matrix Browser Book")

    assert not console_errors, f"Shared list interactions emitted browser errors: {console_errors}"
    assert not page_errors, f"Shared list interactions emitted page errors: {page_errors}"


def test_shared_list_header_wrap_geometry_uses_the_configured_presentation_contract(
    page, books_url, sample_books
):
    """Selected packs must retain a usable minimum wrapping width for long headers."""
    del sample_books
    page.set_viewport_size({"width": 640, "height": 720})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    metrics = page.evaluate(
        """
        () => {
            const root = document.querySelector('[data-powercrud-object-list="true"]');
            const header = document.querySelector(
                'thead th[data-field-name="a_really_long_property_header_for_title"]'
            );
            const styles = window.getComputedStyle(header);
            return {
                whiteSpace: styles.whiteSpace,
                minWidth: styles.minWidth,
                bootstrapMinWrapWidth: root.style.getPropertyValue(
                    '--pc-table-header-min-wrap-width'
                ).trim(),
            };
        }
        """
    )

    assert metrics["whiteSpace"] == "normal", (
        "Long list headers must be allowed to wrap rather than forcing horizontal overflow."
    )
    assert metrics["minWidth"] != "0px", (
        "The public table_header_min_wrap_width setting must produce a real header minimum."
    )
    if settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR:
        assert metrics["bootstrapMinWrapWidth"] == "15ch", (
            "Bootstrap must pass the resolved header-wrap width into its adapter stylesheet."
        )


def test_shared_favourite_application_uses_the_same_list_shell(page, client, books_url, sample_books):
    """A selected pack should apply a saved favourite without leaving the shared shell."""
    user = get_user_model().objects.create_user(username="matrix-browser-favourite")
    client.force_login(user)
    session_cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
    page.context.add_cookies(
        [{"name": settings.SESSION_COOKIE_NAME, "value": session_cookie, "url": books_url}]
    )
    target_book, other_book = sample_books
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Matrix favourite",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    _install_htmx_before_navigation(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    _ensure_htmx(page)
    _select_favourite(_open_favourites(page), "Matrix favourite")
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)
    expect(
        page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    ).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(page.locator("nav[aria-label='Sample navigation']")).to_be_visible()


@pytest.mark.usefixtures("sample_manager_page")
def test_shared_manager_bulk_inline_detail_modal_and_delete_matrix(page, books_url, sample_books, sample_genre):
    """Shared manager actions should retain bulk, inline, detail, modal, and delete paths."""
    inline_book, delete_book = sample_books
    inline_book.genres.add(sample_genre)

    _install_htmx_before_navigation(page)
    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")
    _ensure_htmx(page)

    inline_row = page.locator("tr[data-inline-row='true']", has_text=inline_book.title)
    inline_row.locator(".inline-edit-trigger[data-inline-field='title']").click(force=True)
    active_row = page.locator("tr[data-inline-row='true'][data-inline-active='true']")
    expect(active_row).to_have_count(1, timeout=15000)
    new_title = f"Matrix Inline {uuid4().hex[:6]}"
    active_row.locator("input[name='title']").fill(new_title)
    active_row.locator("[data-inline-save]").click()
    expect(page.locator("tr[data-inline-row='true']", has_text=new_title)).to_be_visible(
        timeout=15000
    )
    inline_book.refresh_from_db()
    assert inline_book.title == new_title, "The shared inline save should persist the edited title."

    row_actions = page.locator("[data-powercrud-row-actions-trigger='true']").first
    row_actions.dispatch_event("click")
    expect(page.locator("[data-powercrud-row-actions-floating-panel='true']")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator("[data-powercrud-row-actions-floating-panel='true']")).to_have_count(0)

    selection = page.locator("input.row-select-checkbox").first
    selection.click()
    expect(page.locator("#selected-items-counter")).to_have_text("1")
    page.evaluate("() => window.initPowercrud(document)")
    expect(selection).to_be_checked()

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    detail_row = page.locator("tbody tr", has_text=new_title)
    detail_row.locator('td[data-field-name="pages"] a').click()
    expect(page).to_have_url(re.compile(rf"/sample/bigbook/{inline_book.pk}/"))
    expect(page.locator("body")).to_contain_text(new_title)

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    delete_row = page.locator("tbody tr", has_text=delete_book.title)
    delete_row.get_by_role("link", name="Delete").click()
    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    expect(modal.locator("#powercrudModalContent")).to_contain_text(delete_book.title)
    modal.get_by_role("button", name="Delete").click()
    expect(modal).not_to_be_visible()
    expect(page.locator("body")).not_to_contain_text(delete_book.title)
    assert not Book.objects.filter(pk=delete_book.pk).exists(), (
        "The shared modal delete action should remove its selected Book."
    )
