from __future__ import annotations

import re
from datetime import date, datetime

import pytest
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django_filters import BooleanFilter

from powercrud.mixins.config_mixin import resolve_class_config
from powercrud.mixins.list_options_mixin import LIST_OPTIONS_SESSION_KEY
from powercrud.mixins.filtering_mixin import NULL_FILTER_SENTINEL
from powercrud.templatetags import powercrud as powercrud_tags
from sample import views as sample_views
from sample.models import AsyncTaskRecord, Author, Book, Genre, Profile


def _login_sample_manager(client):
    """Authenticate the client as the sample manager user."""
    return client.post(reverse("sample:demo-login", args=["manager"]))


@pytest.mark.django_db
def test_author_sample_view_exposes_nullable_scalar_companion_filter():
    """Author sample view should expose the nullable birth-date companion filter."""
    Author.objects.create(name="Alan", birth_date=None)

    view = sample_views.AuthorCRUDView()
    view.request = RequestFactory().get("/")
    filterset = view.get_filterset(Author.objects.all())

    assert (
        filterset is not None
    ), "Expected AuthorCRUDView to generate a filterset for the sample app."
    assert (
        "birth_date__isnull" in filterset.filters
    ), "AuthorCRUDView should expose the nullable birth_date companion filter in the sample app."


@pytest.mark.django_db
def test_author_sample_view_keeps_nullable_scalar_companion_optional_by_default():
    """Author sample view should allow the birth-date null companion without showing it by default."""
    Author.objects.create(name="Alan", birth_date=None)

    view = sample_views.AuthorCRUDView()
    view.request = RequestFactory().get("/")
    filterset = view.get_filterset(Author.objects.all())
    context = view.get_filter_visibility_context(filterset)

    assert [field.name for field in context["visible_filter_fields"]] == [
        "name",
        "birth_date",
        "genres",
    ], "AuthorCRUDView should keep its main filters visible by default without auto-showing the nullable companion control."
    assert [choice["name"] for choice in context["addable_filter_choices"]] == [
        "birth_date__isnull",
    ], "AuthorCRUDView should still allow the nullable birth-date companion control to be added on demand."


@pytest.mark.django_db
def test_profile_sample_view_exposes_nullable_relation_empty_only_option():
    """Profile sample view should expose the merged null-only relation option."""
    author_one = Author.objects.create(name="Alan")
    author_two = Author.objects.create(name="Betty")
    genre = Genre.objects.create(name="Sci-Fi")
    Profile.objects.create(
        author=author_one,
        nickname="Has Genre",
        favorite_genre=genre,
    )
    Profile.objects.create(
        author=author_two,
        nickname="Missing Genre",
        favorite_genre=None,
    )

    view = sample_views.ProfileCRUDView()
    view.request = RequestFactory().get("/")
    filterset = view.get_filterset(Profile.objects.all())

    assert (
        filterset is not None
    ), "Expected ProfileCRUDView to generate a filterset for the sample app."
    relation_choices = list(filterset.form.fields["favorite_genre"].choices)
    assert (
        (NULL_FILTER_SENTINEL, "Empty only") in relation_choices
    ), "ProfileCRUDView should expose the merged 'Empty only' option for nullable favorite_genre filtering."


@pytest.mark.django_db
def test_profile_sample_view_applies_static_queryset_filters_to_forms_and_bulk():
    """Profile sample view should demonstrate static queryset rules across surfaces."""
    author = Author.objects.create(name="Static Profile Author")
    sci_fi = Genre.objects.create(name="Sci-Fi")
    fantasy = Genre.objects.create(name="Fantasy")
    profile = Profile.objects.create(
        author=author,
        nickname="Static Demo",
        favorite_genre=sci_fi,
    )

    view = sample_views.ProfileCRUDView()
    view.request = RequestFactory().get("/")

    form = view._finalize_form(view.get_form_class()(instance=profile))
    inline_form = view.build_inline_form(instance=profile)
    bulk_qs = view.get_bulk_choices_for_field(
        "favorite_genre",
        Profile._meta.get_field("favorite_genre"),
    )

    form_genre_names = list(
        form.fields["favorite_genre"].queryset.values_list("name", flat=True)
    )
    inline_genre_names = list(
        inline_form.fields["favorite_genre"].queryset.values_list("name", flat=True)
    )
    bulk_genre_names = list(bulk_qs.values_list("name", flat=True))

    assert form_genre_names == [
        "Sci-Fi"
    ], "ProfileCRUDView should restrict regular form genre choices using a static field_queryset_dependencies rule."
    assert inline_genre_names == [
        "Sci-Fi"
    ], "ProfileCRUDView should reuse the same static field queryset restriction during inline editing."
    assert bulk_genre_names == [
        "Sci-Fi"
    ], "ProfileCRUDView should reuse the same static field queryset restriction for bulk edit choices."
    assert (
        fantasy.name not in bulk_genre_names
    ), "ProfileCRUDView bulk choices should exclude genres that fail the sample static queryset rule."


