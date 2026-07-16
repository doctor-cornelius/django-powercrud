import re

import pytest
from django.conf import settings

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from sample.models import Author

pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
    pytest.mark.skipif(
        settings.SETTINGS_MODULE == "tests.settings_bootstrap",
        reason="This module verifies DaisyUI's Tippy integration; Bootstrap uses its native tooltip adapter.",
    ),
]


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


def wait_for_automatic_tippy_instance(page, selector: str):
    """Wait for automatic tooltip composition without invoking the public initializer."""
    page.wait_for_function(
        """
        (tooltipSelector) => {
            const element = document.querySelector(tooltipSelector);
            return element instanceof HTMLElement && Boolean(element._tippy);
        }
        """,
        arg=selector,
    )


def install_deferred_lazy_tooltip_fetch(page):
    """Install one controllable lazy-tooltip fetch without fixed timing delays."""
    page.add_init_script(
        """
        window.__powercrudLazyTooltipText = '';
        window.__powercrudLazyTooltipFetchStarted = false;
        window.__powercrudResolveLazyTooltipFetch = null;
        const originalFetch = window.fetch.bind(window);
        window.fetch = (input, init) => {
            const url = typeof input === 'string' ? input : (input?.url || '');
            if (!url.includes('/cell-tooltip/pages/')) {
                return originalFetch(input, init);
            }
            window.__powercrudLazyTooltipFetchStarted = true;
            let resolveFetch;
            const pendingFetch = new Promise((resolve) => {
                resolveFetch = resolve;
            });
            window.__powercrudResolveLazyTooltipFetch = async () => {
                resolveFetch(new Response(
                    JSON.stringify({ tooltip: window.__powercrudLazyTooltipText }),
                    {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' },
                    },
                ));
                await pendingFetch;
                await new Promise((resolve) => setTimeout(resolve, 0));
            };
            return pendingFetch;
        };
        """
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


def test_toolbar_controls_use_powercrud_tooltips(page, books_url):
    """Toolbar controls should use top-placed PowerCRUD tooltips, not native titles."""
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

    page.goto(books_url)
    page.wait_for_load_state("networkidle")

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
    }, "Expected the Vite-backed sample to expose vendor globals and stable PowerCRUD helpers."
    assert any(
        re.search(r"/static/django_assets/powercrud-[^/]+\.js(?:\?|$)", url)
        for url in requested_urls
    ), "Expected the normal sample to request the built Vite PowerCRUD entry."

    tooltip_selectors = [
        "[data-powercrud-filter-favourites-trigger='true'][data-tippy-content='Saved favourites']",
        "[data-powercrud-filter-toggle][data-tippy-content='Show filters']",
        "[data-powercrud-list-columns-trigger='true'][data-tippy-content='Choose visible columns']",
        "#page-size-form label[data-tippy-content='Rows per page']",
    ]

    for selector in tooltip_selectors:
        trigger = page.locator(selector).first
        expect(trigger).to_be_visible()
        expect(trigger).not_to_have_attribute("title", re.compile(".+"))
        wait_for_tippy_instance(page, selector)
        assert trigger.evaluate("el => Boolean(el._tippy)"), (
            f"Expected toolbar control {selector} to have a PowerCRUD Tippy instance."
        )

    filter_trigger = page.locator("[data-powercrud-filter-toggle]").first
    assert filter_trigger.evaluate("el => el._tippy.props.placement") == "top"
    filter_trigger.hover()
    expect(page.locator("[data-tippy-root] .tippy-box[data-placement^='top']")).to_be_visible()

    page_size_select = page.locator("#page-size-select")
    assert page_size_select.evaluate("el => window.getComputedStyle(el).cursor") == "pointer", (
        "Expected the page-size select to show pointer cursor on hoverable devices."
    )
    assert console_errors == [], f"Expected no Vite sample console errors, got: {console_errors}"
    assert page_errors == [], f"Expected no Vite sample page errors, got: {page_errors}"


