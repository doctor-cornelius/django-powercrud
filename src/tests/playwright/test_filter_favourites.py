import json
import re
from datetime import date
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from playwright.sync_api import expect

from powercrud.contrib.favourites.models import SavedFilterFavourite
from sample.models import Book
from sample.views import BookCRUDView

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]
HTMX_TEST_BUNDLE_PATH = (
    Path(__file__).resolve().parents[3] / "node_modules" / "htmx.org" / "dist" / "htmx.min.js"
)
BOOK_VIEW_KEY = f"{BookCRUDView.__module__}.{BookCRUDView.__name__}"


def open_favourites_dropdown(page):
    """Open the filter favourites dropdown using its stable trigger selector."""

    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_be_visible()
    trigger.evaluate("(el) => el.click()")
    expect(get_open_favourites_panel(page)).to_have_count(1)


def get_open_favourites_panel(page):
    """Return the floating favourites panel."""

    return page.locator("[data-powercrud-filter-favourites-floating-panel='true']").last


def install_htmx_init_script(page):
    """Install HTMX before navigation so page scripts can use it during page load."""

    assert HTMX_TEST_BUNDLE_PATH.exists(), (
        f"Expected local HTMX bundle at '{HTMX_TEST_BUNDLE_PATH}' for Playwright browser setup."
    )
    page.add_init_script(path=str(HTMX_TEST_BUNDLE_PATH))


def ensure_htmx_available(page):
    """Inject HTMX into the Playwright page when the test asset pipeline omits ``window.htmx``."""

    has_htmx = page.evaluate("() => Boolean(window.htmx)")
    if has_htmx:
        return

    assert HTMX_TEST_BUNDLE_PATH.exists(), (
        f"Expected local HTMX bundle at '{HTMX_TEST_BUNDLE_PATH}' for Playwright browser setup."
    )
    page.add_script_tag(path=str(HTMX_TEST_BUNDLE_PATH))
    page.evaluate(
        """
        () => {
            if (window.htmx) {
                window.htmx.process(document.body);
            }
        }
        """
    )
    assert page.evaluate("() => Boolean(window.htmx)"), (
        "Expected Playwright browser setup to expose window.htmx after injecting the local HTMX bundle."
    )


def select_saved_favourite(page, favourite_label: str):
    """Select one saved favourite through the rendered TomSelect/native control."""

    panel = get_open_favourites_panel(page)
    select = panel.locator("select[name='favourite_id']")
    option_value = select.evaluate(
        """
        (el, label) => {
            const option = Array.from(el.options).find(
                (candidate) => candidate.textContent.trim() === label
            );
            return option ? String(option.value) : '';
        }
        """,
        favourite_label,
    )
    assert option_value, (
        f"Expected saved favourite option '{favourite_label}' to exist in the favourites picker."
    )

    indices = select.evaluate(
        """
        (el, nextValue) => {
            const options = Array.from(el.options).map((option) => String(option.value));
            return {
                currentIndex: Math.max(options.indexOf(String(el.value)), 0),
                targetIndex: options.indexOf(String(nextValue)),
            };
        }
        """,
        option_value,
    )
    assert indices["targetIndex"] != -1, (
        f"Expected saved favourite option value '{option_value}' to exist in the favourites picker."
    )
    select.evaluate(
        """
        (el, nextValue) => {
            if (el.tomselect) {
                el.tomselect.setValue(String(nextValue), true);
                return;
            }
            el.value = String(nextValue);
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """,
        option_value,
    )
    return option_value


def login_playwright_user(*, client, page, books_url: str, username: str):
    """Authenticate the Playwright browser context using a Django test-client session."""

    user = get_user_model().objects.create_user(username=username, password="unused-password")
    client.force_login(user)
    session_cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
    page.context.add_cookies(
        [
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session_cookie,
                "url": books_url,
            }
        ]
    )
    return user


def test_filter_favourite_apply_preserves_sample_shell(
    page, client, books_url, sample_books
):
    """Applying a saved favourite should refresh the list in #content without dropping the sample shell."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-user",
    )
    target_book = sample_books[0]
    other_book = sample_books[1]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Only target",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    expect(page.locator("body")).to_contain_text("Home (Reload)")
    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Only target")
    page.wait_for_load_state("networkidle")

    expect(page.locator("body")).to_contain_text("Home (Reload)")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)


def test_book_page_size_query_still_renders_correctly_when_filter_favourites_enabled(
    page, books_url, sample_author, sample_books
):
    """The page-size query parameter should still render the expected result size when favourites are enabled."""

    for idx in range(2, 12):
        Book.objects.create(
            title=f"Page Size Book {idx}",
            author=sample_author,
            published_date=date(2024, 3, idx),
            bestseller=False,
            isbn=f"97877777{idx:04d}",
            pages=120 + idx,
            description="Created for page-size regression coverage",
        )

    install_htmx_init_script(page)
    page.goto(f"{books_url}?page_size=10")
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    expect(page.locator("#page-size-select")).to_have_value("10")
    expect(page.locator("#filtered_results tbody tr[data-inline-row='true']")).to_have_count(10)


def test_filter_reset_clears_remembered_selected_favourite(
    page, client, books_url, sample_books
):
    """Resetting filters should also clear the remembered selected favourite in the toolbar."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-reset-favourite-user",
    )
    target_book = sample_books[0]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Reset me",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    open_favourites_dropdown(page)
    favourites_select = get_open_favourites_panel(page).locator("select[name='favourite_id']")
    select_saved_favourite(page, "Reset me")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    page.get_by_role("link", name="Reset").click()
    page.wait_for_load_state("networkidle")

    filter_toggle = page.locator("#filterToggleBtn")
    if re.search(r"show filters", filter_toggle.inner_text(), re.I):
        filter_toggle.click()
    open_favourites_dropdown(page)

    expect(favourites_select).to_have_value("")


