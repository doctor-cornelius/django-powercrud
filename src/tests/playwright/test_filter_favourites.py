import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

import pytest

pytest.importorskip("playwright.sync_api")
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from playwright.sync_api import expect

from powercrud.contrib.favourites.models import SavedFilterFavourite
from sample.models import Author, Book
from sample.views import BookCRUDView

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]
HTMX_TEST_BUNDLE_PATH = (
    Path(__file__).resolve().parents[3] / "node_modules" / "htmx.org" / "dist" / "htmx.min.js"
)
BOOK_VIEW_KEY = f"{BookCRUDView.__module__}.{BookCRUDView.__name__}"
SELECTED_FAVOURITE_STORAGE_KEY = f"powercrud:selected-filter-favourite:{BOOK_VIEW_KEY}"
DIRTY_FAVOURITE_STORAGE_KEY = f"powercrud:selected-filter-favourite-dirty:{BOOK_VIEW_KEY}"
VIEW_STATE_STORAGE_KEY = f"powercrud:view-state:{BOOK_VIEW_KEY}"


def open_favourites_dropdown(page):
    """Open the filter favourites dropdown using its stable trigger selector."""

    trigger_selector = "[data-powercrud-filter-favourites-trigger='true']:visible"
    trigger = page.locator(trigger_selector).first
    expect(trigger).to_be_visible()
    trigger.click(force=True)
    panel = get_open_favourites_panel(page)
    try:
        expect(panel).to_have_count(1, timeout=1500)
    except AssertionError:
        # HTMX reset/list swaps can leave the first click racing the refreshed toolbar.
        # Re-resolve the visible trigger and retry once against the new DOM.
        trigger = page.locator(trigger_selector).first
        expect(trigger).to_be_visible()
        trigger.click(force=True)
        expect(panel).to_have_count(1)


def get_open_favourites_panel(page):
    """Return the floating favourites panel."""

    return page.locator("[data-powercrud-filter-favourites-floating-panel='true']").last


def open_column_chooser(page):
    """Open the list-column chooser."""

    trigger = page.locator("[data-powercrud-list-columns='true'] summary")
    expect(trigger).to_be_visible()
    trigger.click(force=True)
    panel = page.locator("[data-powercrud-list-columns-floating-panel='true']").last
    expect(panel).to_be_visible()
    return panel


def open_filters_panel(page):
    """Open the list filter panel if it is currently collapsed."""

    toggle = page.locator("#filterToggleBtn")
    expect(toggle).to_be_visible()
    if toggle.get_attribute("aria-expanded") != "true":
        toggle.click()
    expect(page.locator("#filterCollapse")).not_to_have_class(re.compile(r"\bhidden\b"))


