from django.contrib.auth import get_user_model, login, logout
from django.db.models import BooleanField, Case, Value, When
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from neapolitan.views import CRUDView
from powercrud.mixins.async_crud_mixin import PowerCRUDAsyncMixin
from powercrud.conf import get_powercrud_setting
from powercrud.actions import PowerAction, PowerButton
from powercrud.powerfields import PowerField, PowerOverride

from . import models
from . import forms
from .services import BookBulkUpdateService


SAMPLE_DEMO_USERS = {
    "viewer": {
        "username": "sample-viewer",
        "email": "sample-viewer@example.com",
        "is_staff": False,
    },
    "manager": {
        "username": "sample-manager",
        "email": "sample-manager@example.com",
        "is_staff": True,
    },
}


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


def _sample_next_url(request):
    """Return a safe local redirect target for sample auth actions."""
    fallback = reverse("sample:bigbook-list")
    next_url = request.POST.get("next") or request.GET.get("next") or fallback
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback


def sample_demo_login(request, role):
    """Log in as one of the sample demo users without a password form."""
    if request.method != "POST":
        return HttpResponseBadRequest("Sample demo login requires POST.")

    demo_user = SAMPLE_DEMO_USERS.get(role)
    if demo_user is None:
        return HttpResponseBadRequest("Unknown sample demo role.")

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

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect(_sample_next_url(request))


def sample_demo_logout(request):
    """Log out the current sample demo user."""
    if request.method != "POST":
        return HttpResponseBadRequest("Sample demo logout requires POST.")
    logout(request)
    return redirect(_sample_next_url(request))


def sample_user_can_preview_descriptions(user):
    """Return whether the sample user can open description preview actions."""
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.get_username() == SAMPLE_DEMO_USERS["manager"]["username"]
        )
    )


def sample_user_can_use_selected_summaries(user):
    """Return whether the sample user can open selected-summary toolbar actions."""
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.get_username() == SAMPLE_DEMO_USERS["manager"]["username"]
        )
    )


def sample_user_can_manage_books(user):
    """Return whether the sample user can use built-in book mutation actions."""
    return sample_user_can_use_selected_summaries(user)