@pytest.mark.django_db
def test_profile_sample_view_exposes_centered_alignment_overrides():
    """Profile sample view should expose the current mixed alignment demo."""
    view = sample_views.ProfileCRUDView()

    assert view.get_column_alignments() == {
        "status": "center",
        "priority_band": "right",
        "favorite_genre": "left",
    }, "ProfileCRUDView should expose the current sample alignment overrides for its categorical and text demo columns."


@pytest.mark.django_db
def test_async_task_sample_view_demonstrates_temporal_list_formats():
    """The async task sample should expose the documented temporal column example."""
    view = sample_views.AsyncTaskRecordCRUDView()

    assert view.default_datetime_value_format == "date", (
        "The async task sample should make unoverridden datetime columns date-only."
    )
    assert view.column_value_formats == {
        "updated_at": "time",
        "completed_at": "datetime",
    }, "The sample should override one datetime column to time-only and one to date-and-time."
    assert view.fields == [
        "id",
        "task_name",
        "user_label",
        "status",
        "cleaned_up",
        "created_at",
        "updated_at",
        "completed_at",
        "failed_at",
    ], "The sample list should include all datetime columns needed to inspect defaults and overrides."


@pytest.mark.django_db
def test_async_task_sample_view_exposes_native_datetime_filter_by_default(client):
    """The async sample should visibly demonstrate the selected pack's datetime control."""
    view = sample_views.AsyncTaskRecordCRUDView()
    view.request = RequestFactory().get("/")
    filterset = view.get_filterset(AsyncTaskRecord.objects.all())
    visibility = view.get_filter_visibility_context(filterset)

    assert filterset is not None, (
        "AsyncTaskRecordCRUDView should generate its configured task filters."
    )
    assert [field.name for field in visibility["visible_filter_fields"]] == [
        "task_name",
        "status",
        "completed_from",
        "completed_to",
    ], "The async sample should show its useful task and completion-range filters by default."

    for field_name in ("completed_from", "completed_to"):
        widget = filterset.form.fields[field_name].widget
        rendered = widget.render(field_name, "2026-08-09T14:05")
        assert widget.input_type == "datetime-local", (
            f"The selected pack should present {field_name} as a native datetime-local control."
        )
        assert widget.attrs.get("step") == "60", (
            f"The async sample's {field_name} control should use minute precision."
        )
        assert re.findall(r'\btype="([^"]+)"', rendered) == ["datetime-local"], (
            f"The visible {field_name} filter should render exactly one datetime-local type."
        )
        assert 'value="2026-08-09T14:05"' in rendered, (
            f"The visible {field_name} filter should retain its minute-precision value."
        )

    response = client.get(reverse("sample:asynctaskrecord-list"))
    response_text = response.content.decode()
    assert response.status_code == 200, (
        "The Async Tasks list should render with its generated filter controls."
    )
    for field_name in ("completed_from", "completed_to"):
        assert f'name="{field_name}"' in response_text, (
            f"The rendered Async Tasks filter panel should include {field_name} by default."
        )
    assert re.findall(r'\btype="([^"]+)"', response_text).count(
        "datetime-local"
    ) == 2, (
        "The rendered Async Tasks page should contain two visible native datetime filters."
    )
    assert response_text.count('step="60"') == 2, (
        "Both rendered completion-range controls should use minute precision."
    )


@pytest.mark.django_db
def test_async_task_sample_completion_range_is_inclusive():
    """Completion ranges should include both boundaries and sub-second values within them."""
    timestamps = {
        "before": datetime(2026, 8, 9, 14, 4, 59, 999999),
        "at-lower": datetime(2026, 8, 9, 14, 5),
        "inside": datetime(2026, 8, 9, 14, 5, 37, 482913),
        "at-upper": datetime(2026, 8, 9, 14, 6),
        "after": datetime(2026, 8, 9, 14, 6, 0, 1),
    }
    for task_name, timestamp in timestamps.items():
        record = AsyncTaskRecord.objects.create(
            task_name=task_name,
            status=AsyncTaskRecord.STATUS.SUCCESS,
        )
        AsyncTaskRecord.objects.filter(pk=record.pk).update(
            completed_at=timezone.make_aware(timestamp)
        )

    view = sample_views.AsyncTaskRecordCRUDView()
    view.request = RequestFactory().get(
        "/",
        {
            "completed_from": "2026-08-09T14:05",
            "completed_to": "2026-08-09T14:06",
        },
    )
    filterset = view.get_filterset(AsyncTaskRecord.objects.all())

    assert filterset.is_valid(), (
        "The async sample completion range should accept datetime-local values."
    )
    assert set(filterset.qs.values_list("task_name", flat=True)) == {
        "at-lower",
        "inside",
        "at-upper",
    }, "The completion range should include both selected boundaries and values between them."


