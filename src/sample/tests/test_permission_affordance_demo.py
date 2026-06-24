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
