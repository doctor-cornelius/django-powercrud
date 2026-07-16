import re

import pytest
from django.conf import settings

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect


pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]

BOOTSTRAP_SELECTOR = "powercrud.contrib.bootstrap5:template_pack"


def using_bootstrap_pack() -> bool:
    """Return whether the active browser settings select Bootstrap."""
    return settings.POWERCRUD_SETTINGS.get("POWERCRUD_TEMPLATE_PACK") == BOOTSTRAP_SELECTOR


def test_row_actions_menu_stays_visible_for_top_and_bottom_rows(
    page, books_url, sample_books
):
    """Keep floating row-action menus fully visible on short pages."""
    del sample_books

    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    row_action_triggers = page.locator("[data-powercrud-row-actions-trigger='true']")
    expect(row_action_triggers).to_have_count(2)

    for index in range(2):
        trigger = row_action_triggers.nth(index)
        trigger.dispatch_event("click")

        floating_panel = page.locator(
            "[data-powercrud-row-actions-floating-panel='true']"
        )
        expect(floating_panel).to_have_count(1)
        expect(floating_panel).to_be_visible()
        expect(trigger).to_have_attribute("aria-expanded", "true")
        assert floating_panel.evaluate("element => element.parentElement === document.body"), (
            "Expected the row-actions shell to be cloned directly under the document body."
        )
        assert floating_panel.evaluate("element => getComputedStyle(element).position") == "fixed", (
            "Expected the detached row-actions shell to use fixed viewport positioning."
        )
        expect(floating_panel).to_contain_text("Normal Edit")
        expect(floating_panel).to_contain_text("Description Preview")

        panel_box = floating_panel.bounding_box()
        viewport = page.viewport_size

        assert panel_box is not None, (
            f"Expected floating row-actions panel for visible row index {index} to expose a measurable bounding box."
        )
        assert viewport is not None, (
            "Expected Playwright to provide a viewport size so row-actions visibility can be verified."
        )
        assert panel_box["y"] >= -1, (
            "Expected floating row-actions panel for visible row index "
            f"{index} to stay inside the top of the viewport, but its top was {panel_box['y']}."
        )
        assert panel_box["y"] + panel_box["height"] <= viewport["height"] + 1, (
            "Expected floating row-actions panel to stay inside the bottom of the viewport "
            f"for visible row index {index}, but its bottom was {panel_box['y'] + panel_box['height']} while the viewport height was {viewport['height']}."
        )
        assert panel_box["x"] >= -1, (
            "Expected the floating row-actions panel to stay inside the viewport's left edge."
        )
        assert panel_box["x"] + panel_box["width"] <= viewport["width"] + 1, (
            "Expected the floating row-actions panel to stay inside the viewport's right edge."
        )
        if index:
            expect(row_action_triggers.nth(index - 1)).to_have_attribute(
                "aria-expanded", "false"
            )

    page.keyboard.press("Escape")
    expect(page.locator("[data-powercrud-row-actions-floating-panel='true']")).to_have_count(0)
    expect(row_action_triggers.last).to_have_attribute("aria-expanded", "false")


test_row_actions_menu_stays_visible_for_top_and_bottom_rows = pytest.mark.playwright_smoke(
    test_row_actions_menu_stays_visible_for_top_and_bottom_rows
)


def test_row_actions_floating_panel_modal_action_uses_cloned_trigger_presentation(
    page, books_url, sample_books
):
    """A cloned row action must retain its portable modal-presentation metadata."""

    target_book = sample_books[0]
    target_book.description = "Description Preview Playwright Body"
    target_book.save(update_fields=["description"])

    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    page.locator("[data-powercrud-row-actions-trigger='true']").first.dispatch_event("click")
    floating_panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(floating_panel).to_be_visible()
    description_preview = floating_panel.get_by_role("link", name="Description Preview")
    expect(description_preview).to_have_attribute(
        "data-powercrud-modal-max-width", "64rem"
    )
    expect(description_preview).to_have_attribute(
        "data-powercrud-modal-size", "default"
    )
    description_preview.click()

    modal = page.locator("#powercrudBaseModal")
    expect(modal).to_be_visible()
    expect(modal.locator("#powercrudModalContent")).to_contain_text("Description Preview")
    expect(modal.locator("#powercrudModalContent")).to_contain_text(target_book.description)
    modal_box = modal.locator("[data-powercrud-modal-box]")
    expect(modal_box).to_have_class(
        re.compile(r"\bmodal-dialog\b" if using_bootstrap_pack() else r"\bmax-w-lg\b")
    )
    if using_bootstrap_pack():
        assert "64rem" in modal_box.evaluate(
            "element => element.style.getPropertyValue('--bs-modal-width')"
        )
    else:
        assert "64rem" in modal_box.evaluate("element => element.style.maxWidth")
    expect(floating_panel).to_have_count(0)


