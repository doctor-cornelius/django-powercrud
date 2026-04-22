from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from neapolitan.views import CRUDView
from powercrud.mixins.async_crud_mixin import PowerCRUDAsyncMixin
from powercrud.conf import get_powercrud_setting

from . import models
from . import forms
from .services import BookBulkUpdateService
class SampleCRUDMixin(PowerCRUDAsyncMixin, CRUDView):
    """Base mixin to ensure sample views use the dashboard-aware manager."""

    async_manager_class_path = "sample.async_manager.SampleAsyncManager"


def home(request):
    """Render the sample home page."""
    template_name = (
        f"sample/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}/index.html"
    )
    context = {"header_title": "Home"}
    if request.htmx:
        return render(request, f"{template_name}#content", context)
    return render(request, template_name, context)


class BookCRUDView(SampleCRUDMixin):
    """Full-featured sample CRUD view for the Book model."""

    model = models.Book
    view_title = "My List of Books"
    view_instructions = "Here you can edit books"
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True
    # use_crispy = False

    # standard neapolitan setting; this demonstrates how to override the default url_base (ie model name)
    # useful if you want multiple CRUDViews for the same model
    url_base = "bigbook"
    paginate_by = 5

    # use_crispy = False

    # fields = ["author","title","published_date",]
    fields = "__all__"
    exclude = ["description"]
    properties = "__all__"
    column_help_text = {
        "title": "The book title shown throughout the app.",
        "isbn_empty": "Shows whether this row currently has an ISBN value.",
    }
    list_cell_tooltip_fields = ["title", "isbn_empty"]
    detail_fields = "__all__"
    detail_properties = "__all__"

    bulk_fields = [
        "title",
        "published_date",
        "bestseller",
        "pages",
        "author",
        "genres",
    ]
    bulk_delete = True
    bulk_async = True
    bulk_min_async_records = 2
    bulk_update_persistence_backend_path = "sample.backends.BookBulkUpdateBackend"

    form_display_fields = ["uneditable_field"]
    form_disabled_fields = ["isbn"]
    form_class = forms.BookForm
    field_queryset_dependencies = {
        "genres": {
            "depends_on": ["author"],
            "filter_by": {"authors": "author"},
            "order_by": "name",
            "empty_behavior": "all",
        }
    }

    # filterset_class = filters.BookFilterSet
    filterset_fields = [
        "author",
        "title",
        "published_date",
        "isbn",
        "pages",
        "description",
        "genres",
        "bestseller",
    ]
    default_filterset_fields = [
        "author",
        "title",
        "published_date",
        "bestseller",
    ]
    filter_favourites_enabled = True
    # Define how filter dropdown options should be sorted
    dropdown_sort_options = {
        "author": "name",  # Sort authors by name field in all dropdowns
        "unknown_model": "zebra_face",
    }
    m2m_filter_and_logic = False  # Use AND logic for M2M filters

    # filter_queryset_options = {
    #     'author': {
    #         # 'name': 'Nancy Wilson',
    #         # 'name__in': ['Nancy Wilson', 'Thomas Adams', ],
    #         'name__icontains': 'Nancy',
    #     },
    # }

    table_pixel_height_other_page_elements = 100
    table_max_height = 80
    table_header_min_wrap_width = "15"  # characters
    table_max_col_width = "25"  # characters

    table_classes = "table-zebra table-sm"
    # action_button_classes = 'btn-sm min-h-0 h-6 leading-6'
    action_button_classes = "btn-xs"
    extra_button_classes = "btn-sm"
    extra_actions_mode = "dropdown"
    extra_actions_dropdown_open_upward_bottom_rows = 5

    inline_edit_always_visible = True # default is True
    inline_edit_highlight_accent = "#f40b0b"  # default is "#14b8a6"

    inline_preserve_required_fields = True  # toggle for testing
    inline_edit_fields = [
        "title",
        "author",
        "genres",
        "published_date",
        "bestseller",
        "isbn",
        # "pages",
        "description",
    ]

    # Example of overrides of get_queryset and get_filter_queryset_for_field
    # def get_queryset(self):
    #     qs = super().get_queryset()
    #     qs = qs.filter(author__id=20)
    #     return qs.select_related('author')

    # def get_filter_queryset_for_field(self, field_name, model_field):
    #     """Override to restrict the available options if the field is author.
    #     """
    #     qs = super().get_filter_queryset_for_field(field_name, model_field)
    #     print(field_name)
    #     if field_name == 'author':
    #         qs = qs.filter(id=20)
    #     return qs

    extra_buttons = [
        {
            "url_name": "home",
            "text": "Home",
            "button_class": "btn-success",
            "htmx_target": "content",
            "needs_pk": False,
            "display_modal": False,
            "extra_class_attrs": "",
            "extra_attrs": 'hx-push-url="false" hx-replace-url="false"',
        },
        {
            "url_name": "home",
            "text": "Home in Modal!",
            "button_class": "btn-warning",
            "htmx_target": "content",
            "display_modal": True,  # NB if True then htmx_target is ignored
            "extra_class_attrs": "bg-warning",
        },
        {
            "url_name": "sample:bigbook-selected-summary",
            "text": "Selected Summary",
            "button_class": "btn-primary",
            "display_modal": True,
            "uses_selection": True,
            "selection_min_count": 1,
            "selection_min_behavior": "disable",
            "selection_min_reason": "Select at least one book first.",
        },
    ]

    extra_actions = [
        {
            "url_name": "sample:bigbook-update",  # namespace:url_pattern
            "text": "Normal Edit",  # bypasses powercrud & uses regular view
            "needs_pk": True,  # if the URL needs the object's primary key
            "button_class": "btn-info",
            "htmx_target": "powercrudModalContent",
            "display_modal": True,
            "lock_sensitive": True,  # this will be greyed out if async locks in force
        },
        {
            "url_name": "sample:bigbook-description-preview",
            "text": "Description Preview",
            "needs_pk": True,
            "button_class": "btn-secondary",
            "htmx_target": "powercrudModalContent",
            "display_modal": True,
            "disabled_if": "is_description_preview_disabled",
            "disabled_reason": "get_description_preview_disabled_reason",
        },
    ]

    def is_description_preview_disabled(self, obj, request):
        """Return True when the row lacks description content for preview."""
        return not bool((obj.description or "").strip())

    def get_description_preview_disabled_reason(self, obj, request):
        """Return the tooltip shown when description preview is unavailable."""
        if self.is_description_preview_disabled(obj, request):
            return "This book does not have a description yet."
        return None

    def get_list_cell_tooltip(self, obj, field_name, *, is_property, request=None):
        """Return semantic tooltip text for selected list cells in the sample app."""
        if field_name == "title":
            return f"{obj.author}\n{obj.pages} pages"
        if field_name == "isbn_empty":
            if obj.isbn_empty:
                return "This book does not currently have an ISBN."
            return f"ISBN: {obj.isbn}"
        return None

    def can_update_object(self, obj, request):
        """Disable update affordances for the guarded sample row."""
        return obj.title != models.Book.GUARDED_SAMPLE_TITLE

    def get_update_disabled_reason(self, obj, request):
        """Explain why the guarded sample row cannot be edited."""
        if not self.can_update_object(obj, request):
            return "Guarded Sample Book demonstrates built-in Edit and inline update guards."
        return None

    def persist_single_object(self, *, form, mode, instance=None):
        """Sample override showing where downstream form/inline writes can hook in."""
        return super().persist_single_object(
            form=form,
            mode=mode,
            instance=instance,
        )

    def persist_bulk_update(
        self,
        *,
        queryset,
        fields_to_update,
        field_data,
        progress_callback=None,
    ):
        """Route sync bulk writes through the sample bulk service."""
        return BookBulkUpdateService().apply(
            queryset=queryset,
            bulk_fields=list(self.bulk_fields),
            fields_to_update=fields_to_update,
            field_data=field_data,
            context=self._build_bulk_update_execution_context(
                queryset=queryset,
                mode="sync",
            ),
            progress_callback=progress_callback,
        )

    # def get_bulk_choices_for_field(self, field_name, field):
    #     """Example of how to override to further restrict foreign key choices for
    #         dropdown in bulk edit form.
    #     """
    #     if field_name == 'author' and hasattr(field, "related_model") and field.related_model is not None:
    #         return field.related_model.objects.filter(
    #             id=19
    #         )
    #     return super().get_bulk_choices_for_field(field_name, field)