@pytest.mark.django_db
def test_book_sample_view_scopes_genres_queryset_for_regular_forms():
    """Book sample view should scope genres from the selected author in regular forms."""
    author_a = Author.objects.create(name="Author A")
    author_b = Author.objects.create(name="Author B")
    genre_a = Genre.objects.create(name="Genre A")
    genre_b = Genre.objects.create(name="Genre B")
    author_a.genres.add(genre_a)
    author_b.genres.add(genre_b)
    book = Book.objects.create(
        title="Scoped Sample Book",
        author=author_a,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9781234500001",
        pages=88,
    )

    view = sample_views.BookCRUDView()
    view.request = RequestFactory().post("/")
    form = view._finalize_form(
        view.get_form_class()(
            instance=book,
            data={
                "title": book.title,
                "author": str(author_b.pk),
                "published_date": "2024-01-01",
                "isbn": book.isbn,
                "pages": str(book.pages),
                "bestseller": "",
            },
        )
    )

    genre_ids = list(form.fields["genres"].queryset.values_list("id", flat=True))
    assert genre_ids == [
        genre_b.pk
    ], "BookCRUDView should scope genre choices to the selected author in the sample form."
    assert (
        form.fields["genres"].required is False
    ), "The sample BookForm should still keep genres optional while PowerCRUD scopes the queryset."


@pytest.mark.django_db
def test_book_sample_view_derives_inline_dependencies_from_queryset_config():
    """Book sample view should expose inline dependency metadata without duplicating config."""
    view = sample_views.BookCRUDView()
    view.request = RequestFactory().get("/")

    deps = view.get_inline_field_dependencies()

    assert (
        deps["genres"]["depends_on"] == ["author"]
    ), "BookCRUDView should derive inline dependency metadata from field_queryset_dependencies."


def test_sample_views_demonstrate_row_actions_column_layout_options():
    """The sample catalogue should demonstrate stickiness and relocation separately."""
    book_view = sample_views.BookCRUDView()
    annotated_view = sample_views.AnnotatedBookCRUDView()
    author_view = sample_views.AuthorCRUDView()

    assert book_view.get_row_actions_column_position() == "end" and book_view.get_row_actions_column_sticky() is True, (
        "BookCRUDView should demonstrate sticky actions at the logical end of its wide table."
    )
    assert annotated_view.get_row_actions_column_position() == "start" and annotated_view.get_row_actions_column_sticky() is False, (
        "AnnotatedBookCRUDView should demonstrate relocation to logical start independently of stickiness."
    )
    assert annotated_view.get_extra_actions_mode() == "buttons", (
        "AnnotatedBookCRUDView should demonstrate directly visible configured row-action buttons."
    )
    assert author_view.get_row_actions_column_position() == "start" and author_view.get_row_actions_column_sticky() is True, (
        "AuthorCRUDView should demonstrate the combined logical-start and sticky layout."
    )
    assert author_view.get_extra_actions_mode() == "all_dropdown", (
        "AuthorCRUDView should demonstrate the compact menu containing native and configured row actions."
    )
    assert author_view.get_extra_buttons_mode() == "dropdown", (
        "AuthorCRUDView should demonstrate the list-level extra-button dropdown mode."
    )
    assert author_view.get_extra_buttons_dropdown_label() == "More", (
        "AuthorCRUDView should demonstrate a per-view override of the default Actions label."
    )
    assert author_view.extra_buttons[0]["text"] == "Genres", (
        "AuthorCRUDView should expose the existing Genre list as its toolbar demo action."
    )


def test_sample_views_demonstrate_extra_action_custom_icon_presentations():
    """Keep the sample catalogue aligned with the documented custom-icon API."""
    annotated_view = sample_views.AnnotatedBookCRUDView()
    powerfield_view = sample_views.PowerFieldBookCRUDView()
    async_view = sample_views.AsyncTaskRecordCRUDView()

    annotated_action = annotated_view.extra_actions[0]
    assert (
        annotated_action["icon_svg"] == sample_views.OPEN_BOOK_ICON_SVG
        and annotated_action["icon_only"] is True
    ), (
        "Annotated Books should demonstrate an icon-only direct dictionary action."
    )

    normal_edit, description_preview = powerfield_view.extra_actions
    assert normal_edit["icon_svg"] == sample_views.NORMAL_EDIT_ICON_SVG, (
        "PowerField Books should demonstrate a PowerAction custom SVG in its all-actions menu."
    )
    assert description_preview.get("icon_svg") is None, (
        "The derived PowerAction should deliberately remain iconless for mixed-menu alignment."
    )

    async_action = async_view.extra_actions[0]
    assert async_action["icon_svg"] == sample_views.VIEW_PROGRESS_ICON_SVG, (
        "Async records should demonstrate an extras-only dropdown action with a custom SVG."
    )


