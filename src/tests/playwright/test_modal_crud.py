import re
from uuid import uuid4

import pytest
from django.conf import settings

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from sample.models import Book

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]

BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def using_bootstrap_pack() -> bool:
    """Return whether the active browser settings select Bootstrap."""
    return settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR


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
    if modal.count():
        expect(modal).to_be_visible()
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


test_create_book_via_modal = pytest.mark.playwright_smoke(test_create_book_via_modal)


def test_portable_per_trigger_modal_presentation_is_applied_and_reset(page, books_url):
    """Both pack adapters must apply semantic trigger settings without leaking them."""

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    modal = page.locator("#powercrudBaseModal")
    modal_box = modal.locator("[data-powercrud-modal-box]")
    modal_selector = "#powercrudBaseModal[data-powercrud-modal]"

    modal.evaluate(
        """
        element => {
            const duplicate = element.cloneNode(true);
            duplicate.dataset.powercrudTestDuplicate = 'true';
            element.after(duplicate);
        }
        """
    )
    expect(page.locator(modal_selector)).to_have_count(2)

    page.locator("[data-powercrud-extra-buttons-dropdown='true'] summary").click()
    trigger = page.locator(
        "[data-powercrud-extra-buttons-dropdown='true'] a",
        has_text="Home in Modal!",
    ).first
    trigger.evaluate(
        """
        element => {
            element.dataset.powercrudModalSize = 'wide';
            element.dataset.powercrudModalMaxWidth = '60rem';
            element.dataset.powercrudModalMaxHeight = '75dvh';
            element.dataset.powercrudModalScroll = 'modal';
            element.dataset.powercrudModalFullscreen = 'false';
            element.dataset.powercrudModalVerticalAlignment = 'top';
        }
        """
    )
    trigger.click()

    expect(page.locator(modal_selector)).to_have_count(1)
    expect(modal).to_be_visible()
    expect(modal.locator("#powercrudModalContent")).to_contain_text("Home")
    if using_bootstrap_pack():
        expect(modal_box).to_have_class(re.compile(r"\bmodal-lg\b"))
        expect(modal_box).to_have_class(re.compile(r"\bpc-bootstrap-modal-scroll-shell\b"))
        assert modal_box.evaluate("element => element.style.getPropertyValue('--bs-modal-width')")
        assert modal_box.evaluate("element => element.style.getPropertyValue('--pc-modal-max-height')")
    else:
        expect(modal).to_have_class(re.compile(r"\bmodal-top\b"))
        expect(modal_box).to_have_class(re.compile(r"\bmax-w-4xl\b"))
        assert modal_box.evaluate("element => element.style.maxWidth")
        assert modal_box.evaluate("element => element.style.maxHeight")
        assert modal_box.evaluate("element => element.style.overflowY") == "auto"
    page.wait_for_load_state("networkidle")

    modal.evaluate(
        """
        element => {
            const duplicate = element.cloneNode(true);
            duplicate.removeAttribute('open');
            duplicate.dataset.powercrudTestClosedDuplicate = 'true';
            element.after(duplicate);
        }
        """
    )
    expect(page.locator(modal_selector)).to_have_count(2)
    page.evaluate("() => window.initPowercrud(document)")
    expect(page.locator(modal_selector)).to_have_count(1)
    expect(modal).to_be_visible()
    expect(page.locator("[data-powercrud-test-closed-duplicate='true']")).to_have_count(0)

    if using_bootstrap_pack():
        modal.get_by_role("button", name="Close").click()
    else:
        page.keyboard.press("Escape")
    expect(modal).not_to_be_visible()

    page.get_by_role("link", name=re.compile("create", re.I)).click()
    expect(modal).to_be_visible()
    expect(modal.locator("#powercrudModalContent form")).to_be_visible()
    if using_bootstrap_pack():
        expect(modal_box).to_have_class(re.compile(r"\bmodal-dialog-centered\b"))
        expect(modal_box).to_have_class(re.compile(r"\bmodal-dialog-scrollable\b"))
        assert not modal_box.evaluate("element => element.style.getPropertyValue('--bs-modal-width')")
    else:
        expect(modal).to_have_class(re.compile(r"\bmodal-middle\b"))
        expect(modal_box).to_have_class(re.compile(r"\bmax-w-lg\b"))
        assert not modal_box.evaluate("element => element.style.maxWidth")

    if using_bootstrap_pack():
        modal.get_by_role("button", name="Close").click()
    else:
        page.keyboard.press("Escape")
    expect(modal).not_to_be_visible()
    page.locator("[data-powercrud-extra-buttons-dropdown='true'] summary").click()
    trigger.evaluate(
        """element => { element.dataset.powercrudModalFullscreen = 'true'; }"""
    )
    trigger.click()
    expect(modal).to_be_visible()
    if using_bootstrap_pack():
        expect(modal_box).to_have_class(re.compile(r"\bmodal-fullscreen\b"))
    else:
        assert modal_box.evaluate("element => element.style.width") == "100dvw"
        assert modal_box.evaluate("element => element.style.height") == "100dvh"