class GenreCRUDView(SampleCRUDMixin):
    model = models.Genre
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True

    table_classes = "table-zebra table-sm"
    action_button_classes = "btn-xs"
    extra_button_classes = "btn-sm"

    # ensure duplicates are de-duplicated
    fields = ["name", "numeric_string", "name",]
    inline_edit_fields = [
        "name", "numeric_string", "name",
    ]

    def can_delete_object(self, obj, request):
        """Disable the built-in Delete action for the guarded sample row."""
        return obj.name != models.Genre.GUARDED_SAMPLE_NAME

    def get_delete_disabled_reason(self, obj, request):
        """Explain why the guarded sample row cannot be deleted from the UI."""
        if not self.can_delete_object(obj, request):
            return "Guarded Sample Genre demonstrates built-in Delete disable hooks."
        return None


class ProfileCRUDView(SampleCRUDMixin):
    """Sample CRUD view demonstrating centered categorical list columns."""

    model = models.Profile
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True

    table_classes = "table-zebra table-sm"
    action_button_classes = "btn-xs"
    extra_button_classes = "btn-sm"

    fields = "__all__"
    properties = "__all__"
    column_alignments = {
        "status": "center",
        "priority_band": "right",
        "favorite_genre": "left",
    }
    filterset_fields = ["author", "nickname", "favorite_genre"]
    filter_favourites_enabled = True
    inline_edit_fields = ["nickname", "status", "priority_band", "favorite_genre"]
    field_queryset_dependencies = {
        "favorite_genre": {
            "static_filters": {"name__startswith": "S"},
            "order_by": "name",
        }
    }

    # Add the OneToOneField to bulk_fields to test it
    bulk_fields = [
        "author",  # OneToOneField
        "nickname",
        "status",
        "priority_band",
        "favorite_genre",
    ]


