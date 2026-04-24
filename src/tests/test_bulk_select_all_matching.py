import json

import pytest
from django.test import override_settings
from django.urls import reverse

from sample.models import Author


def normalize_html_text(value: str) -> str:
    """Collapse HTML whitespace to make response text assertions stable."""
    return " ".join(value.split())


def set_bulk_selection(client, model_name: str, ids: list[int]) -> None:
    """Persist a bulk selection into the test client session."""
    session = client.session
    selections = session.get("powercrud_selections", {})
    selections[f"powercrud_bulk_{model_name}_"] = [str(object_id) for object_id in ids]
    session["powercrud_selections"] = selections
    session.save()


@pytest.mark.django_db
def test_author_list_shows_select_all_matching_cta_when_any_record_is_selected(client):
    """Render the queryset-wide select-all CTA once any selection exists and all matches fit within the cap."""
    authors = [Author.objects.create(name=f"Author {index:02d}") for index in range(16)]
    set_bulk_selection(client, "author", [authors[0].pk])

    response = client.get(reverse("sample:author-list"))
    response_text = normalize_html_text(response.content.decode())

    assert response.status_code == 200, (
        "Author list should render successfully when the select-all matching CTA is eligible."
    )
    assert "Select all 16 matching records" in response_text, (
        "List metadata should offer a queryset-wide select-all CTA whenever at least one record is selected and the remaining matches fit within the cap."
    )


@pytest.mark.django_db
@override_settings(POWERCRUD_SETTINGS={"BULK_MAX_SELECTED_RECORDS": 15})
def test_author_list_shows_add_more_cta_when_cap_limits_expansion(client):
    """Render a capped CTA that clearly describes adding more matching rows without implying adjacency to the visible selection."""
    authors = [Author.objects.create(name=f"Author {index:02d}") for index in range(16)]
    set_bulk_selection(client, "author", [authors[0].pk])

    response = client.get(reverse("sample:author-list"))
    response_text = normalize_html_text(response.content.decode())

    assert response.status_code == 200, (
        "Author list should render successfully when the capped add-more CTA is shown."
    )
    assert "Add 14 more from 16 matching records" in response_text, (
        "List metadata should describe capped queryset expansion as adding more matching rows rather than selecting the next visible records."
    )
    assert "Select all 16 matching records" not in response_text, (
        "List metadata should not promise a full select-all when the configured cap only allows a partial queryset expansion."
    )


@pytest.mark.django_db
def test_author_list_hides_bulk_selection_meta_when_disabled(client, monkeypatch):
    """Allow views to disable the bulk-selection metadata row independently of record-count display."""
    monkeypatch.setattr(
        "sample.views.AuthorCRUDView.show_bulk_selection_meta",
        False,
        raising=False,
    )

    authors = [Author.objects.create(name=f"Author {index:02d}") for index in range(16)]
    set_bulk_selection(client, "author", [authors[0].pk])

    response = client.get(reverse("sample:author-list"))
    response_text = normalize_html_text(response.content.decode())

    assert response.status_code == 200, (
        "Author list should still render successfully when bulk-selection metadata is disabled."
    )
    assert "Select all 16 matching records" not in response_text, (
        "List metadata should not render the bulk-selection CTA when show_bulk_selection_meta is disabled."
    )


@pytest.mark.django_db
def test_select_all_matching_endpoint_expands_session_selection_and_triggers_refresh(client):
    """Expand the session-backed selection and ask the page to refresh the list metadata."""
    authors = [Author.objects.create(name=f"Author {index:02d}") for index in range(16)]
    set_bulk_selection(client, "author", [authors[0].pk])

    response = client.post(
        reverse("sample:author-select-all-matching"),
        HTTP_HX_REQUEST="true",
    )
    session = client.session
    selected_ids = session["powercrud_selections"]["powercrud_bulk_author_"]

    assert response.status_code == 200, (
        "Select-all matching endpoint should respond successfully to an HTMX request."
    )
    assert len(selected_ids) == 16, (
        "Select-all matching endpoint should add every remaining filtered record ID when the whole queryset still fits within the configured cap."
    )
    assert json.loads(response["HX-Trigger"]) == {"refreshTable": True}, (
        "Select-all matching endpoint should trigger a list refresh so the metadata line and checkboxes redraw."
    )
    assert "Bulk Edit <span id=\"selected-items-counter\">16</span>" in response.content.decode(), (
        "Select-all matching endpoint should return the updated bulk-actions toolbar count."
    )
    assert 'hx-target="#powercrudModalContent"' in response.content.decode(), (
        "Bulk-action toolbar partials should keep the default modal target when rendered outside the full list context."
    )
    assert "document.getElementById('powercrudBaseModal').showModal();" in response.content.decode(), (
        "Bulk-action toolbar partials should keep the default modal opener when rendered outside the full list context."
    )


@pytest.mark.django_db
@override_settings(POWERCRUD_SETTINGS={"BULK_MAX_SELECTED_RECORDS": 15})
def test_select_all_matching_endpoint_respects_configured_selection_cap(client):
    """Add only the next matching records up to the configured PowerCRUD selection cap."""
    authors = [Author.objects.create(name=f"Author {index:02d}") for index in range(16)]
    set_bulk_selection(client, "author", [authors[0].pk])

    response = client.post(
        reverse("sample:author-select-all-matching"),
        HTTP_HX_REQUEST="true",
    )
    session = client.session
    selected_ids = session["powercrud_selections"]["powercrud_bulk_author_"]

    assert response.status_code == 200, (
        "Select-all matching endpoint should still respond successfully when only a capped subset of matching records can be added."
    )
    assert len(selected_ids) == 15, (
        "Select-all matching endpoint should fill the selection up to the configured cap rather than refusing to add any matching records."
    )
    assert json.loads(response["HX-Trigger"]) == {"refreshTable": True}, (
        "Select-all matching endpoint should still trigger a list refresh when it performs a capped queryset expansion."
    )


@pytest.mark.django_db
def test_select_all_matching_endpoint_preserves_existing_selection_outside_current_filter(client):
    """Union the filtered result set with any records that were already selected outside the current filter."""
    target_authors = [
        Author.objects.create(name="Alice Example"),
        Author.objects.create(name="Alicia Example"),
    ]
    outside_author = Author.objects.create(name="Bob Example")
    set_bulk_selection(client, "author", [outside_author.pk])

    response = client.post(
        f"{reverse('sample:author-select-all-matching')}?name=Ali",
        HTTP_HX_REQUEST="true",
    )
    session = client.session
    selected_ids = session["powercrud_selections"]["powercrud_bulk_author_"]

    assert response.status_code == 200, (
        "Select-all matching endpoint should accept current filter params from the query string."
    )
    assert sorted(selected_ids) == sorted(
        [str(outside_author.pk), str(target_authors[0].pk), str(target_authors[1].pk)]
    ), (
        "Select-all matching should preserve records selected outside the current filter while adding the matching filtered records."
    )