@pytest.mark.django_db
def test_author_sample_all_actions_menu_survives_inline_htmx_rows():
    """Author list and replacement rows should share the all-actions contract."""
    author = Author.objects.create(name="Author Unified Menu")
    client = Client()
    _login_sample_manager(client)

    list_response = client.get(reverse("sample:author-list"))
    display_response = client.get(
        reverse("sample:author-inline-row", args=[author.pk]),
        {"inline_display": "true"},
        HTTP_HX_REQUEST="true",
    )
    form_response = client.get(
        reverse("sample:author-inline-row", args=[author.pk]),
        HTTP_HX_REQUEST="true",
    )

    assert list_response.status_code == 200, (
        "The Author sample list should render its unified row-actions demonstration."
    )
    list_html = list_response.content.decode()
    row_start = list_html.index('data-inline-row="true"')
    row_html = list_html[row_start:list_html.index("</tr>", row_start)]
    assert row_html.index('data-powercrud-row-select="true"') < row_html.index(
        'data-powercrud-row-actions-column="true"'
    ) < row_html.index('data-field-name="id"'), (
        "The Author list should keep selection, start-positioned actions, then data columns."
    )
    assert "data-powercrud-row-actions-scope='all'" in list_html and "aria-label='Actions'" in list_html, (
        "The Author list should expose the unified Actions trigger through stable semantic markup."
    )
    header_start = list_html.index("<thead")
    header_html = list_html[header_start:list_html.index("</thead>", header_start)]
    assert '<span class="sr-only pc-row-actions-heading-label">Actions</span>' in header_html, (
        "The all-dropdown Author header should retain an accessible name without a visible Actions label."
    )
    assert display_response.status_code == 200 and b"data-powercrud-row-actions-scope='all'" in display_response.content, (
        "An HTMX display-row replacement should retain the Author all-actions menu."
    )
    assert form_response.status_code == 200 and b"data-inline-save" in form_response.content and b"data-inline-cancel" in form_response.content, (
        "An active Author inline row should replace its menu with working Save and Cancel controls."
    )


@pytest.mark.django_db
def test_book_sample_view_exposes_default_and_optional_filter_visibility():
    """Book sample view should demonstrate default-visible and optional filters."""
    Author.objects.create(name="Filter Demo Author")

    view = sample_views.BookCRUDView()
    view.request = RequestFactory().get("/", {"visible_filters": ["isbn"]})
    filterset = view.get_filterset(Book.objects.all())
    context = view.get_filter_visibility_context(filterset)

    assert [field.name for field in context["visible_filter_fields"]] == [
        "author",
        "title",
        "published_date",
        "isbn",
        "bestseller",
    ], "BookCRUDView should keep its configured default filters visible and allow optional filters to be revealed from the URL-backed visibility state."
    assert context["persisted_optional_filter_names"] == [
        "isbn"
    ], "BookCRUDView should persist revealed optional filters separately from its default-visible filter set."
    assert [choice["name"] for choice in context["addable_filter_choices"]] == [
        "pages",
        "description",
        "genres",
    ], "BookCRUDView should leave only the remaining hidden filters available in the Add filter menu."


@pytest.mark.django_db
def test_annotated_book_sample_view_exposes_query_annotation_filter():
    """AnnotatedBookCRUDView should demonstrate first-class queryset annotation fields."""
    author = Author.objects.create(name="Annotation Demo Author")
    short_book = Book.objects.create(
        title="Short Annotation Demo",
        author=author,
        published_date=date(2024, 4, 1),
        bestseller=False,
        isbn="9781234500201",
        pages=120,
    )
    long_book = Book.objects.create(
        title="Long Annotation Demo",
        author=author,
        published_date=date(2024, 4, 2),
        bestseller=False,
        isbn="9781234500202",
        pages=640,
    )

    request = RequestFactory().get("/", {"long_book": "true"})
    view = sample_views.AnnotatedBookCRUDView()
    view.request = request
    queryset = view.get_queryset()
    filterset = view.get_filterset(queryset)

    assert view.fields == [
        "title",
        "author",
        "pages",
        "long_book",
        "published_date",
    ], "AnnotatedBookCRUDView should keep the annotation in the explicit list-field order."
    assert isinstance(filterset.filters["long_book"], BooleanFilter), (
        "AnnotatedBookCRUDView should generate a BooleanFilter for the annotation output_field."
    )
    assert filterset.form.fields["long_book"].label == "Long book", (
        "AnnotatedBookCRUDView should label the annotation filter from its public name, not django-filter's invalid-name fallback."
    )
    assert list(filterset.qs) == [long_book], (
        "AnnotatedBookCRUDView should filter by the queryset-backed long_book column."
    )
    assert short_book not in list(filterset.qs), (
        "AnnotatedBookCRUDView should exclude rows whose annotation does not match the filter."
    )


@pytest.mark.django_db
def test_annotated_book_sample_list_renders(client: Client):
    """The annotation sample list route should render the queryset-backed column."""
    author = Author.objects.create(name="Annotation Render Author")
    Book.objects.create(
        title="Rendered Annotation Demo",
        author=author,
        published_date=date(2024, 4, 3),
        bestseller=False,
        isbn="9781234500203",
        pages=650,
    )

    response = client.get(reverse("sample:annotated-book-list"))

    assert response.status_code == 200, (
        "AnnotatedBookCRUDView list should render successfully in the sample app."
    )
    response_text = response.content.decode()
    assert "Long Book" in response_text, (
        "AnnotatedBookCRUDView should render the humanized annotation column header."
    )
    assert "Rendered Annotation Demo" in response_text, (
        "AnnotatedBookCRUDView should render rows from the annotated queryset."
    )
    assert "[invalid name]" not in response_text, (
        "AnnotatedBookCRUDView should not render django-filter's invalid-name fallback label for annotation filters."
    )
    assert 'data-inline-field="pages"' in response_text, (
        "AnnotatedBookCRUDView should make the real pages model field inline-editable."
    )
    assert 'data-inline-field="long_book"' not in response_text, (
        "AnnotatedBookCRUDView should keep the queryset annotation read-only."
    )
    assert "Annotated Selection Summary" in response_text, (
        "AnnotatedBookCRUDView should render a selection-aware extra button without bulk edit enabled."
    )
    assert 'data-powercrud-row-select="true"' in response_text, (
        "AnnotatedBookCRUDView should render row selection controls for its selection-aware extra button."
    )
    assert "annotated-book/bulk-edit/" not in response_text, (
        "AnnotatedBookCRUDView should not render the built-in bulk edit route when no bulk fields or bulk delete are configured."
    )
    assert ">Bulk Edit" not in response_text, (
        "AnnotatedBookCRUDView should not render the built-in Bulk Edit button for a selection-only extra button."
    )