def get_sample_navigation(page):
    """Return the sample shell navigation."""

    return page.locator("nav[aria-label='Sample navigation']")


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
                el.tomselect.setValue(String(nextValue));
                return;
            }
            el.value = String(nextValue);
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """,
        option_value,
    )
    return option_value


def click_saved_favourite(page, favourite_label: str):
    """Select one saved favourite through the visible Tom Select UI."""

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

    panel.locator(".powercrud-filter-favourite-select-control").click()
    option = page.locator(".powercrud-filter-favourite-select-dropdown .option").filter(
        has_text=favourite_label
    ).last
    expect(option).to_be_visible()
    option.click()
    return option_value


def select_single_filter_value(page, field_name: str, option_value: str):
    """Select one filter option, preferring Tom Select when the filter is enhanced."""

    select = page.locator(f"#filter-form select[name='{field_name}']")
    expect(select).to_have_count(1)
    is_searchable = select.evaluate(
        "el => el.getAttribute('data-powercrud-searchable-select') === 'true'"
    )
    if is_searchable:
        page.wait_for_function(
            """
            (name) => {
                const element = document.querySelector(`#filter-form select[name="${name}"]`);
                return Boolean(element && element.tomselect);
            }
            """,
            arg=field_name,
        )

    if select.evaluate("el => Boolean(el.tomselect)"):
        select.evaluate(
            """
            (el, value) => {
                el.tomselect.setValue(String(value));
            }
            """,
            option_value,
        )
    else:
        select.select_option(option_value)
    expect(select).to_have_value(option_value)


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


def seed_filter_favourite_browser_state(
    page,
    *,
    selected_favourite_id: str,
    dirty_favourite_id: str = "",
    stored_view_query: str = "",
):
    """Seed the browser-side favourite and stored-view session state."""

    page.evaluate(
        """
        (payload) => {
            const setOrRemove = (key, value) => {
                if (value) {
                    window.sessionStorage.setItem(key, value);
                    return;
                }
                window.sessionStorage.removeItem(key);
            };
            setOrRemove(payload.selectedKey, payload.selectedValue);
            setOrRemove(payload.dirtyKey, payload.dirtyValue);
            setOrRemove(payload.viewStateKey, payload.viewStateValue);
        }
        """,
        {
            "selectedKey": SELECTED_FAVOURITE_STORAGE_KEY,
            "selectedValue": str(selected_favourite_id),
            "dirtyKey": DIRTY_FAVOURITE_STORAGE_KEY,
            "dirtyValue": str(dirty_favourite_id),
            "viewStateKey": VIEW_STATE_STORAGE_KEY,
            "viewStateValue": stored_view_query,
        },
    )


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
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    expect(get_sample_navigation(page).get_by_role("link", name="Home")).to_be_visible()
    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Only target")
    page.wait_for_load_state("networkidle")

    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("aria-label", "Saved favourite: Only target")
    expect(trigger).to_have_attribute("data-tippy-content", "Only target")
    expect(
        trigger.locator("[data-powercrud-filter-favourites-icon-filled='true']")
    ).not_to_have_class(re.compile(r"\bhidden\b"))
    expect(
        trigger.locator("[data-powercrud-filter-favourites-icon-outline='true']")
    ).to_have_class(re.compile(r"\bhidden\b"))
    expect(get_sample_navigation(page).get_by_role("link", name="Home")).to_be_visible()
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)

    page.reload()
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("aria-label", "Saved favourite: Only target")
    expect(trigger).to_have_attribute("data-tippy-content", "Only target")
    expect(
        trigger.locator("[data-powercrud-filter-favourites-icon-filled='true']")
    ).not_to_have_class(re.compile(r"\bhidden\b"))
    expect(
        trigger.locator("[data-powercrud-filter-favourites-icon-outline='true']")
    ).to_have_class(re.compile(r"\bhidden\b"))


test_filter_favourite_apply_preserves_sample_shell = pytest.mark.playwright_smoke(
    test_filter_favourite_apply_preserves_sample_shell
)


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


def test_toolbar_transient_dropdowns_are_mutually_exclusive(
    page, client, books_url, sample_books
):
    """Toolbar popovers should hand off without overlapping each other."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-toolbar-dropdown-user",
    )
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Toolbar favourite",
        state={
            "filters": {},
            "visible_filters": [],
            "sort": "",
            "page_size": "10",
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    filter_panel = page.locator("#filterCollapse")
    expect(filter_panel).not_to_have_class(re.compile(r"\bhidden\b"))

    open_favourites_dropdown(page)
    expect(page.locator("[data-powercrud-filter-favourites-floating-panel='true']")).to_have_count(1)

    column_panel = open_column_chooser(page)
    expect(page.locator("[data-powercrud-filter-favourites-floating-panel='true']")).to_have_count(0)
    expect(column_panel).to_be_visible()
    expect(filter_panel).not_to_have_class(re.compile(r"\bhidden\b"))

    open_favourites_dropdown(page)
    expect(page.locator("[data-powercrud-list-columns-floating-panel='true']")).to_have_count(0)
    expect(page.locator("[data-powercrud-filter-favourites-floating-panel='true']")).to_have_count(1)

    page.locator("#page-size-select").click(force=True)
    expect(page.locator("[data-powercrud-filter-favourites-floating-panel='true']")).to_have_count(0)
    expect(filter_panel).not_to_have_class(re.compile(r"\bhidden\b"))

    column_panel = open_column_chooser(page)
    expect(column_panel).to_be_visible()
    page.locator("#page-size-select").focus()
    expect(page.locator("[data-powercrud-list-columns-floating-panel='true']")).to_have_count(0)
    expect(filter_panel).not_to_have_class(re.compile(r"\bhidden\b"))


def test_page_size_change_marks_selected_favourite_dirty(
    page, client, books_url, sample_author, sample_books
):
    """Page-size changes should dirty the selected favourite without losing selection state."""

    for idx in range(2, 12):
        Book.objects.create(
            title=f"Favourite Page Size Book {idx}",
            author=sample_author,
            published_date=date(2024, 5, idx),
            bestseller=False,
            isbn=f"97877888{idx:04d}",
            pages=140 + idx,
            description="Created for favourite dirty-state page-size coverage",
        )

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-page-size-dirty-user",
    )
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Five rows",
        state={
            "filters": {},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    install_htmx_init_script(page)
    page.goto(f"{books_url}?page_size=10")
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Five rows")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#page-size-select")).to_have_value("5")

    with page.expect_response(re.compile(r"/sample/bigbook/")):
        page.locator("#page-size-select").select_option("10")
    page.wait_for_load_state("networkidle")

    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "true")
    expect(trigger).to_have_attribute("aria-label", "Saved favourite: Five rows (edited)")
    expect(trigger).to_have_attribute("data-tippy-content", "Five rows (edited)")
    expect(page.locator("#page-size-select")).to_have_value("10")


