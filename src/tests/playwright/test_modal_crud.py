import re
from uuid import uuid4

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from sample.models import Book

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def select_single_value(page, form, field_name: str, option_label: str, option_value: str):
    select = form.locator(f"select[name='{field_name}']")
    ts_wrapper = form.locator(f"select[name='{field_name}'] + .ts-wrapper")
    if ts_wrapper.count() > 0:
        native_hidden = select.evaluate(
            """
            (el) => {
                const style = window.getComputedStyle(el);
                return (
                    el.hidden
                    || style.display === 'none'
                    || style.visibility === 'hidden'
                    || el.getAttribute('aria-hidden') === 'true'
                );
            }
            """
        )
        assert native_hidden, (
            f"Native select '{field_name}' should be hidden when TomSelect enhancement is active."
        )
        control_input = ts_wrapper.locator("input").first
        input_in_viewport = control_input.evaluate(
            """
            (el) => {
                const rect = el.getBoundingClientRect();
                return (
                    rect.width > 0
                    && rect.height > 0
                    && rect.top >= 0
                    && rect.left >= 0
                    && rect.bottom <= window.innerHeight
                    && rect.right <= window.innerWidth
                );
            }
            """
        )
        if input_in_viewport:
            control_input.click()
            control_input.fill(option_label)
            option = page.locator(".ts-dropdown .option", has_text=option_label).first
            expect(option).to_be_visible()
            option.click()
        else:
            # In some headless viewport/layout combinations, TomSelect's input
            # can end up outside the viewport. Use TomSelect API directly so
            # modal CRUD tests stay deterministic.
            select.evaluate(
                """
                (el, payload) => {
                    if (!el.tomselect) {
                        throw new Error('Expected TomSelect instance for modal helper');
                    }
                    el.tomselect.setValue(String(payload.value));
                }
                """,
                {"value": option_value},
            )
        expect(select).to_have_value(option_value)
        return
    select.select_option(option_value)


def test_create_book_via_modal(page, books_url, sample_author, sample_genre):
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    expect(page.get_by_role("heading", name=re.compile("book", re.I))).to_be_visible()

    create_link = page.get_by_role("link", name=re.compile("create", re.I))
    expect(create_link).to_be_visible()
    create_link.click()

    modal = page.locator("#powercrudBaseModal")
    form = None
    if modal.count() and modal.is_visible():
        modal_content = modal.locator("#powercrudModalContent")
        form = modal_content.locator("form")
        expect(form).to_be_visible()
    else:
        page.wait_for_url(re.compile(r"/sample/bigbook/(new|create)/"))
        form = page.locator("form").first

    title = f"Playwright Title {uuid4().hex[:6]}"
    isbn = f"978{uuid4().hex[:10]}"

    form.locator("input[name='title']").fill(title)
    select_single_value(
        page=page,
        form=form,
        field_name="author",
        option_label=sample_author.name,
        option_value=str(sample_author.pk),
    )
    form.locator("input[name='published_date']").fill("2025-01-01")
    form.locator("select[name='genres']").select_option(str(sample_genre.pk))
    form.locator("input[name='isbn']").fill(isbn)
    form.locator("input[name='pages']").fill("321")
    description = form.locator("textarea[name='description']")
    if description.count() > 0:
        description.fill("Created via Playwright")

    form.get_by_role("button", name=re.compile("save", re.I)).click()

    if modal.count():
        expect(modal).not_to_be_visible()
        page.wait_for_load_state("networkidle")

    expect(page.locator("table")).to_contain_text(title)

    assert Book.objects.filter(title=title, author=sample_author).exists(), (
        "Submitting the create modal should persist a Book linked to the selected author."
    )