@pytest.mark.django_db
def test_annotated_book_selected_summary_uses_annotated_selection(client: Client):
    """The annotated selection summary should read the annotated view selection key."""
    author = Author.objects.create(name="Annotation Summary Author")
    book = Book.objects.create(
        title="Selected Annotation Demo",
        author=author,
        published_date=date(2024, 4, 4),
        bestseller=False,
        isbn="9781234500204",
        pages=650,
    )
    view = sample_views.AnnotatedBookCRUDView()
    session = client.session
    session["powercrud_selections"] = {view.get_storage_key(): [str(book.pk)]}
    session.save()

    response = client.get(reverse("sample:annotated-book-selected-summary"))

    assert response.status_code == 200, (
        "Annotated selection summary should render successfully from persisted selection state."
    )
    response_text = response.content.decode()
    assert "Selected Annotation Demo" in response_text, (
        "Annotated selection summary should include selected books from the annotated view storage key."
    )
    assert "Long book:" in response_text, (
        "Annotated selection summary should include annotation-derived row metadata."
    )


@pytest.mark.django_db
def test_sample_menu_links_to_annotated_book_view(client: Client):
    """Sample navigation should expose the annotated book demo view."""
    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200, (
        "Book sample list should render before inspecting sample navigation."
    )
    response_text = response.content.decode()
    annotated_url = reverse("sample:annotated-book-list")
    assert "Annotated Books" in response_text, (
        "Sample navigation should include a visible annotated-books menu label."
    )
    assert f'hx-get="{annotated_url}"' in response_text, (
        "Sample navigation should expose the annotated-books route for HTMX loading."
    )
    assert f'href="{annotated_url}"' in response_text, (
        "Sample navigation should expose the annotated-books route for full-page reload."
    )


@pytest.mark.django_db
def test_powerfield_book_sample_view_matches_book_field_intent_config():
    """PowerField Book sample should resolve to the primitive Book config shape."""
    primitive_view = sample_views.BookCRUDView()
    powerfield_view = sample_views.PowerFieldBookCRUDView()

    exact_config_names = [
        "fields",
        "exclude",
        "detail_fields",
        "form_fields",
        "form_display_fields",
        "form_disabled_fields",
        "default_list_fields",
        "field_queryset_dependencies",
        "column_help_text",
        "column_alignments",
        "extra_actions_dropdown_open_upward_bottom_rows",
        "row_actions_column_position",
        "row_actions_column_sticky",
    ]
    for config_name in exact_config_names:
        assert getattr(powerfield_view, config_name) == getattr(
            primitive_view, config_name
        ), (
            "PowerFieldBookCRUDView should compile the same resolved "
            f"{config_name} as BookCRUDView."
        )

    assert primitive_view.extra_actions_mode == "dropdown" and powerfield_view.extra_actions_mode == "all_dropdown", (
        "PowerFieldBookCRUDView should deliberately contrast the compact all-actions menu with BookCRUDView's extras-only menu."
    )

    assert set(powerfield_view.properties) == set(primitive_view.properties), (
        "PowerFieldBookCRUDView should expose the same list property names as "
        "BookCRUDView, even when explicit declaration order differs from __all__."
    )
    assert set(powerfield_view.detail_properties) == set(
        primitive_view.detail_properties
    ), (
        "PowerFieldBookCRUDView should expose the same detail property names as "
        "BookCRUDView."
    )
    assert set(powerfield_view.inline_edit_fields) == set(
        primitive_view.inline_edit_fields
    ), (
        "PowerFieldBookCRUDView should expose the same inline-editable fields as "
        "BookCRUDView, while allowing declaration order to follow field grouping."
    )
    assert set(powerfield_view.bulk_fields) == set(primitive_view.bulk_fields), (
        "PowerFieldBookCRUDView should expose the same bulk-editable fields as "
        "BookCRUDView, while allowing declaration order to follow field grouping."
    )
    assert "uneditable_field" in powerfield_view.fields, (
        "PowerFieldBookCRUDView should expose the same uneditable list column "
        "as BookCRUDView while retaining its display-only form intent."
    )
    assert "description" not in powerfield_view.fields, (
        "PowerFieldBookCRUDView should mirror BookCRUDView by excluding the "
        "form-only description field from otherwise complete list columns."
    )
    assert powerfield_view.list_cell_tooltip_fields == {
        "title": "get_title_tooltip",
        "pages": {"hook": "get_pages_tooltip", "mode": "lazy"},
        "isbn_empty": "get_isbn_empty_tooltip",
    }, (
        "PowerFieldBookCRUDView should compile tooltip_hook declarations to the "
        "same primitive tooltip mapping as BookCRUDView, including lazy mode where configured."
    )

    primitive_links = primitive_view.link_fields
    powerfield_links = {
        field_name: dict(link_config)
        for field_name, link_config in powerfield_view.link_fields.items()
    }
    powerfield_links["pages"]["view_name"] = "sample:bigbook-detail"
    assert powerfield_links == primitive_links, (
        "PowerFieldBookCRUDView should match BookCRUDView link_fields after "
        "normalising the intentional pages detail route difference."
    )

    assert powerfield_view.form_class is primitive_view.form_class, (
        "PowerFieldBookCRUDView should use the same custom BookForm as BookCRUDView "
        "for clone-equivalence testing."
    )
    assert primitive_view.get_column_width_policy() == "semantic", (
        "The ordinary Book sample should demonstrate semantic list-column sizing."
    )
    assert powerfield_view.get_column_width_policy() == "semantic", (
        "The PowerField Book sample should demonstrate the same semantic list-column sizing."
    )