class AuthorCRUDView(SampleCRUDMixin):
    model = models.Author
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True

    show_record_count = True

    table_classes = "table-zebra table-sm"
    action_button_classes = "btn-xs"
    extra_button_classes = "btn-sm"

    paginate_by = 15

    # fields = ["name","bio","birth_date",]
    fields = "__all__"
    # exclude = ['bio',]
    # filter_favourites_enabled = True
    # filterset_class = AuthorFilterSet
    filterset_fields = ["name", "birth_date", "genres"]
    default_filterset_fields = ["name", "birth_date", "genres"]
    properties = "__all__"
    # properties_exclude = ['has_bio',]
    detail_fields = "__fields__"
    detail_properties = "__properties__"

    # inline_edit_enabled = True # deprecated
    inline_edit_fields = "__fields__"

    bulk_fields = [
        "genres",
    ]

    extra_actions = [
        {
            "url_name": "home",  # namespace:url_pattern
            "text": "Home",
            "needs_pk": False,  # if the URL needs the object's primary key
            "button_class": "btn-warning",
            "htmx_target": "powercrudModalContent",
            "display_modal": True,
        },
        {
            "url_name": "sample:author-detail",
            "text": "View Again",
            "needs_pk": True,  # if the URL needs the object's primary key
            "htmx_target": "powercrudModalContent",
            "display_modal": True,
        },
    ]


class AsyncTaskRecordCRUDView(SampleCRUDMixin):
    model = models.AsyncTaskRecord
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True
    bulk_delete = True

    fields = [
        "id",
        "task_name",
        "user_label",
        "status",
        "cleaned_up",
        "completed_at",
        "failed_at",
    ]
    paginate_by = 25
    table_header_min_wrap_width = "15"  # characters
    table_max_col_width = "35"  # characters
    view_action = False

    extra_actions = [
        {
            "url_name": "sample:async-dashboard-detail",
            "text": "View Progress",
            "needs_pk": True,  # if the URL doesn't need the object's primary key
            "htmx_target": "#powercrudModalContent",
            "display_modal": True,
        },
    ]


def async_task_detail(request, pk):
    """Render a modal/detail view for one async task record."""
    record = get_object_or_404(models.AsyncTaskRecord, pk=pk)
    framework = get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK")
    template = f"sample/{framework}/async_task_detail.html"
    if request.htmx:
        template += "#pcrud_content"
    progress_url = reverse("powercrud:async_progress")
    context = {
        "record": record,
        "progress_url": progress_url,
    }
    return render(request, template, context)


def book_selected_summary(request):
    """Render a sample modal summarizing the current persisted book selection."""
    framework = get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK")
    template = f"sample/{framework}/book_selected_summary.html"
    if request.htmx:
        template += "#pcrud_content"

    view = BookCRUDView()
    selected_ids = view.get_selected_ids_for_extra_button(
        request,
        {"uses_selection": True},
    )
    selected_books = list(
        models.Book.objects.filter(pk__in=selected_ids)
        .select_related("author")
        .order_by("title")
    )
    context = {
        "selected_books": selected_books,
        "selected_count": len(selected_books),
        "selection_required_message": "Select at least one book first.",
    }
    return render(request, template, context)


def book_description_preview(request, pk):
    """Render a sample modal previewing one book description."""
    book = get_object_or_404(models.Book, pk=pk)
    framework = get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK")
    template = f"sample/{framework}/book_description_preview.html"
    if request.htmx:
        template += "#pcrud_content"

    context = {
        "book": book,
        "has_description": bool((book.description or "").strip()),
    }
    return render(request, template, context)
