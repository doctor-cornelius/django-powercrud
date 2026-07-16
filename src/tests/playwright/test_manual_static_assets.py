import re

import pytest
from django.conf import settings

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.skipif(
        settings.SETTINGS_MODULE == "tests.settings_bootstrap",
        reason="This module verifies the DaisyUI manual-static entry; Bootstrap has dedicated coverage.",
    ),
]


def test_manual_static_sample_loads_powercrud_module_entry(
    page, manual_static_books_url, sample_books, sample_manager_page
):
    """The manual sample path should load PowerCRUD through normal static tags."""
    del sample_manager_page
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
            hasDestroySearchableSelects: typeof window.destroyPowercrudSearchableSelects === 'function',
            hasInitTooltips: typeof window.initPowercrudTooltips === 'function',
            hasHideTooltips: typeof window.hidePowercrudTooltips === 'function',
            hasDestroyTooltips: typeof window.destroyPowercrudTooltips === 'function',
            hasCurrentFilters: typeof window.getCurrentFilters === 'function',
            hasToggleFavouriteSaveForm: typeof window.powercrudToggleFavouriteSaveForm === 'function',
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
        "hasDestroySearchableSelects": True,
        "hasInitTooltips": True,
        "hasHideTooltips": True,
        "hasDestroyTooltips": True,
        "hasCurrentFilters": True,
        "hasToggleFavouriteSaveForm": True,
    }, (
        "Expected manual static loading to expose vendor globals and PowerCRUD public helpers. "
        f"Console errors: {console_errors}; page errors: {page_errors}"
    )

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
    page.locator("[data-powercrud-list-columns='true'] summary").click()
    expect(
        page.locator("[data-powercrud-list-columns-floating-panel='true']")
    ).to_have_count(1)
    expect(
        page.locator("[data-powercrud-list-columns-floating-panel='true']")
    ).to_be_visible()
    page.keyboard.press("Escape")
    favourites_trigger = page.locator(
        "[data-powercrud-filter-favourites-trigger='true']:visible"
    ).first
    favourites_trigger.click()
    favourites_panel = page.locator(
        "[data-powercrud-filter-favourites-floating-panel='true']"
    )
    expect(favourites_panel).to_have_count(1)
    expect(favourites_panel).to_be_visible()
    assert favourites_panel.evaluate("element => element.parentElement === document.body"), (
        "Expected repeated manual init to open one body-level favourites panel."
    )
    page.keyboard.press("Escape")
    expect(favourites_panel).to_have_count(0)
    row_actions_trigger = page.locator(
        "[data-powercrud-row-actions-trigger='true']"
    ).first
    row_actions_trigger.dispatch_event("click")
    row_actions_panel = page.locator(
        "[data-powercrud-row-actions-floating-panel='true']"
    )
    expect(row_actions_panel).to_have_count(1)
    expect(row_actions_panel).to_be_visible()
    assert row_actions_panel.evaluate("element => element.parentElement === document.body"), (
        "Expected repeated manual init to open one body-level row-actions panel."
    )
    page.keyboard.press("Escape")
    expect(row_actions_panel).to_have_count(0)
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
    assert any(
        "/static/powercrud/js/runtime/daisyui-composition.js" in url
        for url in requested_urls
    ), "Expected manual static loading to follow the private DaisyUI composition import."
    assert any(
        "/static/powercrud/js/runtime/daisyui-modal-adapter.js" in url
        for url in requested_urls
    ), "Expected manual static loading to follow the private modal adapter import."
    assert any(
        "/static/powercrud/js/runtime/daisyui-action-selection-adapter.js" in url
        for url in requested_urls
    ), "Expected manual static loading to follow the private action/selection adapter import."
    assert any(
        "/static/powercrud/js/runtime/daisyui-inline-presentation-adapter.js" in url
        for url in requested_urls
    ), "Expected manual static loading to follow the private inline-presentation adapter import."
    assert any(
        "/static/powercrud/js/runtime/daisyui-list-column-presentation-adapter.js" in url
        for url in requested_urls
    ), "Expected manual static loading to follow the private list-column adapter import."
    assert any(
        "/static/powercrud/js/runtime/daisyui-filter-favourites-presentation-adapter.js" in url
        for url in requested_urls
    ), "Expected manual static loading to follow the private filter/favourites adapter import."
    assert any(
        "/static/powercrud/js/runtime/daisyui-row-action-menu-presentation-adapter.js" in url
        for url in requested_urls
    ), "Expected manual static loading to follow the private row-action menu adapter import."
    assert not any("/static/django_assets/" in url for url in requested_urls), (
        "Manual static sample should not request Vite-built django_assets files."
    )
    assert not any(re.search(r"(@vite/client|config/static/js/main\.js)", url) for url in requested_urls), (
        "Manual static sample should not request the Vite client or app entry."
    )
    assert console_errors == [], f"Expected no browser console errors, got: {console_errors}"
    assert page_errors == [], f"Expected no browser page errors, got: {page_errors}"
