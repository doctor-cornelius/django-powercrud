import re

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytestmark = [pytest.mark.playwright, pytest.mark.django_db]


def test_manual_static_sample_loads_powercrud_module_entry(
    page, manual_static_books_url, sample_books
):
    """The manual sample path should load PowerCRUD through normal static tags."""
    requested_urls = []
    console_errors = []
    page_errors = []

    page.on("request", lambda request: requested_urls.append(request.url))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    page.goto(manual_static_books_url)
    page.wait_for_load_state("networkidle")

    expect(page.locator("#filtered_results")).to_contain_text(sample_books[0].title)

    runtime_ready = page.evaluate(
        """
        () => ({
            loaded: window.__powercrudRuntimeLoaded === true,
            hasHtmx: Boolean(window.htmx),
            hasTomSelect: Boolean(window.TomSelect),
            hasTippy: Boolean(window.tippy),
            hasInitPowercrud: typeof window.initPowercrud === 'function',
            hasSearchableSelects: typeof window.initPowercrudSearchableSelects === 'function',
            hasTooltips: typeof window.initPowercrudTooltips === 'function',
            hasCurrentFilters: typeof window.getCurrentFilters === 'function',
        })
        """
    )

    assert runtime_ready == {
        "loaded": True,
        "hasHtmx": True,
        "hasTomSelect": True,
        "hasTippy": True,
        "hasInitPowercrud": True,
        "hasSearchableSelects": True,
        "hasTooltips": True,
        "hasCurrentFilters": True,
    }, "Expected manual static loading to expose vendor globals and PowerCRUD public helpers."

    page.wait_for_function(
        """
        () => {
            const element = document.querySelector("#filter-form select[name='author']");
            return Boolean(element && element.tomselect);
        }
        """
    )
    assert page.locator("#filter-form select[name='author'] + .ts-wrapper").count() == 1, (
        "Expected manual static loading to initialise one TomSelect wrapper for the author filter."
    )

    tooltip_trigger = page.locator("[data-powercrud-filter-toggle]").first
    expect(tooltip_trigger).to_be_visible()
    page.wait_for_function(
        """
        () => {
            const element = document.querySelector("[data-powercrud-filter-toggle]");
            return Boolean(element && element._tippy);
        }
        """
    )
    assert tooltip_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected manual static loading to initialise PowerCRUD tooltips."
    )
    for _ in range(3):
        page.evaluate("() => window.initPowercrud(document)")

    assert page.locator("#filter-form select[name='author'] + .ts-wrapper").count() == 1, (
        "Expected repeated manual init to keep exactly one TomSelect wrapper for the author filter."
    )
    assert tooltip_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected repeated manual init to keep a PowerCRUD tooltip instance."
    )
    style_count = page.evaluate(
        """
        () => Array.from(document.querySelectorAll('style')).filter(
            style => style.textContent.includes('powercrud-range-selecting')
        ).length
        """
    )
    assert style_count == 1, (
        "Expected repeated manual init to keep exactly one range-selection suppression style."
    )

    assert any("/static/powercrud/js/powercrud.js" in url for url in requested_urls), (
        "Expected the manual sample to request the stable PowerCRUD module entry."
    )
    assert any("/static/powercrud/js/runtime/startup.js" in url for url in requested_urls), (
        "Expected the browser to follow the stable module entry's internal runtime imports."
    )
    assert not any("/static/django_assets/" in url for url in requested_urls), (
        "Manual static sample should not request Vite-built django_assets files."
    )
    assert not any(re.search(r"(@vite/client|config/static/js/main\.js)", url) for url in requested_urls), (
        "Manual static sample should not request the Vite client or app entry."
    )
    assert console_errors == [], f"Expected no browser console errors, got: {console_errors}"
    assert page_errors == [], f"Expected no browser page errors, got: {page_errors}"