def test_searchable_select_and_tooltip_initializers_are_idempotent_after_htmx_refresh(
    page, books_url, sample_author, sample_books
):
    """Repeated fragment initialisation should not duplicate widgets after HTMX swaps."""

    filtered_out_author = Author.objects.create(
        name="Playwright Filtered Out Author",
        bio="",
        birth_date=None,
    )
    filtered_out_book = sample_books[1]
    filtered_out_book.author = filtered_out_author
    filtered_out_book.save(update_fields=["author"])

    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    page.get_by_role("button", name=re.compile("filters", re.I)).click()

    author_select = page.locator("#filter-form select[name='author']")
    expect(author_select).to_have_count(1)
    page.wait_for_function(
        """
        () => {
            const element = document.querySelector("#filter-form select[name='author']");
            return Boolean(element && element.tomselect);
        }
        """
    )
    wait_for_tippy_instance(page, "[data-powercrud-filter-toggle]")

    for _ in range(2):
        page.evaluate(
            """
            () => {
                window.initPowercrudSearchableSelects(document);
                window.initPowercrudTooltips(document);
            }
            """
        )

    assert author_select.evaluate("el => Boolean(el.tomselect)")
    assert page.locator("#filter-form select[name='author'] + .ts-wrapper").count() == 1
    assert page.locator("[data-powercrud-filter-toggle]").first.evaluate("el => Boolean(el._tippy)")

    page.evaluate(
        """
        () => {
            const oldSelect = document.querySelector("#filter-form select[name='author']");
            const oldInstance = oldSelect.tomselect;
            const oldWrapper = oldInstance.wrapper;
            window.__powercrudSearchableLifecycle = {
                oldSelect,
                oldInstance,
                oldWrapper,
                beforeSwap: null,
            };
            const captureRestoredSelect = event => {
                const lifecycle = window.__powercrudSearchableLifecycle;
                lifecycle.beforeSwap = {
                    instanceDestroyed: !oldSelect.tomselect,
                    wrapperDisconnected: !oldWrapper.isConnected,
                    hidden: oldSelect.hidden,
                    ariaHidden: oldSelect.hasAttribute('aria-hidden'),
                    hiddenClass: oldSelect.classList.contains('ts-hidden-accessible'),
                    nativeStyleStored: oldSelect.hasAttribute('data-powercrud-native-style'),
                    nativeTabindexStored: oldSelect.hasAttribute('data-powercrud-native-tabindex'),
                };
                document.removeEventListener('htmx:beforeSwap', captureRestoredSelect);
            };
            document.addEventListener('htmx:beforeSwap', captureRestoredSelect);
        }
        """
    )

    select_single_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="author",
        option_value=str(sample_author.pk),
    )
    page.wait_for_load_state("networkidle")
    expect(page.locator("#filtered_results")).to_contain_text(sample_books[0].title)
    expect(page.locator("#filtered_results")).not_to_contain_text(filtered_out_book.title)

    author_select = page.locator("#filter-form select[name='author']")
    page.wait_for_function(
        """
        (selectedAuthor) => {
            const element = document.querySelector("#filter-form select[name='author']");
            const wrapperCount = document.querySelectorAll(
                "#filter-form select[name='author'] + .ts-wrapper"
            ).length;
            return Boolean(
                element
                && element.value === selectedAuthor
                && element.tomselect
                && wrapperCount === 1
            );
        }
        """,
        arg=str(sample_author.pk),
    )
    wait_for_tippy_instance(page, "[data-powercrud-filter-toggle]")
    lifecycle = page.evaluate(
        """
        () => {
            const state = window.__powercrudSearchableLifecycle;
            const newSelect = document.querySelector("#filter-form select[name='author']");
            state.freshInstance = newSelect.tomselect;
            return {
                beforeSwap: state.beforeSwap,
                oldSelectDisconnected: !state.oldSelect.isConnected,
                freshSelect: newSelect !== state.oldSelect,
                freshInstance: newSelect.tomselect !== state.oldInstance,
                freshWrapper: newSelect.tomselect.wrapper !== state.oldWrapper,
            };
        }
        """
    )
    assert lifecycle == {
        "beforeSwap": {
            "instanceDestroyed": True,
            "wrapperDisconnected": True,
            "hidden": False,
            "ariaHidden": False,
            "hiddenClass": False,
            "nativeStyleStored": False,
            "nativeTabindexStored": False,
        },
        "oldSelectDisconnected": True,
        "freshSelect": True,
        "freshInstance": True,
        "freshWrapper": True,
    }, "Expected HTMX teardown to restore the old native select before creating one fresh replacement."
    for _ in range(2):
        page.evaluate(
            """
            () => {
                window.initPowercrudSearchableSelects(document);
                window.initPowercrudTooltips(document);
            }
            """
        )

    assert author_select.evaluate("el => Boolean(el.tomselect)")
    assert page.locator("#filter-form select[name='author'] + .ts-wrapper").count() == 1
    assert page.evaluate(
        """
        () => document.querySelector("#filter-form select[name='author']").tomselect
            === window.__powercrudSearchableLifecycle.freshInstance
        """
    ), "Expected repeated public initialization to retain the fresh Tom Select instance."
    assert page.locator("[data-powercrud-filter-toggle]").first.evaluate("el => Boolean(el._tippy)")


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

    page.get_by_role("button", name=re.compile("filters", re.I)).click()
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


