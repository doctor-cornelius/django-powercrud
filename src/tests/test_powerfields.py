import pytest
from django.core.exceptions import ImproperlyConfigured
from django.views import View

from powercrud.mixins.config_mixin import resolve_class_config
from powercrud.mixins.core_mixin import CoreMixin
from powercrud.mixins.url_mixin import UrlMixin
from powercrud.powerfields import (
    PowerField,
    PowerOverride,
    compile_powerfields,
    merge_powerfield_fragments,
)
from sample.models import Book


def test_powerfield_extracts_list_style_primitive_fragment():
    fragment = PowerField(
        "status",
        list=True,
        default_list=True,
        form=True,
        inline=True,
        bulk=True,
        tooltip=True,
    ).to_primitive_fragment()

    assert fragment == {
        "fields": ["status"],
        "default_list_fields": ["status"],
        "form_fields": ["status"],
        "inline_edit_fields": ["status"],
        "bulk_fields": ["status"],
        "list_cell_tooltip_fields": ["status"],
    }, "PowerField should expose list-style primitive contributions for one field."


def test_powerfield_extracts_mapping_primitive_fragment():
    fragment = PowerField(
        "status",
        column={"help_text": "Current status.", "alignment": "center"},
        queryset_dependencies={"static_filters": {"is_active": True}},
        link={"view_name": "workflow:status-detail", "open_in": "modal"},
    ).to_primitive_fragment()

    assert fragment == {
        "column_help_text": {"status": "Current status."},
        "column_alignments": {"status": "center"},
        "field_queryset_dependencies": {
            "status": {"static_filters": {"is_active": True}},
        },
        "link_fields": {
            "status": {"view_name": "workflow:status-detail", "open_in": "modal"},
        },
    }, "PowerField should expose mapping-style primitive contributions for one field."


def test_powerfield_rejects_include_and_exclude_for_same_dimension():
    with pytest.raises(ValueError, match="include and exclude"):
        PowerField("status", form=True, exclude={"form": True})


def test_powerfield_with_options_returns_changed_copy_without_mutating_original():
    original = PowerField(
        "status",
        list=True,
        default_list=True,
        tooltip=True,
        bulk=True,
    )

    copied = original.with_options(bulk=False)

    assert copied is not original, "with_options should return a new PowerField."
    assert original.bulk is True, "with_options should not mutate the source field."
    assert copied.bulk is False, "with_options should apply the requested change."
    assert copied.to_primitive_fragment() == {
        "fields": ["status"],
        "default_list_fields": ["status"],
        "list_cell_tooltip_fields": ["status"],
    }, "The copied PowerField should compile with the changed options."


def test_powerfield_with_options_reruns_validation():
    field = PowerField("status", form=True)

    with pytest.raises(ValueError, match="include and exclude"):
        field.with_options(exclude={"form": True})


def test_powerfield_with_options_rejects_unknown_options():
    field = PowerField("status")

    with pytest.raises(TypeError, match="unexpected keyword"):
        field.with_options(filter=True)


def test_merge_powerfield_fragments_preserves_order_and_merges_mappings():
    fragment = merge_powerfield_fragments(
        [
            PowerField("status", list=True, column={"help_text": "Current status."}),
            PowerField("status", list=True),
            PowerField("owner", list=True, column={"help_text": "Current owner."}),
        ]
    )

    assert fragment == {
        "fields": ["status", "owner"],
        "column_help_text": {
            "status": "Current status.",
            "owner": "Current owner.",
        },
    }, "Merged PowerField fragments should dedupe list values and combine mappings."


def test_poweroverride_extracts_sentinel_primitive_fragment():
    fragment = PowerOverride(
        list="__all__",
        detail="__all__",
        form="__all__",
    ).to_primitive_fragment()

    assert fragment == {
        "fields": "__all__",
        "detail_fields": "__all__",
        "form_fields": "__all__",
    }, "PowerOverride should expose primitive sentinel values for broad defaults."


def test_compile_powerfields_combines_override_fields_and_excludes():
    primitive_config = compile_powerfields(
        [
            PowerOverride(list="__all__", detail="__all__", form="__all__"),
            PowerField("status", inline=True, bulk=True),
            PowerField("internal_notes", exclude={"list": True, "form": True}),
        ]
    )

    assert primitive_config == {
        "fields": "__all__",
        "detail_fields": "__all__",
        "form_fields": "__all__",
        "inline_edit_fields": ["status"],
        "bulk_fields": ["status"],
        "exclude": ["internal_notes"],
        "form_fields_exclude": ["internal_notes"],
    }, (
        "Compiled PowerField config should combine broad defaults, explicit "
        "fields, and override excludes."
    )


def test_compile_powerfields_rejects_multiple_overrides():
    with pytest.raises(ValueError, match="at most one PowerOverride"):
        compile_powerfields(
            [
                PowerOverride(list="__all__"),
                PowerOverride(form="__all__"),
            ]
        )


def test_compile_powerfields_rejects_override_after_field():
    with pytest.raises(ValueError, match="first power_fields entry"):
        compile_powerfields(
            [
                PowerField("status", list=True),
                PowerOverride(form="__all__"),
            ]
        )


