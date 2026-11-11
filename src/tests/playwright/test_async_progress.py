import json
from urllib.parse import parse_qs, urlparse

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect

from django.urls import reverse

from sample.models import AsyncTaskRecord


pytestmark = [
    pytest.mark.playwright,
    pytest.mark.django_db,
    pytest.mark.usefixtures("sample_manager_page"),
]


def _observation(status="unknown", *, terminal=False, reason="cache unavailable", **extra):
    return {
        "status": status,
        "terminal": terminal,
        "reason": reason,
        "progress": "Checking task status…",
        "task_name": "browser-task",
        "outcome": None,
        "polling_stopped": False,
        **extra,
    }


def test_unknown_status_stops_after_budget_and_manual_refresh_recovers(
    page, live_server, sample_async_task_record
):
    page.clock.install()
    task_url = reverse(
        "sample:async-dashboard-detail", kwargs={"pk": sample_async_task_record.pk}
    )
    endpoint = reverse("powercrud:async_progress")
    seen_elapsed = []
    exhausted = False

    def progress(route):
        nonlocal exhausted
        request = route.request
        params = parse_qs(urlparse(request.url).query)
        elapsed = int(params.get("unknown_elapsed_ms", ["0"])[0])
        seen_elapsed.append(elapsed)
        if exhausted:
            route.fulfill(
                status=286,
                content_type="application/json",
                body=json.dumps(
                    _observation(
                        "success", terminal=True, reason=None, outcome={"message": "Done"}
                    )
                ),
            )
        elif elapsed < 30000:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(_observation()),
            )
        else:
            exhausted = True
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(_observation(polling_stopped=True)),
            )

    page.route(f"**{endpoint}**", progress)
    page.goto(f"{live_server.url}{task_url}")
    status = page.locator("[data-powercrud-async-progress]")
    expect(status).to_contain_text("Checking task status")

    page.clock.fast_forward(31000)
    expect(status).to_contain_text("Status currently unavailable")
    expect(status.get_by_role("button", name="Refresh status")).to_be_visible()
    assert max(seen_elapsed) >= 30000

    status.get_by_role("button", name="Refresh status").click()
    expect(page.locator("[data-powercrud-async-progress]")).to_contain_text("Done")


def test_partial_bulk_result_refreshes_without_success_event(
    page, live_server, sample_async_task_record
):
    page.clock.install()
    task_url = reverse(
        "sample:async-dashboard-detail", kwargs={"pk": sample_async_task_record.pk}
    )
    endpoint = reverse("powercrud:async_progress")

    def progress(route):
        page.evaluate(
            """() => {
                if (document.querySelector('[data-powercrud-bulk-outcome="queued"]')) return;
                const root = document.querySelector('[data-powercrud-async-progress]');
                const bulk = document.createElement('div');
                bulk.dataset.powercrudBulkOutcome = 'queued';
                bulk.innerHTML = '<h2 id="async-status-heading">Queued</h2>';
                root.before(bulk);
                window.__bulkSuccesses = 0;
                window.__tableRefreshes = 0;
                document.body.addEventListener('bulkEditSuccess', () => window.__bulkSuccesses++);
                document.body.addEventListener('refreshTable', () => window.__tableRefreshes++);
            }"""
        )
        route.fulfill(
            status=286,
            content_type="application/json",
            body=json.dumps(
                _observation(
                    "failed",
                    terminal=True,
                    reason=None,
                    task_name="partial-task",
                    outcome={
                        "business_status": "partial",
                        "processed_count": 1,
                        "total_count": 2,
                        "message": "One item changed",
                    },
                )
            ),
        )

    page.route(f"**{endpoint}**", progress)
    page.goto(f"{live_server.url}{task_url}")
    expect(page.locator("[data-powercrud-async-progress]")).to_contain_text(
        "One item changed"
    )
    assert page.evaluate("window.__bulkSuccesses") == 0
    assert page.evaluate("window.__tableRefreshes") == 1
