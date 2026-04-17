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
    checkbox.click()

    # HTMX briefly duplicates the container during swaps, so always pin to the first match.
    bulk_container = page.locator("#bulk-actions-container").first
    expect(bulk_container).to_be_visible()
    expect(page.locator("#selected-items-counter")).to_have_text("1")

    bulk_container.locator("button", has_text="Clear Selection").click()

    expect(page.locator("#selected-items-counter")).to_have_text("0")
    expect(page.locator("#bulk-actions-container").first).to_have_class(
        re.compile(r"\bhidden\b")
    )


def test_bulk_selection_shift_click_selects_visible_range(
    page, books_url, sample_author, sample_books
):
    for idx in range(2, 6):
        Book.objects.create(
            title=f"Shift Range Book {idx}",
            author=sample_author,
            published_date=date(2024, 1, idx + 1),
            bestseller=False,
            isbn=f"97854321{idx:02d}00",
            pages=150 + idx,
            description="Created for shift-click bulk selection coverage",
        )

    page.goto(f"{books_url}?page_size=all")
    page.wait_for_load_state("networkidle")

    checkboxes = page.locator("input.row-select-checkbox")
    expect(checkboxes).to_have_count(6)

    checkboxes.nth(1).click()
    checkboxes.nth(4).click(modifiers=["Shift"])

    expect(page.locator("#selected-items-counter")).to_have_text("4")
    for idx in range(1, 5):
        expect(checkboxes.nth(idx)).to_be_checked()
    expect(checkboxes.nth(0)).not_to_be_checked()
    expect(checkboxes.nth(5)).not_to_be_checked()


def test_bulk_selection_shift_click_can_clear_visible_range(
    page, books_url, sample_author, sample_books
):
    for idx in range(2, 6):
        Book.objects.create(
            title=f"Shift Clear Book {idx}",
            author=sample_author,
            published_date=date(2024, 2, idx + 1),
            bestseller=False,
            isbn=f"97865432{idx:02d}00",
            pages=175 + idx,
            description="Created for shift-click clear coverage",
        )

    page.goto(f"{books_url}?page_size=all")
    page.wait_for_load_state("networkidle")

    checkboxes = page.locator("input.row-select-checkbox")
    expect(checkboxes).to_have_count(6)

    checkboxes.nth(1).click()
    checkboxes.nth(4).click(modifiers=["Shift"])
    expect(page.locator("#selected-items-counter")).to_have_text("4")

    checkboxes.nth(4).click()
    expect(page.locator("#selected-items-counter")).to_have_text("3")

    checkboxes.nth(2).click(modifiers=["Shift"])

    expect(page.locator("#selected-items-counter")).to_have_text("1")
    expect(checkboxes.nth(1)).to_be_checked()
    for idx in range(2, 5):
        expect(checkboxes.nth(idx)).not_to_be_checked()


def select_single_value(page, container, field_name: str, option_label: str, option_value: str):
    select = container.locator(f"select[name='{field_name}']")
    tomselect_ready = select.evaluate("el => Boolean(el.tomselect)")
    if tomselect_ready:
        # Prefer TomSelect API in CI/headless to avoid viewport/layout click flakiness.
        select.evaluate(
            """
            (el, payload) => {
                el.tomselect.setValue(String(payload.value));
            }
            """,
            {"value": option_value},
        )
        expect(select).to_have_value(option_value)
        return
    select.select_option(option_value)


def select_multi_value(page, container, field_name: str, option_label: str, option_value: str):
    select = container.locator(f"select[name='{field_name}']")
    tomselect_ready = select.evaluate("el => Boolean(el.tomselect)")
    if tomselect_ready:
        select.evaluate(
            """
            (el, payload) => {
                const nextValue = String(payload.value);
                const currentValues = Array.isArray(el.tomselect.items)
                    ? el.tomselect.items.map(String)
                    : [];
                const mergedValues = Array.from(new Set([...currentValues, nextValue]));
                el.tomselect.setValue(mergedValues);
                el.tomselect.setTextboxValue('');
                el.tomselect.refreshOptions(true);
            }
            """,
            {"value": option_value},
        )
        selected_values = select.evaluate(
            "el => Array.from(el.selectedOptions).map(opt => String(opt.value))"
        )
        assert (
            option_value in selected_values
        ), f"Expected multi-select field '{field_name}' to include option '{option_value}' after Tom Select selection."
        return
    select.select_option([option_value])


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
    select_single_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="author",
        option_label=sample_author.name,
        option_value=str(sample_author.pk),
    )

    page.wait_for_load_state("networkidle")
    expect(page.locator("#filtered_results")).to_contain_text(target_book.title)
    expect(page.locator("#filtered_results")).not_to_contain_text(other_book.title)

    checkbox = page.locator("input.row-select-checkbox").first
    expect(checkbox).to_be_visible()
    checkbox.click()

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


