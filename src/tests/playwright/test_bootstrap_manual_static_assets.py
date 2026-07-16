"""Bootstrap manual-static loading and lifecycle smoke coverage."""

import re

import pytest

pytest.importorskip("playwright.sync_api")
from django.conf import settings
from playwright.sync_api import expect


pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.skipif(
        settings.SETTINGS_MODULE != "tests.settings_bootstrap",
        reason="Bootstrap manual-static coverage requires the optional Bootstrap settings overlay.",
    ),
]


def test_bootstrap_manual_static_loads_selected_runtime_without_vite(
    page, manual_static_books_url, sample_books, sample_manager_page
):
    """The Bootstrap manual-static shell should load its own runtime and stay repeatable."""
    del sample_manager_page
    requested_urls = []
    console_errors = []
    page_errors = []
    page.on("request", lambda request: requested_urls.append(request.url))
    page.on(
        "console",
        lambda message: console_errors.append(message.text)
        if message.type == "error"
        else None,
    )
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
            hasBootstrap: Boolean(window.bootstrap),
            hasInitPowercrud: typeof window.initPowercrud === 'function',
            hasBootstrapModal: typeof window.bootstrap?.Modal === 'function',
            hasBootstrapTooltip: typeof window.bootstrap?.Tooltip === 'function',
            hasTippy: Boolean(window.tippy),
        })
        """
    )
    assert runtime_ready == {
        "loaded": True,
        "hasHtmx": True,
        "hasTomSelect": True,
        "hasBootstrap": True,
        "hasInitPowercrud": True,
        "hasBootstrapModal": True,
        "hasBootstrapTooltip": True,
        "hasTippy": False,
    }, "Bootstrap manual-static loading should expose only the selected presentation runtime."

    page.locator("#filterToggleBtn").click()
    page.wait_for_function(
        """
        () => {
            const element = document.querySelector("#filter-form select[name='author']");
            return Boolean(element && element.tomselect);
        }
        """
    )
    for _ in range(3):
        page.evaluate("() => window.initPowercrud(document)")

    assert page.locator("#filter-form select[name='author'] + .ts-wrapper").count() == 1, (
        "Repeated Bootstrap manual-static initialization should keep one TomSelect wrapper."
    )

    assert any(
        "/static/node_modules/bootstrap/dist/css/bootstrap.min.css" in url
        for url in requested_urls
    ), "Bootstrap manual-static loading should request the vendor stylesheet."
    assert any(
        "/static/node_modules/bootstrap/dist/js/bootstrap.bundle.min.js" in url
        for url in requested_urls
    ), "Bootstrap manual-static loading should request the vendor bundle."
    assert any(
        "/static/powercrud/contrib/bootstrap5/css/bootstrap5.css" in url
        for url in requested_urls
    ), "Bootstrap manual-static loading should request package-owned Bootstrap CSS."
    assert any(
        "/static/powercrud/contrib/bootstrap5/js/bootstrap5.js" in url
        for url in requested_urls
    ), "Bootstrap manual-static loading should request the package-owned entry."
    assert any(
        "/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-composition.js" in url
        for url in requested_urls
    ), "Bootstrap manual-static loading should reach the private Bootstrap composition."
    assert not any(
        re.search(r"(@vite/client|config/static/js/bootstrap5\.js|/static/django_assets/)", url)
        for url in requested_urls
    ), "Bootstrap manual-static loading should not request Vite assets."
    assert console_errors == [], f"Expected no Bootstrap console errors, got: {console_errors}"
    assert page_errors == [], f"Expected no Bootstrap page errors, got: {page_errors}"
