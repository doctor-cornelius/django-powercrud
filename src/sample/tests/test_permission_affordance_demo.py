from datetime import date

import pytest
from django.urls import reverse

from sample.models import Author, Book
from sample.views import SAMPLE_DEMO_USERS


def _create_preview_book():
    author = Author.objects.create(name="Permission Demo Author")
    return Book.objects.create(
        title="Permission Demo Book",
        author=author,
        published_date=date(2024, 6, 1),
        bestseller=False,
        isbn="9780000001775",
        pages=177,
        description="This description makes the preview row-state eligible.",
    )


def _login_as(client, role):
    return client.post(reverse("sample:demo-login", args=[role]))


@pytest.mark.django_db
def test_sample_login_bar_starts_anonymous_and_logs_in_viewer(client):
    _create_preview_book()

    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200
    response_text = response.content.decode()
    assert "Login" in response_text
    assert SAMPLE_DEMO_USERS["viewer"]["username"] not in response_text

    login_response = _login_as(client, "viewer")
    assert login_response.status_code == 302

    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()
    assert SAMPLE_DEMO_USERS["viewer"]["username"] in response_text


@pytest.mark.django_db
def test_sample_viewer_cannot_see_or_call_description_preview(client):
    book = _create_preview_book()

    _login_as(client, "viewer")
    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200
    assert "Description Preview" not in response.content.decode()

    response = client.get(
        reverse("sample:bigbook-description-preview", args=[book.pk])
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_sample_manager_can_see_and_call_description_preview(client):
    book = _create_preview_book()

    _login_as(client, "manager")
    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200
    assert SAMPLE_DEMO_USERS["manager"]["username"] in response.content.decode()
    assert "Description Preview" in response.content.decode()

    response = client.get(
        reverse("sample:bigbook-description-preview", args=[book.pk])
    )

    assert response.status_code == 200
    assert book.title in response.content.decode()


@pytest.mark.django_db
def test_sample_poweraction_demo_uses_same_permission_affordance(client):
    _create_preview_book()

    _login_as(client, "viewer")
    response = client.get(reverse("sample:powerfield-book-list"))
    assert response.status_code == 200
    assert "Description Preview" not in response.content.decode()

    _login_as(client, "manager")
    response = client.get(reverse("sample:powerfield-book-list"))
    assert response.status_code == 200
    assert "Description Preview" in response.content.decode()


@pytest.mark.django_db
def test_sample_viewer_cannot_see_or_call_selected_summary(client):
    book = _create_preview_book()
    session = client.session
    session["powercrud_selections"] = {"powercrud_bulk_book_": [str(book.pk)]}
    session.save()

    _login_as(client, "viewer")
    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200
    assert "Selected Summary" not in response.content.decode()

    response = client.get(reverse("sample:bigbook-selected-summary"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_sample_manager_sees_selected_summary_disabled_without_selection(client):
    _create_preview_book()

    _login_as(client, "manager")
    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()

    assert response.status_code == 200
    assert "Selected Summary" in response_text
    assert "Select at least one book first." in response_text
    assert "btn-disabled opacity-50" in response_text


@pytest.mark.django_db
def test_sample_manager_can_see_and_call_selected_summary(client):
    book = _create_preview_book()
    session = client.session
    session["powercrud_selections"] = {"powercrud_bulk_book_": [str(book.pk)]}
    session.save()

    _login_as(client, "manager")
    response = client.get(reverse("sample:bigbook-list"))
    response_text = response.content.decode()

    assert response.status_code == 200
    assert "Selected Summary" in response_text
    selected_summary_index = response_text.find("Selected Summary")
    selected_summary_anchor_start = response_text.rfind("<a ", 0, selected_summary_index)
    selected_summary_anchor_end = response_text.find(">", selected_summary_anchor_start)
    selected_summary_link = response_text[
        selected_summary_anchor_start:selected_summary_anchor_end
    ]
    assert "btn-disabled opacity-50" not in selected_summary_link

    response = client.get(reverse("sample:bigbook-selected-summary"))

    assert response.status_code == 200
    assert book.title in response.content.decode()


@pytest.mark.django_db
def test_sample_powerbutton_demo_uses_same_permission_affordance(client):
    _create_preview_book()

    _login_as(client, "viewer")
    response = client.get(reverse("sample:powerfield-book-list"))
    assert response.status_code == 200
    assert "Selected Summary" not in response.content.decode()

    _login_as(client, "manager")
    response = client.get(reverse("sample:powerfield-book-list"))
    assert response.status_code == 200
    assert "Selected Summary" in response.content.decode()