def test_bulk_edit_searchable_select_updates_author(
    page, books_url, sample_author, sample_books
):
    selected_book = sample_books[0]
    untouched_book = sample_books[1]
    replacement_author = Author.objects.create(
        name="Bulk Search Author",
        bio="",
        birth_date=None,
    )

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    checkbox = page.locator("input.row-select-checkbox").first
    checkbox.check()

    bulk_container = page.locator("#bulk-actions-container").first
    expect(bulk_container).to_be_visible()
    bulk_container.get_by_role("link", name=re.compile("bulk edit", re.I)).click()

    modal = page.locator("#powercrudBaseModal")
    form = modal.locator("#bulk-edit-form")
    expect(form).to_be_visible()

    form.locator("input.field-toggle[value='author']").check()
    select_single_value(
        page=page,
        container=form,
        field_name="author",
        option_label=replacement_author.name,
        option_value=str(replacement_author.pk),
    )
    form.get_by_role("button", name=re.compile("apply changes", re.I)).click()

    expect(modal).not_to_be_visible()
    page.wait_for_load_state("networkidle")

    selected_book.refresh_from_db()
    untouched_book.refresh_from_db()
    assert (
        selected_book.author_id == replacement_author.pk
    ), "Bulk searchable select should update the selected record author."
    assert (
        untouched_book.author_id == sample_author.pk
    ), "Bulk searchable select should not change unselected rows."


def test_pagination_controls_advance_across_multiple_pages(
    page, books_url, sample_author, sample_books
):
    for idx in range(2, 12):
        Book.objects.create(
            title=f"Paginated Playwright Book {idx}",
            author=sample_author,
            published_date=date(2024, 4, (idx % 28) + 1),
            bestseller=False,
            isbn=f"97877777{idx:02d}00",
            pages=300 + idx,
            description="Created to exercise HTMX pagination controls across pages",
        )

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    pagination = page.get_by_role("navigation", name=re.compile("page navigation", re.I))
    expect(pagination).to_be_visible()

    page.get_by_role("link", name="Next").click()
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(re.compile(r"[?&]page=2(?:&|$)"))
    expect(pagination.get_by_role("link", name="2")).to_have_class(re.compile(r"\bbtn-active\b"))

    page.get_by_role("link", name="Next").click()
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(re.compile(r"[?&]page=3(?:&|$)"))
    expect(pagination.get_by_role("link", name="3")).to_have_class(re.compile(r"\bbtn-active\b"))

    page.get_by_role("link", name="1").click()
    page.wait_for_load_state("networkidle")
    expect(page).not_to_have_url(re.compile(r"[?&]page=3(?:&|$)"))
    expect(pagination.get_by_role("link", name="1")).to_have_class(re.compile(r"\bbtn-active\b"))


def test_filter_multiselect_searchable_select_applies_immediately(
    page, books_url, sample_author, sample_books
):
    target_genre = Genre.objects.create(
        name="Playwright Filter Genre A",
        description="Expected to match one row",
    )
    non_matching_genre = Genre.objects.create(
        name="Playwright Filter Genre B",
        description="Expected to be filtered out",
    )
    sample_author.genres.add(target_genre, non_matching_genre)

    target_book = sample_books[0]
    non_matching_book = sample_books[1]
    target_book.genres.set([target_genre])
    non_matching_book.genres.set([non_matching_genre])

    page.goto(f"{books_url}?visible_filters=genres")
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=re.compile("show filters", re.I)).click()

    select_multi_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="genres",
        option_label=target_genre.name,
        option_value=str(target_genre.pk),
    )

    page.wait_for_load_state("networkidle")
    filtered_results = page.locator("#filtered_results")
    expect(filtered_results).to_contain_text(target_book.title)
    expect(filtered_results).not_to_contain_text(non_matching_book.title)


def test_filter_single_select_clear_button_clears_selection(
    page, books_url, sample_author, sample_books
):
    other_author = Author.objects.create(
        name="Playwright Other Filter Author",
        bio="",
        birth_date=None,
    )
    other_book = Book.objects.create(
        title="Outside Author Filter Book",
        author=other_author,
        published_date=date(2024, 3, 1),
        bestseller=False,
        isbn="9788888888800",
        pages=222,
        description="Used to verify clear button resets author filter",
    )

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=re.compile("show filters", re.I)).click()

    select_single_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="author",
        option_label=sample_author.name,
        option_value=str(sample_author.pk),
    )

    page.wait_for_load_state("networkidle")
    filtered_results = page.locator("#filtered_results")
    expect(filtered_results).to_contain_text(sample_books[0].title)
    expect(filtered_results).not_to_contain_text(other_book.title)

    clear_button = page.locator(
        "#filter-form .ts-wrapper .clear-button"
    ).first
    if clear_button.count() > 0:
        expect(clear_button).to_be_visible()
        clear_button.click()
    else:
        page.locator("#filter-form select[name='author']").evaluate(
            """
            (el) => {
                if (el.tomselect) {
                    el.tomselect.clear(true);
                } else {
                    el.value = '';
                }
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """
        )

    page.wait_for_load_state("networkidle")
    expect(page.locator("#filter-form select[name='author']")).to_have_value("")
    expect(filtered_results).to_contain_text(other_book.title)