def test_changing_favourite_populated_filter_applies_immediately(
    page, client, books_url, sample_books
):
    """Editing a filter populated by a favourite should refresh without touching another filter first."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-populated-filter-user",
    )
    target_book = sample_books[0]
    replacement_book = sample_books[1]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Title favourite",
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

    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Title favourite")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(replacement_book.title)

    title_filter = page.locator("#filter-form input[name='title']")
    title_filter.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(replacement_book.title)

    expect(page.locator("#filtered_results")).to_contain_text(replacement_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(target_book.title)


def test_changing_favourite_populated_choice_filter_applies_immediately(
    page, client, books_url, sample_author, sample_books
):
    """Changing a favourite-populated select filter should refresh without touching another filter first."""

    replacement_author = Author.objects.create(
        name="Replacement Favourite Filter Author",
        bio="",
        birth_date=None,
    )
    target_book = sample_books[0]
    replacement_book = sample_books[1]
    replacement_book.author = replacement_author
    replacement_book.save(update_fields=["author"])

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-populated-choice-filter-user",
    )
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Author favourite",
        state={
            "filters": {"author": [str(sample_author.pk)]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Author favourite")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form select[name='author']")).to_have_value(str(sample_author.pk))
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(replacement_book.title)

    select_single_filter_value(page, "author", str(replacement_author.pk))

    expect(page.locator("#filtered_results")).to_contain_text(replacement_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(target_book.title)


def test_filter_reset_marks_selected_favourite_dirty(
    page, client, books_url, sample_books
):
    """Resetting filters should keep the selected favourite and mark it edited."""

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

    open_filters_panel(page)
    open_favourites_dropdown(page)
    favourites_select = get_open_favourites_panel(page).locator("select[name='favourite_id']")
    favourite_id = select_saved_favourite(page, "Reset me")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    page.get_by_role("link", name="Reset filters").click()
    page.wait_for_load_state("networkidle")

    open_filters_panel(page)
    open_favourites_dropdown(page)

    expect(favourites_select).to_have_value(favourite_id)
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "true")
    expect(trigger).to_have_attribute("data-tippy-content", "Reset me (edited)")


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

    open_filters_panel(page)
    expect(page.locator("#filter-form [name='genres']")).to_have_count(1)

    open_favourites_dropdown(page)
    select_saved_favourite(page, "Only title")
    page.wait_for_load_state("networkidle")

    expect(page.locator("#filter-form [name='genres']")).to_have_count(0)
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)


def test_reset_view_clears_favourite_filter_page_size_and_visible_columns(
    page, client, books_url, sample_books, sample_genre
):
    """Reset view should clear saved list state instead of leaving favourite fragments behind."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-reset-view-user",
    )
    target_book = sample_books[0]
    other_book = sample_books[1]
    target_book.genres.add(sample_genre)
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Reset whole view",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "10",
            "visible_columns": [
                *BookCRUDView.default_list_fields,
                "uneditable_field",
            ],
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Reset whole view")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#page-size-select")).to_have_value("10")
    expect(page.locator("td[data-field-name='uneditable_field']").first).to_be_visible()
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)

    open_favourites_dropdown(page)
    panel = get_open_favourites_panel(page)
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        panel.get_by_role("button", name="Reset").click()
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    expect(page.locator("#filter-form input[name='title']")).to_have_value("")
    expect(page.locator("#page-size-select")).to_have_value("5")
    expect(page.locator("td[data-field-name='uneditable_field']")).to_have_count(0)
    expect(page.locator("#filtered_results")).to_contain_text(other_book.title)

    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "false")
    expect(trigger).not_to_have_attribute("data-powercrud-filter-favourites-dirty", "true")
    expect(trigger).to_have_attribute("aria-label", "Saved favourites")
    expect(trigger).to_have_attribute("data-tippy-content", "Saved favourites")


