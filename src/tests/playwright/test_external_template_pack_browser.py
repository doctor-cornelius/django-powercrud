"""Browser acceptance for a package-shaped external template-pack declaration."""

from urllib.parse import urljoin

import pytest
from django.conf import settings
pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect


EXTERNAL_SELECTOR = "tests.template_pack_fixtures:external_browser_template_pack"

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.skipif(
        settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") != EXTERNAL_SELECTOR,
        reason="External browser acceptance requires the external-pack settings overlay.",
    ),
]


def test_external_pack_loads_its_adapter_and_core_runtime(page, books_url):
    """An external declaration must load its adapter and the stable runtime on a project page."""
    requested_urls = []
    page.on("request", lambda request: requested_urls.append(request.url))

    page.goto(urljoin(books_url, "/"))
    page.wait_for_load_state("networkidle")

    expect(page.locator("#content")).to_be_visible()
    runtime = page.evaluate(
        """
        () => ({
            loaded: window.__powercrudRuntimeLoaded === true,
            adapter: window.PowerCRUDAdapter?.identity,
            initialised: document.documentElement.dataset.externalPackAdapterInitialised,
            init: typeof window.initPowercrud === 'function',
        })
        """
    )
    assert runtime == {
        "loaded": True,
        "adapter": "external-browser-fixture",
        "initialised": "true",
        "init": True,
    }, "Expected the external pack adapter and stable PowerCRUD runtime to initialise together."
    assert any(
        "/static/powercrud/packs/external-browser-fixture/js/adapter.js" in url
        for url in requested_urls
    ), "Expected manual-static loading to request the external package's declared adapter."