@pytest.mark.django_db
def test_powerfield_book_sample_class_config_exposes_generated_form_intent():
    """Class-time config should expose form intent before BookForm takes over."""
    cfg = resolve_class_config(sample_views.PowerFieldBookCRUDView)

    assert cfg.form_fields == [
        "title",
        "author",
        "published_date",
        "pages",
        "bestseller",
        "isbn",
        "genres",
        "description",
    ], (
        "PowerFieldBookCRUDView should still compile form=True declarations before "
        "runtime form_class handling clears generated form_fields."
    )


@pytest.mark.django_db
def test_powerfield_book_sample_routes_are_generated():
    """PowerField Book sample should expose normal CRUD and feature routes."""
    expected_route_names = [
        "powerfield-book-list",
        "powerfield-book-detail",
        "powerfield-book-create",
        "powerfield-book-update",
        "powerfield-book-delete",
        "powerfield-book-bulk-edit",
        "powerfield-book-inline-row",
        "powerfield-book-inline-dependency",
        "powerfield-book-columns",
    ]

    for route_name in expected_route_names:
        needs_pk = any(
            token in route_name
            for token in ["detail", "update", "delete", "inline-row", "inline-dependency"]
        )
        url = reverse(f"sample:{route_name}", args=[1] if needs_pk else None)
        assert url, f"Expected sample:{route_name} to reverse for the PowerField Book sample."


@pytest.mark.django_db
def test_powerfield_book_sample_list_renders(client: Client):
    """PowerField Book sample list route should render through the sample app."""
    _login_sample_manager(client)
    author = Author.objects.create(name="PowerField Author")
    book = Book.objects.create(
        title="PowerField Sample Book",
        author=author,
        published_date=date(2024, 2, 1),
        bestseller=False,
        isbn="9781234500204",
        pages=144,
    )

    response = client.get(reverse("sample:powerfield-book-list"))

    assert response.status_code == 200, (
        "PowerFieldBookCRUDView list route should render successfully."
    )
    response_text = response.content.decode()
    assert "PowerField Sample Book" in response_text, (
        "PowerFieldBookCRUDView should render Book rows through the compiled list config."
    )
    assert 'href="https://www.isbn-international.org/content/what-isbn"' in response_text, (
        "PowerFieldBookCRUDView should render the PowerField external link."
    )
    assert reverse("sample:powerfield-book-inline-row", args=[book.pk]) in response_text, (
        "PowerFieldBookCRUDView should render inline-row endpoint URLs into list markup."
    )
    assert 'data-powercrud-row-actions-position="end"' in response_text, (
        "PowerFieldBookCRUDView should render its row actions at the same logical end as BookCRUDView."
    )
    assert 'data-powercrud-row-actions-sticky="true"' in response_text, (
        "PowerFieldBookCRUDView should keep the same horizontally sticky row actions as BookCRUDView."
    )
    assert "data-powercrud-row-actions-scope='all'" in response_text and "aria-label='Actions'" in response_text, (
        "PowerFieldBookCRUDView should demonstrate the compact all-actions menu on its logical-end sticky column."
    )


@pytest.mark.django_db
def test_sample_menu_links_to_powerfield_book_view(client: Client):
    """Sample navigation should expose the PowerField Book demo view."""
    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200, (
        "Book sample list should render before inspecting sample navigation."
    )
    response_text = response.content.decode()
    powerfield_url = reverse("sample:powerfield-book-list")
    assert "PowerField Books" in response_text, (
        "Sample navigation should include a visible PowerField Books menu label."
    )
    assert f'hx-get="{powerfield_url}"' in response_text, (
        "Sample navigation should expose the PowerField Books route for HTMX loading."
    )
    assert f'href="{powerfield_url}"' in response_text, (
        "Sample navigation should expose the PowerField Books route for full-page reload."
    )
    book_group = response_text.index('aria-label="Book List buttons"')
    powerfield_group = response_text.index(
        'aria-label="PowerField Book List buttons"'
    )
    annotated_group = response_text.index(
        'aria-label="Annotated Book List buttons"'
    )
    assert book_group < powerfield_group < annotated_group, (
        "Sample navigation should place PowerField Books immediately after Books "
        "and before Annotated Books."
    )