def test_returning_to_page_keeps_selected_filter_favourite(
    page, client, books_url, authors_url, sample_books
):
    """Returning to a list should keep and apply the selected favourite."""

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

    open_filters_panel(page)
    open_favourites_dropdown(page)
    favourite_id = select_saved_favourite(page, "Come back to me")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)

    page.goto(authors_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)

    open_favourites_dropdown(page)
    favourites_select = get_open_favourites_panel(page).locator("select[name='favourite_id']")
    expect(favourites_select).to_have_value(favourite_id)
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-tippy-content", "Come back to me")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)


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

    open_filters_panel(page)
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

    open_filters_panel(page)
    page.get_by_role("link", name="Reset filters").click()
    page.wait_for_load_state("networkidle")

    open_filters_panel(page)

    open_favourites_dropdown(page)
    select_saved_favourite(page, "Switch me")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(updated_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(updated_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(original_book.title)


def test_updating_dirty_selected_favourite_refreshes_heart_state(
    page, client, books_url, sample_books
):
    """Updating an edited selected favourite should immediately repaint the heart as clean."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-update-clean-heart-user",
    )
    original_book = sample_books[0]
    updated_book = sample_books[1]
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Clean my heart",
        state={
            "filters": {"title": [original_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Clean my heart")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(original_book.title)

    title_filter = page.locator("#filter-form input[name='title']")
    title_filter.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(updated_book.title)
    page.wait_for_load_state("networkidle")

    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "true")
    expect(trigger).to_have_attribute("data-tippy-content", "Clean my heart (edited)")

    open_favourites_dropdown(page)
    panel = get_open_favourites_panel(page)
    expect(panel.locator("select[name='favourite_id']")).to_have_value(str(favourite.pk))
    with page.expect_response(
        lambda response: response.request.method == "POST"
        and "/powercrud/favourites/update/" in response.url
    ) as update_response_info:
        panel.get_by_role("button", name="Update").click()
    assert update_response_info.value.status == 200, (
        "Expected updating the selected favourite to return a successful HTMX response."
    )
    page.wait_for_timeout(100)

    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "false")
    expect(trigger).to_have_attribute("data-tippy-content", "Clean my heart")
    dirty_after_update = page.evaluate(
        "(dirtyKey) => window.sessionStorage.getItem(dirtyKey)",
        DIRTY_FAVOURITE_STORAGE_KEY,
    )
    assert dirty_after_update is None, (
        "Updating the selected favourite should clear the browser dirty marker."
    )


def test_filter_favourite_can_be_saved_inline_without_opening_modal(
    page, client, books_url, sample_books
):
    """The favourites UI should expose inline save controls without opening the shared modal."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-inline-favourite-user",
    )
    target_book = sample_books[0]
    other_book = sample_books[1]
    SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Existing favourite",
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

    open_filters_panel(page)
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

    open_favourites_dropdown(page)
    click_saved_favourite(page, "Existing favourite")
    page.wait_for_load_state("networkidle")

    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)


