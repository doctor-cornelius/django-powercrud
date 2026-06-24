import os
from datetime import date

import pytest

pytest.importorskip("playwright.sync_api")
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from sample.models import Author, Book, Genre, Profile
from sample.views import SAMPLE_DEMO_USERS


os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def books_url(live_server):
    path = reverse("sample:bigbook-list")
    base = os.getenv("PLAYWRIGHT_BASE_URL")
    if base:
        return f"{base.rstrip('/')}{path}"
    return f"{live_server.url.rstrip('/')}{path}"


@pytest.fixture
def manual_static_books_url(live_server):
    path = reverse("sample:manual-static-bigbook-list")
    base = os.getenv("PLAYWRIGHT_BASE_URL")
    if base:
        return f"{base.rstrip('/')}{path}"
    return f"{live_server.url.rstrip('/')}{path}"


@pytest.fixture
def authors_url(live_server):
    path = reverse("sample:author-list")
    base = os.getenv("PLAYWRIGHT_BASE_URL")
    if base:
        return f"{base.rstrip('/')}{path}"
    return f"{live_server.url.rstrip('/')}{path}"


@pytest.fixture
def profiles_url(live_server):
    path = reverse("sample:profile-list")
    base = os.getenv("PLAYWRIGHT_BASE_URL")
    if base:
        return f"{base.rstrip('/')}{path}"
    return f"{live_server.url.rstrip('/')}{path}"


@pytest.fixture
def sample_manager_page(page, client, live_server):
    """Authenticate the Playwright page as the sample manager user."""
    demo_user = SAMPLE_DEMO_USERS["manager"]
    user_model = get_user_model()
    user, _created = user_model.objects.get_or_create(
        username=demo_user["username"],
        defaults={"email": demo_user["email"]},
    )
    changed = False
    for field_name in ("email", "is_staff"):
        value = demo_user[field_name]
        if getattr(user, field_name) != value:
            setattr(user, field_name, value)
            changed = True
    if changed:
        user.save(update_fields=["email", "is_staff"])

    client.force_login(user)
    session_cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
    base = os.getenv("PLAYWRIGHT_BASE_URL") or live_server.url
    page.context.add_cookies(
        [
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session_cookie,
                "url": base.rstrip("/"),
            }
        ]
    )
    return page


@pytest.fixture
def sample_author(db):
    return Author.objects.create(
        name="Playwright Author",
        bio="",
        birth_date=None,
    )


@pytest.fixture
def sample_genre(db, sample_author):
    genre = Genre.objects.create(
        name="Playwright Mystery",
        description="Created for Playwright tests",
    )
    sample_author.genres.add(genre)
    return genre


@pytest.fixture
def sample_books(db, sample_author):
    books = []
    for idx in range(2):
        books.append(
            Book.objects.create(
                title=f"Existing Playwright Book {idx}",
                author=sample_author,
                published_date=date(2024, 1, idx + 1),
                bestseller=False,
                isbn=f"97812345{idx:02d}00",
                pages=200 + idx,
                description="Seeded for Playwright testing",
            )
        )
    return books


@pytest.fixture
def sample_profile(db, sample_author, sample_genre):
    return Profile.objects.create(
        author=sample_author,
        nickname="Playwright Profile",
        status=Profile.Status.ACTIVE,
        priority_band=Profile.PriorityBand.MEDIUM,
        favorite_genre=sample_genre,
    )
