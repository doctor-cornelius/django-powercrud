import re

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from sample.models import Author

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def select_single_value(page, container, field_name: str, option_value: str):
    """Select a single option, preferring Tom Select when present."""
    select = container.locator(f"select[name='{field_name}']")
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
    tomselect_ready = select.evaluate("el => Boolean(el.tomselect)")
    if tomselect_ready:
        select.evaluate(
            """
            (el, value) => {
                el.tomselect.setValue(String(value));
            }
            """,
            option_value,
        )
        expect(select).to_have_value(option_value)
        return
    select.select_option(option_value)


def test_overflow_tooltips_reinitialize_after_htmx_refresh(page, books_url, sample_author, sample_books):
    """A truncated cell should keep its Tippy instance after HTMX refreshes the table."""
    long_title = "Existing Playwright Book With A Deliberately Very Long Title For Tooltip Coverage"
    target_book = sample_books[0]
    target_book.title = long_title
    target_book.save(update_fields=["title"])

    other_author = Author.objects.create(
        name="Tooltip Filter Author",
        bio="",
        birth_date=None,
    )
    sample_books[1].author = other_author
    sample_books[1].save(update_fields=["author"])

    page.set_viewport_size({"width": 900, "height": 900})
    page.add_init_script(
        """
        () => {
            const style = document.createElement('style');
            style.id = 'playwright-tooltip-overflow-style';
            style.textContent = `
                td[data-field-name="a_really_long_property_header_for_title"] [data-powercrud-tooltip="overflow"] {
                    display: block;
                    max-width: 12ch;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
            `;
            const attachStyle = () => {
                if (document.getElementById(style.id)) {
                    return;
                }
                document.head.appendChild(style.cloneNode(true));
            };
            if (document.head) {
                attachStyle();
            } else {
                document.addEventListener('DOMContentLoaded', attachStyle, { once: true });
            }
        }
        """
    )
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    overflow_trigger = page.locator(
        "td[data-field-name='a_really_long_property_header_for_title'] "
        f"[data-powercrud-tooltip='overflow'][data-tippy-content=\"{long_title}\"]"
    ).first
    expect(overflow_trigger).to_be_visible()
    assert (
        overflow_trigger.evaluate("el => el.scrollWidth > el.clientWidth")
    ), "Expected the long property cell to be visually truncated so the overflow tooltip path is exercised."
    assert (
        overflow_trigger.evaluate("el => Boolean(el._tippy)")
    ), "Expected the truncated title to have a Tippy instance on initial page load."

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    select_single_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="author",
        option_value=str(sample_author.pk),
    )

    page.wait_for_load_state("networkidle")
    overflow_trigger = page.locator(
        "td[data-field-name='a_really_long_property_header_for_title'] "
        f"[data-powercrud-tooltip='overflow'][data-tippy-content=\"{long_title}\"]"
    ).first
    expect(overflow_trigger).to_be_visible()
    assert (
        overflow_trigger.evaluate("el => Boolean(el._tippy)")
    ), "Expected the truncated property cell to regain its Tippy instance after HTMX refreshed the filtered results."
