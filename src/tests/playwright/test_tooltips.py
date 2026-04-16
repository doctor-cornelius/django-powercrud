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


def wait_for_tippy_instance(page, selector: str):
    """Wait until the tooltip target exists, is visible, and has a Tippy instance."""
    page.wait_for_function(
        """
        (tooltipSelector) => {
            const element = document.querySelector(tooltipSelector);
            if (!(element instanceof HTMLElement)) {
                return false;
            }
            const style = window.getComputedStyle(element);
            const isVisible = style.visibility !== 'hidden' && style.display !== 'none';
            if (isVisible && !element._tippy && typeof window.initPowercrudTooltips === 'function') {
                window.initPowercrudTooltips(document);
            }
            return isVisible && Boolean(element._tippy);
        }
        """,
        arg=selector,
    )


def wait_for_overflow_truncation(page, selector: str):
    """Wait until the tooltip target is visibly truncated."""
    page.wait_for_function(
        """
        (tooltipSelector) => {
            const element = document.querySelector(tooltipSelector);
            if (!(element instanceof HTMLElement)) {
                return false;
            }
            return element.scrollWidth > element.clientWidth;
        }
        """,
        arg=selector,
    )


def test_overflow_tooltips_reinitialize_after_htmx_refresh(
    page, books_url, sample_author, sample_books
):
    """A truncated cell should keep its Tippy instance after HTMX refreshes the table."""
    long_author_name = "Playwright Author With A Deliberately Very Long Name For Overflow Tooltip Coverage"
    filtered_out_title = sample_books[1].title
    sample_author.name = long_author_name
    sample_author.save(update_fields=["name"])

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
                td[data-field-name="author"] {
                    width: 12ch !important;
                    min-width: 12ch !important;
                    max-width: 12ch !important;
                }
                td[data-field-name="author"] [data-powercrud-tooltip="overflow"] {
                    display: block !important;
                    width: 12ch !important;
                    min-width: 0 !important;
                    max-width: 12ch !important;
                    overflow: hidden !important;
                    text-overflow: ellipsis !important;
                    white-space: nowrap !important;
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

    overflow_selector = (
        "td[data-field-name='author'] "
        f"[data-powercrud-tooltip='overflow'][data-tippy-content=\"{long_author_name}\"]"
    )
    overflow_trigger = page.locator(overflow_selector).first
    expect(overflow_trigger).to_be_visible()
    wait_for_overflow_truncation(page, overflow_selector)
    assert overflow_trigger.evaluate("el => el.scrollWidth > el.clientWidth"), (
        "Expected the long author cell to be visually truncated so the overflow tooltip path is exercised."
    )
    wait_for_tippy_instance(page, overflow_selector)
    assert overflow_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected the truncated author value to have a Tippy instance on initial page load."
    )

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    select_single_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="author",
        option_value=str(sample_author.pk),
    )

    filtered_out_cell = page.locator(
        "td[data-field-name='title']",
        has_text=filtered_out_title,
    )
    expect(filtered_out_cell).to_have_count(
        0,
        timeout=15000,
    )

    overflow_trigger = page.locator(overflow_selector).first
    expect(overflow_trigger).to_be_visible()
    wait_for_tippy_instance(page, overflow_selector)
    assert overflow_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected the truncated property cell to regain its Tippy instance after HTMX refreshed the filtered results."
    )


def test_semantic_list_cell_tooltips_reinitialize_after_htmx_refresh(
    page, books_url, sample_author, sample_books
):
    """Configured semantic list-cell tooltips should survive HTMX table refreshes."""
    target_book = sample_books[0]
    filtered_out_book = sample_books[1]
    semantic_tooltip = f"{sample_author.name}\n{target_book.pages} pages"

    other_author = Author.objects.create(
        name="Semantic Tooltip Filter Author",
        bio="",
        birth_date=None,
    )
    filtered_out_book.author = other_author
    filtered_out_book.save(update_fields=["author"])

    page.set_viewport_size({"width": 900, "height": 900})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    semantic_selector = "td[data-field-name='title'] [data-powercrud-tooltip='semantic-cell']"
    semantic_trigger = page.locator(semantic_selector).first
    expect(semantic_trigger).to_be_visible()
    wait_for_tippy_instance(page, semantic_selector)
    assert semantic_trigger.get_attribute("data-tippy-content") == semantic_tooltip, (
        "Expected the sample semantic title tooltip trigger to keep the multiline tooltip text after initial page load."
    )
    assert semantic_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected the configured semantic title tooltip to have a Tippy instance on initial page load."
    )

    page.get_by_role("button", name=re.compile("show filters", re.I)).click()
    select_single_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="author",
        option_value=str(sample_author.pk),
    )

    filtered_out_cell = page.locator(
        "td[data-field-name='title']",
        has_text=filtered_out_book.title,
    )
    expect(filtered_out_cell).to_have_count(
        0,
        timeout=15000,
    )

    semantic_trigger = page.locator(semantic_selector).first
    expect(semantic_trigger).to_be_visible()
    wait_for_tippy_instance(page, semantic_selector)
    assert semantic_trigger.get_attribute("data-tippy-content") == semantic_tooltip, (
        "Expected the sample semantic title tooltip trigger to keep the multiline tooltip text after the filtered HTMX refresh."
    )
    assert semantic_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected the configured semantic title tooltip to regain its Tippy instance after HTMX refreshed the filtered results."
    )


def test_semantic_list_cell_tooltips_preserve_multiline_text(
    page, books_url, sample_author, sample_books
):
    """Semantic list-cell tooltips should preserve newline-separated text in the rendered tooltip."""
    target_book = sample_books[0]
    expected_tooltip = f"{sample_author.name}\n{target_book.pages} pages"

    page.set_viewport_size({"width": 900, "height": 900})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    semantic_selector = "td[data-field-name='title'] [data-powercrud-tooltip='semantic-cell']"
    semantic_trigger = page.locator(semantic_selector).first
    expect(semantic_trigger).to_be_visible()
    wait_for_tippy_instance(page, semantic_selector)

    assert semantic_trigger.get_attribute("data-tippy-content") == expected_tooltip, (
        "Expected the sample semantic title tooltip trigger to keep the newline-separated tooltip text in its data attribute."
    )

    semantic_trigger.hover()
    tooltip_content = page.locator(
        "[data-tippy-root] .tippy-content",
        has_text=sample_author.name,
    ).last
    expect(tooltip_content).to_be_visible()

    assert tooltip_content.evaluate("el => el.innerText") == expected_tooltip, (
        "Expected the rendered semantic tooltip bubble to preserve the newline between tooltip lines."
    )
    assert tooltip_content.evaluate(
        "el => window.getComputedStyle(el).whiteSpace"
    ) == "pre-line", (
        "Expected the rendered semantic tooltip bubble to use pre-line whitespace handling so newline-separated text displays across lines."
    )
    assert tooltip_content.evaluate(
        """
        (el) => {
            const style = window.getComputedStyle(el);
            const fontSize = parseFloat(style.fontSize || '14');
            const rawLineHeight = parseFloat(style.lineHeight || '');
            const lineHeight = Number.isFinite(rawLineHeight) ? rawLineHeight : (fontSize * 1.4);
            return el.getBoundingClientRect().height >= (lineHeight * 2);
        }
        """
    ), (
        "Expected the rendered semantic tooltip bubble to occupy at least two lines of height when the tooltip text contains a newline."
    )