test_overflow_tooltips_reinitialize_after_htmx_refresh = pytest.mark.playwright_smoke(
    test_overflow_tooltips_reinitialize_after_htmx_refresh
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
    wait_for_automatic_tippy_instance(page, semantic_selector)
    assert semantic_trigger.get_attribute("data-tippy-content") == semantic_tooltip, (
        "Expected the sample semantic title tooltip trigger to keep the multiline tooltip text after initial page load."
    )
    assert semantic_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected the configured semantic title tooltip to have a Tippy instance on initial page load."
    )

    page.evaluate(
        """
        (selector) => {
            const trigger = document.querySelector(selector);
            for (let index = 0; index < 3; index += 1) {
                window.initPowercrudTooltips(trigger.closest('#filtered_results'));
                window.initPowercrud(trigger.closest('#filtered_results'));
            }
            const instance = trigger._tippy;
            window.__powercrudTooltipLifecycle = {
                oldTrigger: trigger,
                oldInstance: instance,
                oldPopper: instance.popper,
                beforeSwapObserved: false,
                destroyedDuringBeforeSwap: false,
                triggerConnectedDuringBeforeSwap: false,
                popperDisconnectedDuringBeforeSwap: false,
            };
            document.addEventListener('htmx:beforeSwap', () => {
                const record = window.__powercrudTooltipLifecycle;
                record.beforeSwapObserved = true;
                record.destroyedDuringBeforeSwap = record.oldInstance.state.isDestroyed === true;
                record.triggerConnectedDuringBeforeSwap = record.oldTrigger.isConnected;
                record.popperDisconnectedDuringBeforeSwap = !record.oldPopper.isConnected;
            }, { once: true });
        }
        """,
        semantic_selector,
    )
    semantic_trigger.hover()
    expect(
        page.locator("[data-tippy-root] .tippy-content", has_text=semantic_tooltip)
    ).to_have_count(1)

    page.get_by_role("button", name=re.compile("filters", re.I)).click()
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
    wait_for_automatic_tippy_instance(page, semantic_selector)
    assert semantic_trigger.get_attribute("data-tippy-content") == semantic_tooltip, (
        "Expected the sample semantic title tooltip trigger to keep the multiline tooltip text after the filtered HTMX refresh."
    )
    assert semantic_trigger.evaluate("el => Boolean(el._tippy)"), (
        "Expected the configured semantic title tooltip to regain its Tippy instance after HTMX refreshed the filtered results."
    )
    lifecycle = page.evaluate(
        """
        (selector) => {
            const record = window.__powercrudTooltipLifecycle;
            const replacement = document.querySelector(selector);
            return {
                beforeSwapObserved: record.beforeSwapObserved,
                destroyedDuringBeforeSwap: record.destroyedDuringBeforeSwap,
                triggerConnectedDuringBeforeSwap: record.triggerConnectedDuringBeforeSwap,
                popperDisconnectedDuringBeforeSwap: record.popperDisconnectedDuringBeforeSwap,
                oldTriggerDisconnected: !record.oldTrigger.isConnected,
                oldInstanceDestroyed: record.oldInstance.state.isDestroyed === true,
                oldPopperDisconnected: !record.oldPopper.isConnected,
                replacementIsFresh: replacement !== record.oldTrigger,
                replacementInstanceIsFresh: replacement._tippy !== record.oldInstance,
                replacementInstanceAlive: replacement._tippy.state.isDestroyed === false,
            };
        }
        """,
        semantic_selector,
    )
    assert lifecycle == {
        "beforeSwapObserved": True,
        "destroyedDuringBeforeSwap": True,
        "triggerConnectedDuringBeforeSwap": True,
        "popperDisconnectedDuringBeforeSwap": True,
        "oldTriggerDisconnected": True,
        "oldInstanceDestroyed": True,
        "oldPopperDisconnected": True,
        "replacementIsFresh": True,
        "replacementInstanceIsFresh": True,
        "replacementInstanceAlive": True,
    }, "Expected HTMX replacement to destroy the prior Tippy instance before installing one fresh instance."
    semantic_trigger.hover()
    expect(
        page.locator("[data-tippy-root] .tippy-content", has_text=semantic_tooltip)
    ).to_have_count(1)