@pytest.mark.django_db
def test_page_size_query_label_prefers_url_value_when_default_is_all(client: Client):
    """The page-size selector should not display All when the URL requests a finite size."""
    for index in range(30):
        Genre.objects.create(name=f"Selector Genre {index:02d}")

    response = client.get(reverse("sample:genre-list"), {"page_size": "25"})

    assert response.status_code == 200, (
        "Genre sample list should render before inspecting page-size selection."
    )
    response_text = " ".join(response.content.decode().split())
    assert '<option value="25" selected >25</option>' in response_text, (
        "Page-size selector should mark the requested finite page size as selected."
    )
    assert '<option value="all" selected' not in response_text, (
        "Page-size selector should not also select All when page_size=25 is active."
    )


@pytest.mark.django_db
def test_book_sample_view_demonstrates_property_link_fields():
    """Book sample view should expose a real list-cell link demo on a non-inline property column."""
    author = Author.objects.create(name="Link Demo Author")
    book = Book.objects.create(
        title="Linked Sample Book",
        author=author,
        published_date=date(2024, 1, 1),
        bestseller=False,
        isbn="9781234500099",
        pages=321,
    )

    view = sample_views.BookCRUDView()
    request = RequestFactory().get("/")
    request.session = {}
    view.request = request

    row = powercrud_tags.object_list({"request": request}, [book], view)["object_list"][
        0
    ]
    cell_map = {cell["name"]: cell for cell in row["cells"]}

    assert (
        cell_map["a_really_long_property_header_for_title"]["link"]["url"]
        == reverse("sample:author-detail", kwargs={"pk": author.pk})
    ), "BookCRUDView should keep a real sample list-cell link on its non-inline title-like property column, now targeting the related author detail."
    assert (
        cell_map["a_really_long_property_header_for_title"]["link"]["open_in"]
        == "modal"
    ), "BookCRUDView should demonstrate view-default modal list-cell links on its existing non-inline sample column."
    assert sample_views.BookCRUDView.list_cell_link_default_open_in == "modal", (
        "BookCRUDView should make modal opening the view-wide default for list-cell link demos."
    )
    assert cell_map["pages"]["tooltip_text"] is None, (
        "BookCRUDView should defer the lazy pages tooltip during list rendering."
    )
    assert cell_map["pages"]["tooltip_mode"] == "lazy", (
        "BookCRUDView should mark the visible non-inline pages field for lazy semantic tooltip hydration."
    )
    assert cell_map["pages"]["tooltip_url"] == reverse(
        "sample:bigbook-cell-tooltip",
        kwargs={"pk": book.pk, "field_name": "pages"},
    ), (
        "BookCRUDView should expose the lazy tooltip endpoint for the visible non-inline pages field."
    )
    assert cell_map["pages"]["link"] == {
        "url": reverse("sample:bigbook-detail", kwargs={"pk": book.pk}),
        "classes": "link link-info",
        "open_in": "current",
    }, "BookCRUDView should demonstrate current-page list-cell links on a visible non-inline sample field."
    assert cell_map["isbn"]["is_inline_editable"] is False, (
        "BookCRUDView should keep ISBN out of inline editing so the external-link demo remains clickable."
    )
    assert cell_map["isbn"]["link"] == {
        "url": "https://www.isbn-international.org/content/what-isbn",
        "classes": "link link-info",
        "open_in": "new",
        "target": "_blank",
        "rel": "noopener noreferrer",
    }, "BookCRUDView should demonstrate declarative static URL list-cell links on a visible non-inline sample field."


@pytest.mark.django_db
def test_book_sample_list_renders_external_link_field_attrs(client: Client):
    """Book sample list should render the declarative static URL demo as a safe external link."""
    author = Author.objects.create(name="External Link Render Author")
    Book.objects.create(
        title="External Link Render Book",
        author=author,
        published_date=date(2024, 1, 2),
        bestseller=False,
        isbn="9781234500105",
        pages=222,
    )

    response = client.get(reverse("sample:bigbook-list"))

    assert response.status_code == 200, (
        "Book sample list should render successfully before inspecting link-field attributes."
    )
    response_text = response.content.decode()
    assert "container mt-20 mb-5 mx-5 p-5" not in response_text, (
        "Sample base template should not keep the old large top margin wrapper."
    )
    assert 'class="box-border w-full px-5 py-5"' in response_text, (
        "Sample base template should use the full available page width with safe internal padding."
    )
    assert 'href="https://www.isbn-international.org/content/what-isbn"' in response_text, (
        "Book sample list should render the static external URL from link_fields."
    )
    assert 'data-tippy-content="Demo link: opens this book detail in the current page."' in response_text, (
        "Book sample Pages header should explain the current-page link demo."
    )
    assert 'data-tippy-content="Demo link: opens an external ISBN reference in a new tab or window."' in response_text, (
        "Book sample ISBN header should explain the new-context link demo."
    )
    assert 'data-tippy-content="Demo link: opens the related author detail in a larger PowerCRUD modal."' in response_text, (
        "Book sample Really Long Title header should explain the modal link demo."
    )
    assert 'data-powercrud-modal-size="extra_wide"' in response_text, (
        "Book sample modal list-cell link should request the larger portable modal preset."
    )
    assert 'target="_blank"' in response_text, (
        "Book sample external URL demo should request a new browser context."
    )
    assert 'rel="noopener noreferrer"' in response_text, (
        "Book sample external URL demo should render the default safe rel value."
    )


