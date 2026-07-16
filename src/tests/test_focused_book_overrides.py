"""Integration tests for the sample's focused Book template overrides."""

from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

from sample.models import Author, Book
from sample.views import BookCRUDView


FOCUSED_COMPONENTS = {
    "list_actions": "book_list_actions.html",
    "filter_trigger": "book_filter_trigger.html",
    "table_header": "book_table_header.html",
    "pagination": "book_pagination.html",
}
FOCUSED_TEMPLATE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "sample"
    / "template_overrides"
    / "focused"
)


def test_focused_book_override_source_contains_only_the_agreed_components():
    """The focused sample should expose exactly four script-free Book components."""
    override_directory = FOCUSED_TEMPLATE_ROOT / "sample"
    override_files = {path.name for path in override_directory.glob("*.html")}

    assert override_files == set(FOCUSED_COMPONENTS.values()), (
        "Focused sample overrides should contain only the four agreed Book components."
    )
    for component, filename in FOCUSED_COMPONENTS.items():
        template = (override_directory / filename).read_text(encoding="utf-8")
        assert f'data-sample-focused-component="{component.replace("_", "-")}"' in template, (
            f"The {component} override should expose its focused sample marker."
        )
        assert "<script" not in template.lower(), (
            f"The {component} override must not copy functional JavaScript."
        )


def test_book_focused_component_candidates_remain_model_first():
    """Book components should resolve through model-first candidates before pack fallbacks."""
    view = BookCRUDView()

    for component in FOCUSED_COMPONENTS:
        candidates = view.get_focused_component_template_paths(component)
        assert candidates == [
            f"sample/book_{component}.html",
            f"powercrud/packs/daisyui/partial/{component}.html",
        ], f"Book {component} should prefer its focused sample template before DaisyUI."


@pytest.mark.django_db
def test_book_list_renders_focused_overrides_only_when_the_overlay_is_active(client):
    """The focused overlay should affect Book list presentation without changing defaults."""
    author = Author.objects.create(name="Focused Override Author")
    for number in range(7):
        Book.objects.create(
            title=f"Focused Override Book {number}",
            author=author,
            published_date="2024-01-01",
            bestseller=False,
            isbn=f"9780000001{number:03d}",
            pages=100 + number,
        )

    response = client.get(f"{reverse('sample:bigbook-list')}?page_size=5")

    assert response.status_code == 200, "The Book list should render under every sample setting."
    response_text = response.content.decode()
    focused_active = getattr(
        settings,
        "SAMPLE_PRESENTATION",
        "Standard DaisyUI",
    ) == "Standard DaisyUI + Book overrides"

    for component in FOCUSED_COMPONENTS:
        marker = f'data-sample-focused-component="{component.replace("_", "-")}"'
        if focused_active:
            assert marker in response_text, (
                f"The focused Book list should render the {component} override marker."
            )
        else:
            assert marker not in response_text, (
                f"The default Book list should not render the focused {component} marker."
            )

    assert 'id="filterToggleBtn"' in response_text, (
        "Book list filtering should retain its stable filter-toggle identifier."
    )
    assert "<thead" in response_text, "Book list rendering should retain a table header."
    assert 'data-powercrud-pagination="true"' in response_text, (
        "Book list rendering should retain the pagination runtime hook."
    )