def test_deleting_selected_dirty_favourite_clears_browser_state(
    page, client, books_url, sample_books
):
    """Deleting a selected dirty favourite should leave the toolbar in the neutral state."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-delete-dirty-user",
    )
    target_book = sample_books[0]
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Delete dirty",
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

    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Delete dirty")
    page.wait_for_load_state("networkidle")

    with page.expect_response(re.compile(r"/sample/bigbook/")):
        page.locator("#page-size-select").select_option("10")
    page.wait_for_load_state("networkidle")
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "true")

    open_favourites_dropdown(page)
    panel = get_open_favourites_panel(page)
    expect(panel.locator("select[name='favourite_id']")).to_have_value(str(favourite.pk))
    with page.expect_response(
        lambda response: response.request.method == "POST"
        and "/powercrud/favourites/delete/" in response.url
    ) as delete_response_info:
        panel.get_by_role("button", name="Delete").click()
    assert delete_response_info.value.status == 200
    assert not SavedFilterFavourite.objects.filter(pk=favourite.pk).exists()

    page.wait_for_timeout(100)
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "false")
    expect(trigger).not_to_have_attribute("data-powercrud-filter-favourites-dirty", "true")
    expect(trigger).to_have_attribute("aria-label", "Saved favourites")
    expect(trigger).to_have_attribute("data-tippy-content", "Saved favourites")

    open_favourites_dropdown(page)
    select = get_open_favourites_panel(page).locator("select[name='favourite_id']")
    expect(select).to_have_value("")
    assert not select.evaluate(
        "(el, deletedValue) => Array.from(el.options).some(option => option.value === deletedValue)",
        str(favourite.pk),
    )


def test_saved_favourite_restores_visible_columns(
    page, client, books_url, sample_books, sample_genre
):
    """Saved favourites should restore visible columns as part of saved list state."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-columns-user",
    )
    sample_books[0].genres.add(sample_genre)

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='uneditable_field']")).to_have_count(0)
    column_panel = open_column_chooser(page)
    column_panel.locator("input[name='visible_columns'][value='uneditable_field']").check()
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        column_panel.get_by_role("button", name="Save").click()
    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='uneditable_field']").first).to_be_visible()

    open_filters_panel(page)
    open_favourites_dropdown(page)
    inline_form = get_open_favourites_panel(page).locator(
        "[data-powercrud-favourite-save-form='true']"
    )
    inline_form.locator("input[name='name']").fill("Columns saved")
    with page.expect_response(
        lambda response: response.request.method == "POST"
        and "/powercrud/favourites/save/" in response.url
    ) as save_response_info:
        inline_form.get_by_role("button", name="Save favourite").click()
    assert save_response_info.value.status == 200, (
        "Expected saving a favourite with visible columns to return a successful HTMX response."
    )
    saved_favourite = SavedFilterFavourite.objects.get(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Columns saved",
    )
    assert "uneditable_field" in saved_favourite.state.get("visible_columns", []), (
        "Saved favourite state should include the currently visible optional column."
    )
    page.keyboard.press("Escape")

    column_panel = open_column_chooser(page)
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        column_panel.get_by_role("button", name="Reset").click()
    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='uneditable_field']")).to_have_count(0)

    open_filters_panel(page)
    open_favourites_dropdown(page)
    select_saved_favourite(page, "Columns saved")
    page.wait_for_load_state("networkidle")

    expect(page.locator("td[data-field-name='genres']").first).to_be_visible()
    expect(page.locator("td[data-field-name='genres']").first).to_contain_text(
        sample_genre.name
    )
    expect(page.locator("td[data-field-name='uneditable_field']").first).to_be_visible()