@pytest.mark.django_db
def test_book_sample_inline_row_endpoint_renders_edit_form(monkeypatch):
    """Book sample inline row endpoint should still return editable row markup."""
    author = Author.objects.create(name="Inline Author")
    genre = Genre.objects.create(name="Inline Genre")
    author.genres.add(genre)
    book = Book.objects.create(
        title="Inline Endpoint Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9781234500002",
        pages=89,
    )
    book.genres.set([genre])

    monkeypatch.setattr(
        sample_views.BookCRUDView,
        "is_inline_row_locked",
        lambda self, obj: False,
    )
    client = Client()
    _login_sample_manager(client)
    response = client.get(
        reverse("sample:bigbook-inline-row", args=[book.pk]),
        HTTP_HX_REQUEST="true",
    )

    assert (
        response.status_code == 200
    ), "The sample inline row endpoint should render successfully for editable rows."
    assert (
        b"data-inline-save" in response.content
    ), "The sample inline row endpoint should include inline save controls."
    assert (
        b'type="hidden" name="description"' in response.content
    ), "The sample inline row endpoint should repost non-rendered full-form fields like description as hidden inputs."


@pytest.mark.django_db
def test_book_sample_inline_row_respects_session_list_columns(monkeypatch):
    """Inline row renders should use the same active list columns as the parent list."""

    author = Author.objects.create(name="Inline Column Author")
    genre = Genre.objects.create(name="Inline Column Genre")
    author.genres.add(genre)
    book = Book.objects.create(
        title="Inline Column Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9781234500006",
        pages=89,
    )
    book.genres.set([genre])

    monkeypatch.setattr(
        sample_views.BookCRUDView,
        "is_inline_row_locked",
        lambda self, obj: False,
    )
    client = Client()
    session = client.session
    session[LIST_OPTIONS_SESSION_KEY] = {
        f"{sample_views.BookCRUDView.__module__}.{sample_views.BookCRUDView.__name__}": {
            "visible_columns": ["title", "author", "published_date"],
        }
    }
    session.save()
    _login_sample_manager(client)

    response = client.get(
        reverse("sample:bigbook-inline-row", args=[book.pk]),
        HTTP_HX_REQUEST="true",
    )

    assert (
        response.status_code == 200
    ), "The sample inline row endpoint should render successfully with session-backed list columns."
    response_text = response.content.decode()
    assert 'data-field-name="title"' in response_text, (
        "Inline row markup should retain active list columns when the column chooser hides other fields."
    )
    assert 'data-field-name="author"' in response_text, (
        "Inline row markup should retain active relation columns when the column chooser hides other fields."
    )
    assert 'data-field-name="isbn"' not in response_text, (
        "Inline row markup should not render cells for hidden model columns."
    )
    assert 'data-field-name="a_really_long_property_header_for_title"' not in response_text, (
        "Inline row markup should not render cells for hidden property columns."
    )


@pytest.mark.django_db
def test_book_sample_list_renders_inline_trigger_targets(monkeypatch):
    """Book sample list rows should render inline trigger buttons with HTMX targets."""
    author = Author.objects.create(name="Inline List Author")
    book = Book.objects.create(
        title="Inline List Book",
        author=author,
        published_date="2024-01-01",
        bestseller=False,
        isbn="9781234500003",
        pages=90,
        description="List page regression",
    )

    monkeypatch.setattr(
        sample_views.BookCRUDView,
        "is_inline_row_locked",
        lambda self, obj: False,
    )
    client = Client()
    _login_sample_manager(client)
    response = client.get(
        reverse("sample:bigbook-list"),
    )

    assert (
        response.status_code == 200
    ), "The sample list page should render successfully when inline editing is enabled."
    assert (
        f'id="pc-row-{book.pk}"'.encode() in response.content
    ), "Sample list rows should render stable DOM ids so inline swaps have a valid HTMX target."
    assert (
        reverse("sample:bigbook-inline-row", args=[book.pk]).encode() in response.content
    ), "Sample list rows should render the inline-row endpoint URL into the trigger button markup."
    assert (
        b'hx-target="#pc-row-' in response.content
    ), "Sample inline trigger buttons should target the row DOM id for outerHTML swaps."
    assert (
        re.search(rb"<tr[^>]*data-inline-active=\"true\"", response.content) is None
    ), "The sample list page should not render an already-active inline row on initial load."
