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
        default_list=True,
        form=True,
        inline=True,
        bulk=True,
        label="DDMS Execution Owner",
        tooltip_hook="get_status_tooltip",
    ).to_primitive_fragment()

    assert fragment == {
        "fields": ["status"],
        "default_list_fields": ["status"],
        "form_fields": ["status"],
        "inline_edit_fields": ["status"],
        "bulk_fields": ["status"],
        "field_labels": {"status": "DDMS Execution Owner"},
        "list_cell_tooltip_fields": {"status": "get_status_tooltip"},
    }, "PowerField should expose list-style primitive contributions for one field."


def test_powerfield_extracts_lazy_tooltip_primitive_fragment():
    fragment = PowerField(
        "status",
        default_list=True,
        tooltip_hook="get_status_tooltip",
        tooltip_mode="lazy",
    ).to_primitive_fragment()

    assert fragment == {
        "fields": ["status"],
        "default_list_fields": ["status"],
        "list_cell_tooltip_fields": {
            "status": {"hook": "get_status_tooltip", "mode": "lazy"}
        },
    }, "PowerField tooltip_mode='lazy' should compile to the rich primitive tooltip config."


def test_powerfield_default_list_adds_property_to_list_allow_list():
    fragment = PowerField(
        "status_label",
        property=True,
        default_list=True,
    ).to_primitive_fragment()

    assert fragment == {
        "properties": ["status_label"],
        "default_list_fields": ["status_label"],
    }, (
        "A property-backed PowerField default list column should become both an "
        "allowed list property and a default visible column."
    )


def test_powerfield_extracts_mapping_primitive_fragment():
    fragment = PowerField(
        "status",
        list=True,
        column={"help_text": "Current status.", "alignment": "center"},
        queryset_dependencies={"static_filters": {"is_active": True}},
        link={"view_name": "workflow:status-detail", "open_in": "modal"},
    ).to_primitive_fragment()

    assert fragment == {
        "fields": ["status"],
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


@pytest.mark.parametrize("flag_name", ["form", "default_list", "property"])
def test_powerfield_rejects_non_boolean_flags(flag_name):
    with pytest.raises(ValueError, match=f"PowerField.{flag_name}"):
        PowerField("status", **{flag_name: 1})


def test_powerfield_rejects_bad_exclude_shape():
    with pytest.raises(ValueError, match="exclude must be a dictionary"):
        PowerField("status", exclude=["list"])

    with pytest.raises(ValueError, match="unknown exclude dimensions"):
        PowerField("status", exclude={"default_list": True})

    with pytest.raises(ValueError, match="exclude values must be True or False"):
        PowerField("status", exclude={"list": "yes"})


def test_powerfield_rejects_bad_mapping_shapes():
    with pytest.raises(ValueError, match="PowerField.column must be a dictionary"):
        PowerField("status", list=True, column="Current status.")

    with pytest.raises(ValueError, match="PowerField.link must be a dictionary"):
        PowerField("status", list=True, link="workflow:status-detail")

    with pytest.raises(
        ValueError, match="PowerField.queryset_dependencies must be a dictionary"
    ):
        PowerField("status", queryset_dependencies="active-only")


def test_powerfield_rejects_bad_column_options():
    with pytest.raises(ValueError, match="unknown options"):
        PowerField("status", list=True, column={"tooltip": "Current status."})

    with pytest.raises(ValueError, match="alignment must be"):
        PowerField("status", list=True, column={"alignment": "middle"})


def test_powerfield_rejects_blank_label():
    with pytest.raises(ValueError, match="PowerField.label"):
        PowerField("status", label="   ")


@pytest.mark.parametrize(
    "changes",
    [
        {"tooltip_hook": "get_status_tooltip"},
        {"column": {"help_text": "Current status."}},
        {"link": {"view_name": "workflow:status-detail"}},
    ],
)
def test_powerfield_rejects_list_cell_metadata_without_list_visibility(changes):
    with pytest.raises(ValueError, match="list-cell metadata requires"):
        PowerField("status", **changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"list": True, "property": True},
        {"detail": True, "detail_property": True},
        {"form": True, "form_display": True},
    ],
)
def test_powerfield_rejects_logical_dimension_clashes(changes):
    with pytest.raises(ValueError, match="cannot combine"):
        PowerField("status", **changes)


def test_powerfield_rejects_default_list_with_list_exclusion():
    with pytest.raises(ValueError, match="default_list=True"):
        PowerField("status", default_list=True, exclude={"list": True})


@pytest.mark.parametrize("tooltip_hook", ["", "   ", 1])
def test_powerfield_rejects_invalid_tooltip_hook(tooltip_hook):
    with pytest.raises(ValueError, match="tooltip_hook"):
        PowerField("status", default_list=True, tooltip_hook=tooltip_hook)


@pytest.mark.parametrize("tooltip_mode", ["", "   ", "deferred", 1])
def test_powerfield_rejects_invalid_tooltip_mode(tooltip_mode):
    with pytest.raises(ValueError, match="tooltip_mode"):
        PowerField(
            "status",
            default_list=True,
            tooltip_hook="get_status_tooltip",
            tooltip_mode=tooltip_mode,
        )


def test_powerfield_rejects_tooltip_mode_without_tooltip_hook():
    with pytest.raises(ValueError, match="tooltip_mode requires tooltip_hook"):
        PowerField("status", default_list=True, tooltip_mode="lazy")


def test_powerfield_rejects_removed_tooltip_kwarg():
    with pytest.raises(TypeError, match="unexpected keyword"):
        PowerField("status", default_list=True, tooltip=True)


def test_powerfield_with_options_returns_changed_copy_without_mutating_original():
    original = PowerField(
        "status",
        default_list=True,
        tooltip_hook="get_status_tooltip",
        bulk=True,
    )

    copied = original.with_options(bulk=False, tooltip_hook="get_status_summary")

    assert copied is not original, "with_options should return a new PowerField."
    assert original.bulk is True, "with_options should not mutate the source field."
    assert original.tooltip_hook == "get_status_tooltip", (
        "with_options should not mutate the source tooltip hook."
    )
    assert copied.bulk is False, "with_options should apply the requested change."
    assert copied.tooltip_hook == "get_status_summary", (
        "with_options should apply the requested tooltip hook change."
    )
    assert copied.to_primitive_fragment() == {
        "fields": ["status"],
        "default_list_fields": ["status"],
        "list_cell_tooltip_fields": {"status": "get_status_summary"},
    }, "The copied PowerField should compile with the changed options."


def test_powerfield_with_options_can_set_lazy_tooltip_mode():
    original = PowerField(
        "status",
        default_list=True,
        tooltip_hook="get_status_tooltip",
    )

    copied = original.with_options(tooltip_mode="lazy")

    assert copied.to_primitive_fragment()["list_cell_tooltip_fields"] == {
        "status": {"hook": "get_status_tooltip", "mode": "lazy"}
    }, "with_options should support opting an existing tooltip hook into lazy mode."


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
                label="DDMS Execution Owner",
                tooltip_hook="get_title_tooltip",
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
    assert view.field_labels == {"title": "DDMS Execution Owner"}, (
        "PowerField(label=...) should become the primitive field_labels map."
    )
    assert view.list_cell_tooltip_fields == {"title": "get_title_tooltip"}, (
        "PowerField(tooltip_hook=...) should become the primitive tooltip hook map."
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