def test_column_chooser_change_marks_selected_favourite_dirty(
    page, client, books_url, sample_books
):
    """Changing columns with a selected favourite should not reapply the favourite."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-column-dirty-user",
    )
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Default columns",
        state={
            "filters": {},
            "visible_filters": [],
            "sort": "",
            "page_size": "10",
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    install_htmx_init_script(page)
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    open_favourites_dropdown(page)
    with page.expect_response(re.compile(r"/powercrud/favourites/apply/")):
        select_saved_favourite(page, "Default columns")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#page-size-select")).to_have_value("10")
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "false")
    expect(page.locator("td[data-field-name='isbn']").first).to_be_visible()

    column_panel = open_column_chooser(page)
    column_panel.locator("input[name='visible_columns'][value='isbn']").uncheck()
    dirty_storage_key = f"powercrud:selected-filter-favourite-dirty:{BOOK_VIEW_KEY}"
    apply_request_urls = []
    page.on(
        "request",
        lambda request: apply_request_urls.append(request.url)
        if "/powercrud/favourites/apply/" in request.url
        else None,
    )
    with page.expect_response(re.compile(r"/sample/bigbook/")):
        column_panel.get_by_role("button", name="Save").click()
    page.wait_for_load_state("networkidle")

    expect(page.locator("td[data-field-name='isbn']")).to_have_count(0)
    dirty_after_save = page.evaluate(
        "(dirtyKey) => window.sessionStorage.getItem(dirtyKey)",
        dirty_storage_key,
    )
    assert dirty_after_save == str(favourite.pk), (
        "Saving the floating column chooser should mark the selected favourite dirty "
        "using the real selected-favourite dirty storage key."
    )
    assert apply_request_urls == [], (
        "Saving columns for a dirty selected favourite should not auto-apply the saved favourite."
    )
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "true")
    expect(trigger).to_have_attribute("aria-label", "Saved favourite: Default columns (edited)")


def test_remembered_favourite_uses_server_state_before_auto_apply(
    page, client, books_url, sample_books
):
    """Remembered favourites should not auto-apply when server state already matches."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-favourite-server-state-user",
    )
    target_book = sample_books[0]
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Server state wins",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
            "visible_columns": list(BookCRUDView.default_list_fields),
        },
    )

    install_htmx_init_script(page)
    page.goto(f"{books_url}?{urlencode({'title': target_book.title, 'page_size': '5'})}")
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)

    selected_storage_key = f"powercrud:selected-filter-favourite:{BOOK_VIEW_KEY}"
    page.evaluate(
        "(payload) => window.sessionStorage.setItem(payload.key, payload.value)",
        {"key": selected_storage_key, "value": str(favourite.pk)},
    )
    apply_request_urls = []
    page.on(
        "request",
        lambda request: apply_request_urls.append(request.url)
        if "/powercrud/favourites/apply/" in request.url
        else None,
    )

    page.evaluate(
        """
        () => {
            const root = document.querySelector('[data-powercrud-object-list="true"]');
            root?.querySelector('#filter-form input[name="title"]')?.remove();
            window.initPowercrud(root);
        }
        """
    )
    page.wait_for_timeout(500)

    assert apply_request_urls == [], (
        "Remembered favourite auto-apply should trust matching server-rendered toolbar state "
        "instead of dispatching from incomplete client-collected filter state."
    )


def test_returning_to_page_via_sample_shell_htmx_keeps_selected_filter_favourite(
    page, client, books_url, sample_books
):
    """Returning via the sample shell should keep and apply the selected favourite."""

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

    open_filters_panel(page)
    open_favourites_dropdown(page)
    favourite_id = select_saved_favourite(page, "Shell trip")
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)

    get_sample_navigation(page).locator("a", has_text="Authors").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_contain_text("The Author Persons")

    with page.expect_response(re.compile(r"/powercrud/favourites/apply/")) as apply_response:
        get_sample_navigation(page).get_by_label("Load books with HTMX").click()
    assert apply_response.value.ok, (
        "Expected returning via the sample HTMX shell to dispatch the remembered favourite apply request."
    )
    page.wait_for_load_state("networkidle")
    expect(page.locator("#content")).to_contain_text("My List of Books")
    expect(page.locator("#filterToggleBtn")).to_be_visible()

    open_filters_panel(page)

    open_favourites_dropdown(page)
    favourites_select = get_open_favourites_panel(page).locator("select[name='favourite_id']")
    expect(favourites_select).to_have_value(favourite_id)
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-tippy-content", "Shell trip")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)