test_semantic_list_cell_tooltips_reinitialize_after_htmx_refresh = (
    pytest.mark.playwright_smoke(
        test_semantic_list_cell_tooltips_reinitialize_after_htmx_refresh
    )
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


def test_lazy_semantic_list_cell_tooltip_hydrates_on_hover(
    page, books_url, sample_books
):
    """Lazy semantic list-cell tooltips should fetch content only on interaction."""
    target_book = sample_books[0]
    expected_tooltip = f"Page count: {target_book.pages}"
    tooltip_requests = []

    page.on(
        "request",
        lambda request: tooltip_requests.append(request)
        if "/cell-tooltip/pages/" in request.url
        else None,
    )

    page.set_viewport_size({"width": 900, "height": 900})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")

    assert tooltip_requests == [], (
        "Lazy sample page-count tooltip should not fetch during initial list load."
    )

    lazy_selector = (
        "td[data-field-name='pages'] "
        "[data-powercrud-tooltip='semantic-cell'][data-powercrud-tooltip-mode='lazy']"
    )
    lazy_trigger = page.locator(lazy_selector).first
    expect(lazy_trigger).to_be_visible()
    wait_for_tippy_instance(page, lazy_selector)
    assert lazy_trigger.get_attribute("data-tippy-content") == "", (
        "Lazy tooltip trigger should start without resolved semantic content."
    )

    with page.expect_response(
        lambda response: "/cell-tooltip/pages/" in response.url
        and response.status == 200
    ):
        lazy_trigger.hover()
    page.wait_for_function(
        """
        ({ selector, expected }) => {
            const element = document.querySelector(selector);
            return element?.getAttribute('data-tippy-content') === expected;
        }
        """,
        arg={"selector": lazy_selector, "expected": expected_tooltip},
    )

    tooltip_content = page.locator(
        "[data-tippy-root] .tippy-content",
        has_text=expected_tooltip,
    ).last
    expect(tooltip_content).to_be_visible()
    assert len(tooltip_requests) == 1, (
        "First hover should make exactly one lazy tooltip request for the rendered cell."
    )

    page.mouse.move(0, 0)
    lazy_trigger.hover()
    page.wait_for_timeout(300)
    assert len(tooltip_requests) == 1, (
        "Repeated hover on the same rendered cell should reuse the resolved tooltip content."
    )


def test_lazy_semantic_list_cell_tooltip_does_not_replay_after_pointer_leaves(
    page, books_url, sample_books
):
    """Lazy semantic tooltips should not appear after the pointer leaves."""
    target_book = sample_books[0]
    expected_tooltip = f"Page count: {target_book.pages}"
    lazy_selector = (
        "td[data-field-name='pages'] "
        "[data-powercrud-tooltip='semantic-cell'][data-powercrud-tooltip-mode='lazy']"
    )
    install_deferred_lazy_tooltip_fetch(page)
    page.set_viewport_size({"width": 900, "height": 900})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    page.evaluate(
        "(tooltip) => { window.__powercrudLazyTooltipText = tooltip; }",
        expected_tooltip,
    )

    lazy_trigger = page.locator(lazy_selector).first
    expect(lazy_trigger).to_be_visible()
    wait_for_tippy_instance(page, lazy_selector)

    lazy_trigger.hover()
    page.wait_for_function(
        "() => window.__powercrudLazyTooltipFetchStarted === true"
    )

    page.mouse.move(0, 0)
    page.evaluate("window.__powercrudResolveLazyTooltipFetch()")
    page.wait_for_function(
        """
        ({ selector, expected }) => {
            const element = document.querySelector(selector);
            return element?.getAttribute('data-tippy-content') === expected;
        }
        """,
        arg={"selector": lazy_selector, "expected": expected_tooltip},
    )

    stale_tooltip = page.locator(
        "[data-tippy-root] .tippy-content",
        has_text=expected_tooltip,
    )
    expect(stale_tooltip).to_have_count(0)


def test_lazy_semantic_list_cell_tooltip_does_not_replay_after_htmx_detaches_trigger(
    page, books_url, sample_author, sample_books
):
    """A delayed lazy response should not revive a tooltip whose source was swapped out."""
    target_book = sample_books[0]
    expected_tooltip = f"Detached page count: {target_book.pages}"
    lazy_selector = (
        "td[data-field-name='pages'] "
        "[data-powercrud-tooltip='semantic-cell'][data-powercrud-tooltip-mode='lazy']"
    )
    install_deferred_lazy_tooltip_fetch(page)
    page.set_viewport_size({"width": 900, "height": 900})
    page.goto(books_url)
    page.wait_for_load_state("networkidle")
    page.evaluate(
        "(tooltip) => { window.__powercrudLazyTooltipText = tooltip; }",
        expected_tooltip,
    )

    lazy_trigger = page.locator(lazy_selector).first
    expect(lazy_trigger).to_be_visible()
    wait_for_automatic_tippy_instance(page, lazy_selector)
    page.evaluate(
        """
        (selector) => {
            const trigger = document.querySelector(selector);
            window.__powercrudDetachedLazyTooltip = {
                trigger,
                instance: trigger._tippy,
            };
        }
        """,
        lazy_selector,
    )
    lazy_trigger.hover()
    page.wait_for_function(
        "() => window.__powercrudLazyTooltipFetchStarted === true"
    )

    page.get_by_role("button", name=re.compile("filters", re.I)).click()
    select_single_value(
        page=page,
        container=page.locator("#filter-form"),
        field_name="author",
        option_value=str(sample_author.pk),
    )
    page.wait_for_function(
        """
        () => {
            const record = window.__powercrudDetachedLazyTooltip;
            return !record.trigger.isConnected && record.instance.state.isDestroyed === true;
        }
        """
    )
    replacement_trigger = page.locator(lazy_selector).first
    expect(replacement_trigger).to_be_visible()
    wait_for_automatic_tippy_instance(page, lazy_selector)

    page.evaluate("async () => { await window.__powercrudResolveLazyTooltipFetch(); }")

    detached_state = page.evaluate(
        """
        (selector) => {
            const record = window.__powercrudDetachedLazyTooltip;
            const replacement = document.querySelector(selector);
            return {
                oldTriggerDisconnected: !record.trigger.isConnected,
                oldInstanceDestroyed: record.instance.state.isDestroyed === true,
                oldStateLoaded: record.trigger.dataset.powercrudTooltipLazyState === 'loaded',
                replacementIsFresh: replacement !== record.trigger,
                replacementState: replacement.dataset.powercrudTooltipLazyState || '',
                replacementContent: replacement.getAttribute('data-tippy-content') || '',
            };
        }
        """,
        lazy_selector,
    )
    assert detached_state == {
        "oldTriggerDisconnected": True,
        "oldInstanceDestroyed": True,
        "oldStateLoaded": False,
        "replacementIsFresh": True,
        "replacementState": "",
        "replacementContent": "",
    }, "Expected the detached lazy response to leave both the old and replacement triggers unresolved."
    stale_tooltip = page.locator(
        "[data-tippy-root] .tippy-content",
        has_text=expected_tooltip,
    )
    expect(stale_tooltip).to_have_count(0)