def test_compile_powerfields_rejects_unsupported_declarations():
    with pytest.raises(ValueError, match="PowerField or PowerOverride"):
        compile_powerfields([PowerField("status", list=True), "status"])


@pytest.mark.django_db
def test_powerfields_wire_into_core_mixin_primitive_config():
    class BookView(CoreMixin):
        model = Book
        power_fields = [
            PowerOverride(list="__all__", detail="__all__"),
            PowerField(
                "title",
                form=True,
                inline=True,
                bulk=True,
                default_list=True,
                tooltip=True,
                column={"help_text": "Book title.", "alignment": "center"},
                link={"view_name": "sample:book-detail", "open_in": "modal"},
            ),
        ]

    view = BookView()

    assert "title" in view.fields, (
        "PowerOverride(list='__all__') should preserve the primitive all-fields list behaviour."
    )
    assert "title" in view.detail_fields, (
        "PowerOverride(detail='__all__') should preserve the primitive all-detail-fields behaviour."
    )
    assert view.form_fields == ["title"], (
        "PowerField(form=True) should become the primitive form_fields list."
    )
    assert view.inline_edit_fields == ["title"], (
        "PowerField(inline=True) should become the primitive inline_edit_fields list."
    )
    assert view.bulk_fields == ["title"], (
        "PowerField(bulk=True) should become the primitive bulk_fields list."
    )
    assert view.default_list_fields == ["title"], (
        "PowerField(default_list=True) should become the primitive default_list_fields list."
    )
    assert view.list_cell_tooltip_fields == ["title"], (
        "PowerField(tooltip=True) should become the primitive tooltip field list."
    )
    assert view.column_help_text == {"title": "Book title."}, (
        "PowerField column help text should become primitive column_help_text."
    )
    assert view.column_alignments == {"title": "center"}, (
        "PowerField column alignment should become primitive column_alignments."
    )
    assert view.link_fields == {
        "title": {"view_name": "sample:book-detail", "open_in": "modal"},
    }, "PowerField link config should become normalized primitive link_fields."


@pytest.mark.django_db
def test_powerfield_absence_does_not_fall_through_to_primitive_defaults():
    class FormOnlyView(CoreMixin):
        model = Book
        power_fields = [PowerField("title", form=True)]

    view = FormOnlyView()

    assert view.fields == [], (
        "PowerField views should not default absent list fields to all model fields."
    )
    assert view.detail_fields == [], (
        "PowerField views should not default absent detail fields from list fields."
    )
    assert view.form_fields == ["title"], (
        "Declared PowerField form fields should still be resolved when list/detail are absent."
    )


def test_powerfield_parent_rejects_primitive_child():
    class PowerFieldBase(CoreMixin):
        model = Book
        power_fields = [PowerField("title", list=True)]

    class BrokenChild(PowerFieldBase):
        fields = ["title"]

    with pytest.raises(ImproperlyConfigured, match="cannot mix power_fields"):
        BrokenChild()


def test_primitive_parent_rejects_powerfield_child():
    class PrimitiveBase(CoreMixin):
        model = Book
        fields = ["title"]

    class BrokenChild(PrimitiveBase):
        power_fields = [PowerField("title", list=True)]

    with pytest.raises(ImproperlyConfigured, match="cannot mix power_fields"):
        BrokenChild()


@pytest.mark.django_db
def test_powerfield_inheritance_allows_same_style_child():
    class PowerFieldBase(CoreMixin):
        model = Book
        power_fields = [PowerField("title", list=True)]

    class ChildView(PowerFieldBase):
        view_title = "Books"

    view = ChildView()

    assert view.fields == ["title"], (
        "A child class should be able to inherit PowerField config when it does not declare primitive Field Intent config."
    )
    assert view.view_title == "Books", (
        "Non-Field-Intent primitive config should remain safe to declare on a PowerField child."
    )


def test_powerfields_resolve_for_class_time_url_gates():
    class PowerFieldUrlView(UrlMixin, View):
        namespace = "sample"
        url_base = "power-book"
        lookup_field = "pk"
        lookup_url_kwarg = "pk"
        path_converter = "int"
        model = Book
        use_htmx = True
        use_modal = True
        power_fields = [
            PowerField("title", inline=True, bulk=True, default_list=True),
        ]

    cfg = resolve_class_config(PowerFieldUrlView)

    assert cfg.inline_edit_fields == ["title"], (
        "Class-time config should expose compiled inline fields before a view instance exists."
    )
    assert cfg.bulk_fields == ["title"], (
        "Class-time config should expose compiled bulk fields before a view instance exists."
    )
    assert cfg.default_list_fields == ["title"], (
        "Class-time config should expose compiled default list fields before a view instance exists."
    )
    assert PowerFieldUrlView.has_inline_editing_urls() is True, (
        "Compiled inline fields should enable inline URL registration."
    )
    assert PowerFieldUrlView.has_list_options_urls() is True, (
        "Compiled default_list_fields should enable list-options URL registration."
    )