def test_server_selected_favourite_from_full_page_url_auto_applies_after_shell_return(
    page, client, books_url, sample_books
):
    """Server-selected favourites should seed browser state for later HTMX shell returns."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-server-selected-favourite-user",
    )
    target_book = sample_books[0]
    other_book = sample_books[1]
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Server selected trip",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(f"{books_url}?{urlencode({'title': target_book.title, 'page_size': '5'})}")
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)

    open_filters_panel(page)
    favourites_select = page.locator(
        "[data-powercrud-filter-favourites-template='true'] select[name='favourite_id']"
    ).first
    expect(favourites_select).to_have_value(str(favourite.pk))
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-tippy-content", "Server selected trip")
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)

    get_sample_navigation(page).locator("a", has_text="Authors").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_contain_text("The Author Persons")

    with page.expect_response(
        re.compile(r"/powercrud/favourites/apply/"),
        timeout=5000,
    ) as apply_response:
        get_sample_navigation(page).get_by_label("Load books with HTMX").click()
    assert apply_response.value.ok, (
        "Expected returning via the sample HTMX shell to auto-apply the favourite "
        "that was initially selected by the server-rendered URL state."
    )
    page.wait_for_load_state("networkidle")
    expect(page.locator("#content")).to_contain_text("My List of Books")
    expect(page.locator("#filterToggleBtn")).to_be_visible()

    open_filters_panel(page)
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)


def test_matching_remembered_favourite_clears_stale_dirty_state(
    page, client, books_url, sample_books
):
    """A remembered favourite that matches rendered state should not stay dirty."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-stale-dirty-matching-favourite-user",
    )
    target_book = sample_books[0]
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Stale dirty match",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(f"{books_url}?{urlencode({'title': target_book.title, 'page_size': '5'})}")
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)
    seed_filter_favourite_browser_state(
        page,
        selected_favourite_id=str(favourite.pk),
        dirty_favourite_id=str(favourite.pk),
    )

    apply_request_urls = []
    page.on(
        "request",
        lambda request: apply_request_urls.append(request.url)
        if "/powercrud/favourites/apply/" in request.url
        else None,
    )
    page.evaluate(
        """
        () => {
            const root = document.querySelector('[data-powercrud-object-list="true"]');
            window.initPowercrud(root);
        }
        """
    )
    page.wait_for_timeout(500)

    dirty_after_bootstrap = page.evaluate(
        "(dirtyKey) => window.sessionStorage.getItem(dirtyKey)",
        DIRTY_FAVOURITE_STORAGE_KEY,
    )
    assert dirty_after_bootstrap is None, (
        "A remembered favourite whose saved state exactly matches the rendered list "
        "should clear a stale dirty marker."
    )
    assert apply_request_urls == [], (
        "A matching remembered favourite should not dispatch an apply request just to clear dirty state."
    )
    trigger = page.locator("[data-powercrud-filter-favourites-trigger='true']:visible").first
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-selected", "true")
    expect(trigger).to_have_attribute("data-powercrud-filter-favourites-dirty", "false")


def test_stale_dirty_remembered_favourite_auto_applies_after_shell_return(
    page, client, books_url, sample_books
):
    """Stale dirty state from a matching favourite URL must not block HTMX return apply."""

    user = login_playwright_user(
        client=client,
        page=page,
        books_url=books_url,
        username="playwright-stale-dirty-shell-return-user",
    )
    target_book = sample_books[0]
    other_book = sample_books[1]
    favourite = SavedFilterFavourite.objects.create(
        user=user,
        view_key=BOOK_VIEW_KEY,
        name="Stale dirty shell trip",
        state={
            "filters": {"title": [target_book.title]},
            "visible_filters": [],
            "sort": "",
            "page_size": "5",
        },
    )

    install_htmx_init_script(page)
    page.goto(f"{books_url}?{urlencode({'title': target_book.title, 'page_size': '5'})}")
    page.wait_for_load_state("networkidle")
    ensure_htmx_available(page)
    seed_filter_favourite_browser_state(
        page,
        selected_favourite_id=str(favourite.pk),
        dirty_favourite_id=str(favourite.pk),
        stored_view_query=urlencode({"title": other_book.title, "page_size": "5"}),
    )

    page.evaluate(
        """
        () => {
            const root = document.querySelector('[data-powercrud-object-list="true"]');
            window.initPowercrud(root);
        }
        """
    )
    page.wait_for_timeout(500)

    get_sample_navigation(page).locator("a", has_text="Authors").click()
    page.wait_for_load_state("networkidle")
    expect(page.locator("body")).to_contain_text("The Author Persons")

    with page.expect_response(
        re.compile(r"/powercrud/favourites/apply/"),
        timeout=5000,
    ) as apply_response:
        get_sample_navigation(page).get_by_label("Load books with HTMX").click()
    assert apply_response.value.ok, (
        "Expected stale dirty state to be cleared before returning via the sample HTMX shell, "
        "so the remembered favourite can auto-apply."
    )
    page.wait_for_load_state("networkidle")
    open_filters_panel(page)
    expect(page.locator("#filter-form input[name='title']")).to_have_value(target_book.title)
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)
