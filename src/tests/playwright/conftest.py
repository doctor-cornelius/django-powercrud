import os
from datetime import date

import pytest
pytest.importorskip("playwright.sync_api")
from django.urls import reverse

from sample.models import Author, Book, Genre


os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def books_url(live_server):
    path = reverse("sample:bigbook-list")
    base = os.getenv("PLAYWRIGHT_BASE_URL")
    if base:
        return f"{base.rstrip('/')}{path}"
    return f"{live_server.url.rstrip('/')}{path}"


@pytest.fixture
def sample_author(db):
    return Author.objects.create(
        name="Playwright Author",
        bio="",
        birth_date=None,
    )


@pytest.fixture
def sample_genre(db):
    return Genre.objects.create(
        name="Playwright Mystery",
        description="Created for Playwright tests",
    )


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