def test_filter_favourite_apply_replaces_optional_filter_visibility(
    page, client, books_url, sample_books
):
    """Applying a saved favourite should replace browser-remembered optional filters with the saved visible set."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-visible-filters-user",
    )
    target_book = sample_books[0]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Only title",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(f"{books_url}?visible_filters=genres")
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    expect(page.locator("#filter-form [name='genres']")).to_have_count(1)

    open_favourites_dropdown(page)
    select_saved_favourite(page, "Only title")
    page.wait_for_load_state("networkidle")

    expect(page.locator("#filter-form [name='genres']")).to_have_count(0)
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)


def test_returning_to_page_clears_selected_filter_favourite(
    page, client, books_url, authors_url, sample_books
):
    """Returning to a list after leaving it should clear the selected favourite instead of auto-reapplying it."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-return-favourite-user",
    )
    target_book = sample_books[0]
    other_book = sample_books[1]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Come back to me",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Come back to me")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)

    page.goto(authors_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    filter_toggle = page.locator("#filterToggleBtn")
    if re.search(r"show filters", filter_toggle.inner_text(), re.I):
        filter_toggle.click()

    open_favourites_dropdown(page)
    favourites_select = get_open_favourites_panel(page).locator("select[name='favourite_id']")
    expect(favourites_select).to_have_value("")
    expect(page.locator("#filter-form input[name='title']")).to_have_value("")
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(other_book.title)


def test_filter_favourite_update_reapplies_latest_saved_state(
    page, client, books_url, sample_books
):
    """A favourite updated through the contrib endpoint should reapply its latest saved state in-browser."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-update-user",
    )
    original_book = sample_books[0]
    updated_book = sample_books[1]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Switch me",
        state={
            "filters": {"title": [original_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Switch me")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(original_book.title)

    updated_state = {
        "filters": {"title": [updated_book.title]},
        "visible_filters": [],
        "sort": "",
        "page_size": "5",
    }
    response = client.post(
        reverse("powercrud:favourites-update"),
        {
            "favourite_id": SavedFilterFavourite.objects.get(
                user=user,
                view_key=BOOK_VIEW_KEY,
                name="Switch me",
            ).pk,
            "view_key": BOOK_VIEW_KEY,
            "list_view_url": reverse("sample:bigbook-list"),
            "toolbar_dom_id": "powercrud-favourites-toolbar-test",
            "current_state_json": json.dumps(updated_state),
            "state_json": json.dumps(updated_state),
            "original_target": "#content",
        },
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200, (
        "Updating the saved favourite through the contrib endpoint should succeed before the browser reapplies it."
    )

    page.get_by_role("link", name="Reset").click()
    page.wait_for_load_state("networkidle")

    filter_toggle = page.locator("#filterToggleBtn")
    if re.search(r"show filters", filter_toggle.inner_text(), re.I):
        filter_toggle.click()

    open_favourites_dropdown(page)
    select_saved_favourite(page, "Switch me")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(updated_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(updated_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(original_book.title)


def test_filter_favourite_can_be_saved_inline_without_opening_modal(
    page, client, books_url
):
    """The favourites UI should expose inline save controls without opening the shared modal."""

    login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-inline-favourite-user",
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    open_favourites_dropdown(page)

    inline_form = get_open_favourites_panel(page).locator("[data-powercrud-favourite-save-form='true']")
    expect(inline_form).to_be_visible()
    expect(page.locator("#powercrudBaseModal")).not_to_be_visible()
    expect(inline_form.locator("input[name='name']")).to_be_visible()
    expect(inline_form.get_by_role("button", name="Save favourite")).to_be_visible()
    inline_form.locator("input[name='name']").fill("Inline saved favourite")
    with page.expect_response(
        lambda response: response.request.method == "POST"
        and "/powercrud/favourites/save/" in response.url
    ) as save_response_info:
        inline_form.get_by_role("button", name="Save favourite").click()
    assert save_response_info.value.status == 200, (
        "Expected inline favourite save to return a successful HTMX response."
    )

    assert SavedFilterFavourite.objects.filter(
        user__username="playwright-inline-favourite-user",
        view_key=BOOK_VIEW_KEY,
        name="Inline saved favourite",
    ).exists(), (
        "Expected inline favourites save to persist a saved favourite instead of failing CSRF validation."
    )


def test_returning_to_page_via_sample_shell_htmx_clears_selected_filter_favourite(
    page, client, books_url, sample_books
):
    """Returning via the sample shell HTMX nav should clear the previously selected favourite."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-shell-return-favourite-user",
    )
    target_book = sample_books[0]
    other_book = sample_books[1]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Shell trip",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Shell trip")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)

    page.locator("a", has_text=re.compile(r"author list \(htmx\)", re.I)).click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_contain_text("The Author Persons")

    page.locator("a", has_text=re.compile(r"book list \(htmx\)", re.I)).click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("#content")).to_contain_text("My List of Books")
    expect(page.locator("#filterToggleBtn")).to_be_visible()

    filter_toggle = page.locator("#filterToggleBtn")
    if re.search(r"show filters", filter_toggle.inner_text(), re.I):
        filter_toggle.click()

    open_favourites_dropdown(page)
    favourites_select = get_open_favourites_panel(page).locator("select[name='favourite_id']")
    expect(favourites_select).to_have_value("")
    expect(page.locator("#filter-form input[name='title']")).to_have_value("")
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(other_book.title)