class BookCRUDView(SampleCRUDMixin):
    """Full-featured sample CRUD view for the Book model."""

    model = models.Book
    view_title = "My List of Books"
    view_instructions = "Here you can edit books"
    view_help = {
        "summary": "About this feature demo",
        "details": (
            "This Books screen demonstrates many PowerCRUD features in one place."
            "\n\n"
            "Use it to inspect list options, inline editing, saved filter favourites, "
            "bulk actions, async workflows, modal links, external links, selection-aware "
            "toolbar actions, and guarded update behaviour."
            "\n\n"
            "Use the sample login menu as viewer or manager to compare permission-hidden "
            "actions with row-state disabled actions."
        ),
        "color": "info",
    }
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True
    # use_crispy = False

    # standard neapolitan setting; this demonstrates how to override the default url_base (ie model name)
    # useful if you want multiple CRUDViews for the same model
    url_base = "bigbook"
    page_size_options = [5, 10, 25, 50]
    page_size_all_enabled = False

    # use_crispy = False

    # fields = ["author","title","published_date",]
    fields = "__all__"
    exclude = ["description"]
    properties = "__all__"
    list_options_enabled = True
    default_list_fields = [
        "title",
        "author",
        "published_date",
        "pages",
        "bestseller",
        "isbn",
        "genres",
        "isbn_empty",
        "a_really_long_property_header_for_title",
    ]
    column_help_text = {
        "title": "The book title shown throughout the app.",
        "pages": "Demo link: opens this book detail in the current page.",
        "isbn": "Demo link: opens an external ISBN reference in a new tab or window.",
        "isbn_empty": "Shows whether this row currently has an ISBN value.",
        "description_empty": "Shows whether this row currently has description text.",
        "a_really_long_property_header_for_title": (
            "Demo link: opens the related author detail in a larger PowerCRUD modal."
        ),
    }
    list_cell_tooltip_fields = {
        "title": "get_title_tooltip",
        "pages": {"hook": "get_pages_tooltip", "mode": "lazy"},
        "isbn_empty": "get_isbn_empty_tooltip",
    }
    list_cell_link_default_open_in = "modal"
    link_fields = {
        "a_really_long_property_header_for_title": {
            "view_name": "sample:author-detail",
            "pk_attr": "author_id",
            "modal_box_classes": (
                "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 "
                "max-w-6xl flex-col"
            ),
        },
        "pages": {
            "view_name": "sample:bigbook-detail",
            "open_in": "current",
        },
        "isbn": {
            "url": "https://www.isbn-international.org/content/what-isbn",
            "open_in": "new",
        },
    }
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
    extra_buttons_mode = "dropdown"
    extra_actions_mode = "dropdown"
    extra_actions_dropdown_open_upward_bottom_rows = 5

    inline_edit_always_visible = True  # default is True

    inline_preserve_required_fields = True  # toggle for testing
    inline_edit_fields = [
        "title",
        "author",
        "genres",
        "published_date",
        "bestseller",
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
            "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-3xl flex-col",
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
            "permission_check": "can_use_selected_summary",
            "permission_behavior": "hide",
        },
        {
            "url_name": "sample:bigbook-selected-summary",
            "text": "Selected Summary (Do Not Clear)",
            "button_class": "btn-accent",
            "display_modal": True,
            "uses_selection": True,
            "clear_selection_on_success": False,
            "selection_min_count": 1,
            "selection_min_behavior": "disable",
            "selection_min_reason": "Select at least one book first.",
            "permission_check": "can_use_selected_summary",
            "permission_behavior": "hide",
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
            "refresh_list_on_modal_close": True,
            "permission_check": "can_manage_books",
            "permission_behavior": "hide",
            "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-4xl flex-col",
        },
        {
            "url_name": "sample:bigbook-description-preview",
            "text": "Description Preview",
            "needs_pk": True,
            "button_class": "btn-secondary",
            "htmx_target": "powercrudModalContent",
            "display_modal": True,
            "permission_check": "can_preview_description",
            "permission_behavior": "hide",
            "hidden_if": "should_hide_description_preview",
            "hidden_if_mode": "lazy",
            "disabled_state": "get_description_preview_disabled_state",
            "disabled_state_mode": "lazy",
            "modal_box_classes": "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 max-w-5xl flex-col",
        },
    ]

    def can_preview_description(self, request, obj=None):
        """Return whether the sample user can open description previews."""
        return sample_user_can_preview_descriptions(getattr(request, "user", None))

    def can_use_selected_summary(self, request, obj=None):
        """Return whether the sample user can open selected-summary buttons."""
        return sample_user_can_use_selected_summaries(getattr(request, "user", None))

    def can_manage_books(self, request, obj=None):
        """Return whether the sample user can use built-in book mutation actions."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_create_permission(self, request):
        """Return whether the sample user can create books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_detail_permission(self, request, obj):
        """Return whether the sample user can view book details."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_update_permission(self, request, obj):
        """Return whether the sample user can update books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_delete_permission(self, request, obj):
        """Return whether the sample user can delete books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_bulk_update_permission(self, request):
        """Return whether the sample user can bulk update books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_bulk_delete_permission(self, request):
        """Return whether the sample user can bulk delete books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def should_hide_description_preview(self, obj, request):
        """Return True when the preview action is not relevant for the row."""
        return obj.title.startswith("Hidden Preview")

    def get_description_preview_disabled_state(self, obj, request):
        """Return the disabled reason when preview should remain visible but unavailable."""
        if not bool((obj.description or "").strip()):
            return "This book does not have a description yet."
        return None

    def get_title_tooltip(self, obj, request=None):
        """Return the semantic tooltip text for the title list cell."""
        return f"{obj.author}\n{obj.pages} pages"

    def get_pages_tooltip(self, obj, request=None):
        """Return the semantic tooltip text for the pages list cell."""
        return f"Page count: {obj.pages}"

    def get_isbn_empty_tooltip(self, obj, request=None):
        """Return the semantic tooltip text for the ISBN-empty property cell."""
        if obj.isbn_empty:
            return "This book does not currently have an ISBN."
        return f"ISBN: {obj.isbn}"

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


class ManualStaticBookCRUDView(BookCRUDView):
    """Book sample view that exercises direct static asset loading."""

    base_template_path = "sample/manual_static/base.html"
    url_base = "manual-static-bigbook"


class AnnotatedBookCRUDView(SampleCRUDMixin):
    """Focused sample view for queryset annotation list and filter fields."""

    model = models.Book
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True
    url_base = "annotated-book"
    view_title = "Annotated Books"
    view_instructions = "Book rows with queryset-backed operational columns."
    paginate_by = 25

    queryset = models.Book.objects.select_related("author").annotate(
        long_book=Case(
            When(pages__gte=400, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    )
    fields = ["title", "author", "pages", "long_book", "published_date"]
    list_options_enabled = True
    default_list_fields = ["title", "author", "pages", "published_date"]
    detail_fields = "__fields__"
    properties = []
    column_help_text = {
        "long_book": "Queryset annotation: true when pages is at least 400."
    }
    column_alignments = {"long_book": "center"}
    list_cell_tooltip_fields = {"long_book": "get_long_book_tooltip"}
    filterset_fields = ["author", "long_book", "pages"]
    default_filterset_fields = ["author", "long_book"]
    inline_edit_fields = ["pages"]
    bulk_fields = []
    bulk_delete = False
    extra_button_classes = "btn-sm"
    extra_buttons = [
        PowerButton(
            text="Annotated Selection Summary",
            url_name="sample:annotated-book-selected-summary",
            button_class="btn-primary",
            display_modal=True,
            uses_selection=True,
            selection_min_count=1,
            selection_min_behavior="disable",
            selection_min_reason="Select at least one annotated book first.",
        )
    ]
    extra_actions = []

    def get_bulk_selection_key_suffix(self):
        """Keep the annotated-book demo selection separate from the main Book view."""
        return "annotated"

    def get_long_book_tooltip(self, obj, request=None):
        """Return semantic tooltip text for the annotation sample column."""
        if obj.long_book:
            return "This row was annotated as a long book."
        return "This row was annotated as a shorter book."


class PowerFieldBookCRUDView(SampleCRUDMixin):
    """Book sample view demonstrating Field Intent through power_fields."""

    model = models.Book
    namespace = "sample"
    base_template_path = "sample/base.html"
    use_htmx = True
    use_modal = True
    url_base = "powerfield-book"
    view_title = "PowerField Books"
    view_instructions = "Book rows configured through PowerField declarations."
    view_help = {
        "summary": "About the PowerField demo",
        "details": (
            "This Books variant demonstrates the PowerField helper API without "
            "replacing the existing primitive Books sample."
        ),
        "color": "info",
    }
    paginate_by = 5

    list_options_enabled = True
    list_cell_link_default_open_in = "modal"
    form_class = forms.BookForm
    power_fields = [
        PowerOverride(detail="__all__"),
        PowerField(
            "title",
            default_list=True,
            tooltip_hook="get_title_tooltip",
            form=True,
            inline=True,
            bulk=True,
            column={"help_text": "The book title shown throughout the app."},
        ),
        PowerField(
            "author",
            default_list=True,
            form=True,
            inline=True,
            bulk=True,
        ),
        PowerField(
            "published_date",
            default_list=True,
            form=True,
            inline=True,
            bulk=True,
        ),
        PowerField(
            "pages",
            default_list=True,
            tooltip_hook="get_pages_tooltip",
            tooltip_mode="lazy",
            form=True,
            bulk=True,
            column={
                "help_text": "Demo link: opens this book detail in the current page."
            },
            link={"view_name": "sample:powerfield-book-detail", "open_in": "current"},
        ),
        PowerField(
            "bestseller",
            default_list=True,
            form=True,
            inline=True,
            bulk=True,
        ),
        PowerField(
            "isbn",
            default_list=True,
            form=True,
            form_disabled=True,
            column={
                "help_text": (
                    "Demo link: opens an external ISBN reference in a new tab or window."
                )
            },
            link={
                "url": "https://www.isbn-international.org/content/what-isbn",
                "open_in": "new",
            },
        ),
        PowerField(
            "genres",
            default_list=True,
            form=True,
            inline=True,
            bulk=True,
            queryset_dependencies={
                "depends_on": ["author"],
                "filter_by": {"authors": "author"},
                "order_by": "name",
                "empty_behavior": "all",
            },
        ),
        PowerField(
            "isbn_empty",
            property=True,
            detail_property=True,
            default_list=True,
            tooltip_hook="get_isbn_empty_tooltip",
            column={"help_text": "Shows whether this row currently has an ISBN value."},
        ),
        PowerField(
            "description_empty",
            property=True,
            detail_property=True,
            column={
                "help_text": (
                    "Shows whether this row currently has description text."
                )
            },
        ),
        PowerField(
            "a_really_long_property_header_for_title",
            property=True,
            detail_property=True,
            default_list=True,
            column={
                "help_text": (
                    "Demo link: opens the related author detail in a larger PowerCRUD modal."
                )
            },
            link={
                "view_name": "sample:author-detail",
                "pk_attr": "author_id",
                "modal_box_classes": (
                    "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 "
                    "max-w-6xl flex-col"
                ),
            },
        ),
        PowerField("uneditable_field", form_display=True),
        PowerField("description", form=True, inline=True),
        PowerField(
            "there_are_so_many_pages_this_header_surely_will_wrap",
            property=True,
            detail_property=True,
        ),
    ]
    bulk_delete = True
    bulk_async = True
    bulk_min_async_records = 2
    bulk_update_persistence_backend_path = "sample.backends.BookBulkUpdateBackend"
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
    dropdown_sort_options = {
        "author": "name",
        "unknown_model": "zebra_face",
    }
    m2m_filter_and_logic = False
    table_pixel_height_other_page_elements = 100
    table_max_height = 80
    table_header_min_wrap_width = "15"
    table_max_col_width = "25"
    table_classes = "table-zebra table-sm"
    action_button_classes = "btn-xs"
    extra_button_classes = "btn-sm"
    extra_buttons_mode = "dropdown"
    extra_actions_mode = "dropdown"
    extra_actions_dropdown_open_upward_bottom_rows = 5
    inline_edit_always_visible = True
    inline_preserve_required_fields = True
    _home_button = PowerButton(
        text="Home",
        url_name="home",
        button_class="btn-success",
        htmx_target="content",
        display_modal=False,
        extra_class_attrs="",
        extra_attrs='hx-push-url="false" hx-replace-url="false"',
    )
    extra_buttons = [
        _home_button,
        _home_button.with_options(
            text="Home in Modal!",
            button_class="btn-warning",
            display_modal=True,
            extra_class_attrs="bg-warning",
            modal_box_classes=(
                "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 "
                "max-w-3xl flex-col"
            ),
        ),
        PowerButton(
            text="Selected Summary",
            url_name="sample:bigbook-selected-summary",
            button_class="btn-primary",
            display_modal=True,
            uses_selection=True,
            selection_min_count=1,
            selection_min_behavior="disable",
            selection_min_reason="Select at least one book first.",
            permission_check="can_use_selected_summary",
            permission_behavior="hide",
        ),
        PowerButton(
            text="Selected Summary (Do Not Clear)",
            url_name="sample:bigbook-selected-summary",
            button_class="btn-accent",
            display_modal=True,
            uses_selection=True,
            clear_selection_on_success=False,
            selection_min_count=1,
            selection_min_behavior="disable",
            selection_min_reason="Select at least one book first.",
            permission_check="can_use_selected_summary",
            permission_behavior="hide",
        ),
    ]
    _book_modal_action = PowerAction(
        text="Normal Edit",
        url_name="sample:bigbook-update",
        button_class="btn-info",
        htmx_target="powercrudModalContent",
        display_modal=True,
        lock_sensitive=True,
        refresh_list_on_modal_close=True,
        permission_check="can_manage_books",
        permission_behavior="hide",
        modal_box_classes=(
            "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 "
            "max-w-4xl flex-col"
        ),
    )
    extra_actions = [
        _book_modal_action,
        _book_modal_action.with_options(
            text="Description Preview",
            url_name="sample:bigbook-description-preview",
            button_class="btn-secondary",
            lock_sensitive=False,
            refresh_list_on_modal_close=False,
            permission_check="can_preview_description",
            permission_behavior="hide",
            hidden_if="should_hide_description_preview",
            hidden_if_mode="lazy",
            disabled_state="get_description_preview_disabled_state",
            disabled_state_mode="lazy",
            modal_box_classes=(
                "modal-box flex max-h-[calc(100dvh-2rem)] w-11/12 "
                "max-w-5xl flex-col"
            ),
        ),
    ]

    def can_preview_description(self, request, obj=None):
        """Return whether the sample user can open description previews."""
        return sample_user_can_preview_descriptions(getattr(request, "user", None))

    def can_use_selected_summary(self, request, obj=None):
        """Return whether the sample user can open selected-summary buttons."""
        return sample_user_can_use_selected_summaries(getattr(request, "user", None))

    def can_manage_books(self, request, obj=None):
        """Return whether the sample user can use built-in book mutation actions."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_create_permission(self, request):
        """Return whether the sample user can create PowerField books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_detail_permission(self, request, obj):
        """Return whether the sample user can view PowerField book details."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_update_permission(self, request, obj):
        """Return whether the sample user can update PowerField books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_delete_permission(self, request, obj):
        """Return whether the sample user can delete PowerField books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_bulk_update_permission(self, request):
        """Return whether the sample user can bulk update PowerField books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def has_power_bulk_delete_permission(self, request):
        """Return whether the sample user can bulk delete PowerField books."""
        return sample_user_can_manage_books(getattr(request, "user", None))

    def get_title_tooltip(self, obj, request=None):
        """Return the semantic tooltip text for the title list cell."""
        return f"{obj.author}\n{obj.pages} pages"

    def get_pages_tooltip(self, obj, request=None):
        """Return the semantic tooltip text for the pages list cell."""
        return f"Page count: {obj.pages}"

    def get_isbn_empty_tooltip(self, obj, request=None):
        """Return the semantic tooltip text for the ISBN-empty property cell."""
        if obj.isbn_empty:
            return "This book does not currently have an ISBN."
        return f"ISBN: {obj.isbn}"

    def should_hide_description_preview(self, obj, request):
        """Return True when the preview action is not relevant for the row."""
        return obj.title.startswith("Hidden Preview")

    def get_description_preview_disabled_state(self, obj, request):
        """Return the disabled reason for the helper-backed preview action."""
        if not bool((obj.description or "").strip()):
            return "This book does not have a description yet."
        return None

    def can_update_object(self, obj, request):
        """Disable update affordances for the guarded sample row."""
        return obj.title != models.Book.GUARDED_SAMPLE_TITLE

    def get_update_disabled_reason(self, obj, request):
        """Explain why the guarded sample row cannot be edited."""
        if not self.can_update_object(obj, request):
            return "Guarded Sample Book demonstrates built-in Edit and inline update guards."
        return None

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
    list_options_enabled = True
    default_list_fields = ["author", "nickname", "status", "priority_band"]
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
    inline_edit_highlight_accent = "#f40b0b"
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
    column_value_formats = {
        "updated_at": "time",
        "completed_at": "datetime",
    }

    fields = [
        "id",
        "task_name",
        "user_label",
        "status",
        "cleaned_up",
        "created_at",
        "updated_at",
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
    if not sample_user_can_use_selected_summaries(getattr(request, "user", None)):
        return HttpResponseForbidden("You cannot view selected book summaries.")

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


def annotated_book_selected_summary(request):
    """Render a sample modal summarizing the annotated-book selection."""
    framework = get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK")
    template = f"sample/{framework}/annotated_book_selected_summary.html"
    if request.htmx:
        template += "#pcrud_content"

    view = AnnotatedBookCRUDView()
    selected_ids = view.get_selected_ids_for_extra_button(
        request,
        {"uses_selection": True},
    )
    selected_books = list(
        models.Book.objects.filter(pk__in=selected_ids)
        .select_related("author")
        .annotate(
            long_book=Case(
                When(pages__gte=400, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .order_by("title")
    )
    context = {
        "selected_books": selected_books,
        "selected_count": len(selected_books),
        "selection_required_message": "Select at least one annotated book first.",
    }
    return render(request, template, context)


def book_description_preview(request, pk):
    """Render a sample modal previewing one book description."""
    book = get_object_or_404(models.Book, pk=pk)
    if not sample_user_can_preview_descriptions(getattr(request, "user", None)):
        return HttpResponseForbidden("You cannot preview book descriptions.")

    framework = get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK")
    template = f"sample/{framework}/book_description_preview.html"
    if request.htmx:
        template += "#pcrud_content"

    context = {
        "book": book,
        "has_description": bool((book.description or "").strip()),
    }
    return render(request, template, context)