def test_row_actions_menu_hydrates_lazy_disabled_state(
    page, books_url, sample_books
):
    """Opening More should fetch and apply lazy disabled-state details."""

    target_book = sample_books[0]
    target_book.description = ""
    target_book.save(update_fields=["description"])

    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    row = page.get_by_role("row").filter(has_text=target_book.title)
    trigger = row.locator("[data-powercrud-row-actions-trigger='true']").first
    original_trigger = trigger.evaluate(
        """
        (element, spinnerSelector) => {
            window.__powercrudRowActionSpinnerSeen = false;
            new MutationObserver(() => {
                if (element.querySelector(spinnerSelector)) {
                    window.__powercrudRowActionSpinnerSeen = true;
                }
            }).observe(element, { childList: true, subtree: true });
            return {
                html: element.innerHTML,
                inlineWidth: element.style.width,
            };
        }
        """,
        ".spinner-border" if using_bootstrap_pack() else ".loading-spinner",
    )

    with page.expect_request(
        lambda request: (
            request.method == "GET"
            and f"/sample/bigbook/{target_book.pk}/row-action-states/"
            in request.url
        )
    ):
        trigger.dispatch_event("click")

    floating_panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(floating_panel).to_be_visible()
    description_preview = floating_panel.get_by_role(
        "link",
        name="Description Preview",
    )
    expect(description_preview).to_have_attribute("aria-disabled", "true")
    expect(description_preview).to_have_attribute(
        "data-bs-title" if using_bootstrap_pack() else "data-tippy-content",
        "This book does not have a description yet.",
    )
    expect(description_preview).to_have_class(
        re.compile(r"\bdisabled\b" if using_bootstrap_pack() else r"\bbtn-disabled\b")
    )
    expect(description_preview).to_have_class(re.compile(r"\bopacity-50\b"))
    assert description_preview.evaluate("el => window.getComputedStyle(el).pointerEvents") == "auto"
    assert description_preview.evaluate("el => window.getComputedStyle(el).cursor") == "not-allowed"
    if not using_bootstrap_pack():
        description_preview.hover()
        expect(page.locator("[data-tippy-root]")).to_be_visible()
    assert page.evaluate("() => window.__powercrudRowActionSpinnerSeen") is True
    assert trigger.evaluate("el => el.innerHTML") == original_trigger["html"]
    assert trigger.evaluate("el => el.style.width") == original_trigger["inlineWidth"]
    expect(trigger).to_be_enabled()
    expect(trigger).not_to_have_attribute("aria-busy", "true")


def test_row_actions_menu_removes_lazy_hidden_action(
    page, books_url, sample_books
):
    """Opening More should remove lazy-hidden row actions before display."""

    target_book = sample_books[0]
    target_book.title = "Hidden Preview Playwright"
    target_book.save(update_fields=["title"])

    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    row = page.get_by_role("row").filter(has_text=target_book.title)
    trigger = row.locator("[data-powercrud-row-actions-trigger='true']").first

    with page.expect_request(
        lambda request: (
            request.method == "GET"
            and f"/sample/bigbook/{target_book.pk}/row-action-states/"
            in request.url
        )
    ):
        trigger.dispatch_event("click")

    floating_panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(floating_panel).to_be_visible()
    expect(floating_panel.get_by_role("link", name="Normal Edit")).to_be_visible()
    expect(
        floating_panel.get_by_role("link", name="Description Preview")
    ).to_have_count(0)


def test_row_actions_menu_removes_lazy_hidden_actions_when_state_fetch_fails(
    page, books_url, sample_books
):
    """Failed lazy state requests should remove unresolved lazy-hidden actions."""

    target_book = sample_books[0]

    page.route(
        "**/row-action-states/",
        lambda route: route.fulfill(status=500, body="error"),
    )
    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    row = page.get_by_role("row").filter(has_text=target_book.title)
    row.locator("[data-powercrud-row-actions-trigger='true']").first.dispatch_event(
        "click"
    )

    floating_panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
    expect(floating_panel).to_be_visible()
    expect(floating_panel.get_by_role("link", name="Normal Edit")).to_be_visible()
    expect(
        floating_panel.get_by_role("link", name="Description Preview")
    ).to_have_count(0)


def test_row_actions_flagged_modal_close_refreshes_current_list(
    page, books_url, sample_books
):
    """A flagged modal action from the cloned row menu should refresh the list on close."""

    del sample_books

    page.goto(f"{books_url}?page_size=5")
    page.wait_for_load_state("networkidle")

    list_refreshes = []

    def record_list_refresh(request):
        if (
            request.method == "GET"
            and "/sample/bigbook/" in request.url
            and request.headers.get("x-filter-sort-request") == "true"
        ):
            list_refreshes.append(request.url)

    page.on("request", record_list_refresh)

    for close_count in range(1, 3):
        page.locator("[data-powercrud-row-actions-trigger='true']").first.click()
        floating_panel = page.locator("[data-powercrud-row-actions-floating-panel='true']")
        expect(floating_panel).to_be_visible()
        floating_panel.get_by_role("link", name="Normal Edit").click()
        expect(floating_panel).to_have_count(0)

        modal = page.locator("#powercrudBaseModal")
        expect(modal).to_be_visible()
        expect(modal.locator("#powercrudModalContent form")).to_be_visible()

        with page.expect_request(
            lambda request: (
                request.method == "GET"
                and "/sample/bigbook/" in request.url
                and request.headers.get("x-filter-sort-request") == "true"
            )
        ):
            modal.get_by_label("Close" if using_bootstrap_pack() else "Close modal").click()

        expect(modal).not_to_be_visible()
        page.wait_for_load_state("networkidle")
        # Let HTMX's post-swap lifecycle finish before exercising the refreshed controls again.
        page.wait_for_timeout(100)
        expect(page.locator("[data-powercrud-row-actions-floating-panel='true']")).to_have_count(0)
        fresh_trigger = page.locator("[data-powercrud-row-actions-trigger='true']").first
        expect(fresh_trigger).to_be_visible()
        assert len(list_refreshes) == close_count, (
            "Expected each flagged modal close to dispatch exactly one list refresh after repeated initialization."
        )
