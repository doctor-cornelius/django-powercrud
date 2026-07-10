from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


BOOLEAN_DIMENSIONS = (
    "inline",
    "bulk",
    "form",
    "form_display",
    "form_disabled",
    "detail",
    "list",
    "default_list",
    "property",
    "detail_property",
)

LIST_DIMENSIONS = {
    "bulk": "bulk_fields",
    "default_list": "default_list_fields",
    "detail": "detail_fields",
    "detail_property": "detail_properties",
    "form": "form_fields",
    "form_disabled": "form_disabled_fields",
    "form_display": "form_display_fields",
    "inline": "inline_edit_fields",
    "list": "fields",
    "property": "properties",
}

OVERRIDE_DIMENSIONS = {
    "bulk": "bulk_fields",
    "detail": "detail_fields",
    "form": "form_fields",
    "list": "fields",
}

EXCLUDE_DIMENSIONS = {
    "detail": "detail_exclude",
    "detail_property": "detail_properties_exclude",
    "form": "form_fields_exclude",
    "list": "exclude",
    "property": "properties_exclude",
}

LIST_CELL_METADATA_OPTIONS = ("tooltip_hook", "tooltip_mode", "column", "link")

TOOLTIP_MODES = {"eager", "lazy"}

COLUMN_OPTIONS = {"help_text", "alignment", "value_format"}

COLUMN_ALIGNMENTS = {"left", "center", "right"}


@dataclass(frozen=True)
class PowerOverride:
    """View-level defaults for future PowerField compilation."""

    list: str | None = None
    detail: str | None = None
    form: str | None = None
    bulk: str | None = None

    def to_primitive_fragment(self) -> dict[str, Any]:
        """Return override sentinel values as primitive PowerCRUD config."""
        fragment: dict[str, Any] = {}
        for dimension, primitive_name in OVERRIDE_DIMENSIONS.items():
            value = getattr(self, dimension)
            if value is not None:
                fragment[primitive_name] = value
        return fragment


@dataclass(frozen=True)
class PowerField:
    """Field-level declaration that can be compiled to primitive config."""

    name: str
    inline: bool = False
    bulk: bool = False
    form: bool = False
    form_display: bool = False
    form_disabled: bool = False
    tooltip_hook: str | None = None
    tooltip_mode: str | None = None
    detail: bool = False
    list: bool = False
    default_list: bool = False
    property: bool = False
    detail_property: bool = False
    label: str | None = None
    column: dict[str, str] | None = None
    queryset_dependencies: dict[str, Any] | None = None
    link: dict[str, Any] | None = None
    exclude: dict[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate the declaration shape without touching Django model metadata."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("PowerField name must be a non-empty string")

        for dimension in BOOLEAN_DIMENSIONS:
            if not isinstance(getattr(self, dimension), bool):
                raise ValueError(f"PowerField.{dimension} must be True or False")

        if not isinstance(self.exclude, dict):
            raise ValueError("PowerField.exclude must be a dictionary")

        unknown_exclude_dimensions = [
            dimension for dimension in self.exclude if dimension not in EXCLUDE_DIMENSIONS
        ]
        if unknown_exclude_dimensions:
            raise ValueError(
                "PowerField "
                f"{self.name!r} has unknown exclude dimensions: "
                f"{', '.join(sorted(unknown_exclude_dimensions))}"
            )

        non_bool_exclude_dimensions = [
            dimension
            for dimension, excluded in self.exclude.items()
            if not isinstance(excluded, bool)
        ]
        if non_bool_exclude_dimensions:
            raise ValueError(
                "PowerField "
                f"{self.name!r} exclude values must be True or False for "
                f"{', '.join(sorted(non_bool_exclude_dimensions))}"
            )

        if self.tooltip_hook is not None:
            if not isinstance(self.tooltip_hook, str) or not self.tooltip_hook.strip():
                raise ValueError("PowerField.tooltip_hook must be a non-empty string")
            object.__setattr__(self, "tooltip_hook", self.tooltip_hook.strip())

        if self.tooltip_mode is not None:
            if not isinstance(self.tooltip_mode, str) or not self.tooltip_mode.strip():
                raise ValueError("PowerField.tooltip_mode must be 'eager' or 'lazy'")
            tooltip_mode = self.tooltip_mode.strip()
            if tooltip_mode not in TOOLTIP_MODES:
                raise ValueError("PowerField.tooltip_mode must be 'eager' or 'lazy'")
            if not self.tooltip_hook:
                raise ValueError("PowerField.tooltip_mode requires tooltip_hook")
            object.__setattr__(self, "tooltip_mode", tooltip_mode)

        if self.label is not None:
            if not isinstance(self.label, str) or not self.label.strip():
                raise ValueError("PowerField.label must be a non-empty string")
            object.__setattr__(self, "label", self.label.strip())

        for option_name in ("column", "queryset_dependencies", "link"):
            value = getattr(self, option_name)
            if value is not None and not isinstance(value, dict):
                raise ValueError(f"PowerField.{option_name} must be a dictionary")

        if self.column:
            unknown_column_options = [
                option for option in self.column if option not in COLUMN_OPTIONS
            ]
            if unknown_column_options:
                raise ValueError(
                    "PowerField.column supports only help_text, alignment, and value_format; "
                    f"unknown options: {', '.join(sorted(unknown_column_options))}"
                )
            alignment = self.column.get("alignment")
            if alignment is not None and alignment not in COLUMN_ALIGNMENTS:
                raise ValueError(
                    "PowerField.column alignment must be 'left', 'center', or 'right'"
                )
            value_format = self.column.get("value_format")
            if value_format is not None and value_format not in {
                "date",
                "time",
                "datetime",
            }:
                raise ValueError(
                    "PowerField.column value_format must be 'date', 'time', or 'datetime'"
                )

        conflicting_dimensions = [
            dimension
            for dimension in EXCLUDE_DIMENSIONS
            if getattr(self, dimension) and self.exclude.get(dimension)
        ]
        if conflicting_dimensions:
            raise ValueError(
                "PowerField "
                f"{self.name!r} declares both include and exclude for "
                f"{', '.join(sorted(conflicting_dimensions))}"
            )

        if self.property and self.list:
            raise ValueError("PowerField cannot combine property=True with list=True")

        if self.detail_property and self.detail:
            raise ValueError(
                "PowerField cannot combine detail_property=True with detail=True"
            )

        if self.form and self.form_display:
            raise ValueError("PowerField cannot combine form=True with form_display=True")

        if self.default_list and (
            self.exclude.get("list") or self.exclude.get("property")
        ):
            raise ValueError(
                "PowerField cannot combine default_list=True with list or property exclusion"
            )

        uses_list_cell_metadata = any(
            bool(getattr(self, option_name))
            for option_name in LIST_CELL_METADATA_OPTIONS
        )
        has_list_visibility = self.list or self.property or self.default_list
        if uses_list_cell_metadata and not has_list_visibility:
            raise ValueError(
                "PowerField list-cell metadata requires list=True, property=True, "
                "or default_list=True"
            )

    def with_options(self, **changes: Any) -> "PowerField":
        """Return a copy of this PowerField with selected options changed."""
        return replace(self, **changes)

    def to_primitive_fragment(self) -> dict[str, Any]:
        """Return this field's contribution to primitive PowerCRUD config."""
        fragment: dict[str, Any] = {}

        def append_unique(primitive_name: str) -> None:
            values = fragment.setdefault(primitive_name, [])
            if self.name not in values:
                values.append(self.name)

        for dimension, primitive_name in LIST_DIMENSIONS.items():
            if dimension == "default_list":
                continue
            if getattr(self, dimension) and not self.exclude.get(dimension):
                append_unique(primitive_name)

        if self.default_list:
            append_unique("default_list_fields")
            if self.property:
                append_unique("properties")
            else:
                append_unique("fields")

        if self.column:
            help_text = self.column.get("help_text")
            if help_text is not None:
                fragment.setdefault("column_help_text", {})[self.name] = help_text

            alignment = self.column.get("alignment")
            if alignment is not None:
                fragment.setdefault("column_alignments", {})[self.name] = alignment

            value_format = self.column.get("value_format")
            if value_format is not None:
                fragment.setdefault("column_value_formats", {})[
                    self.name
                ] = value_format

        if self.label is not None:
            fragment.setdefault("field_labels", {})[self.name] = self.label

        if self.queryset_dependencies:
            fragment.setdefault("field_queryset_dependencies", {})[self.name] = dict(
                self.queryset_dependencies
            )

        if self.tooltip_hook:
            tooltip_config: str | dict[str, str]
            if self.tooltip_mode is None:
                tooltip_config = self.tooltip_hook
            else:
                tooltip_config = {"hook": self.tooltip_hook, "mode": self.tooltip_mode}
            fragment.setdefault("list_cell_tooltip_fields", {})[
                self.name
            ] = tooltip_config

        if self.link:
            fragment.setdefault("link_fields", {})[self.name] = dict(self.link)

        return fragment


def merge_powerfield_fragments(power_fields: list[PowerField]) -> dict[str, Any]:
    """Merge PowerField primitive fragments into one primitive config fragment."""
    merged: dict[str, Any] = {}
    for power_field in power_fields:
        fragment = power_field.to_primitive_fragment()
        for primitive_name, value in fragment.items():
            if isinstance(value, list):
                existing = merged.setdefault(primitive_name, [])
                existing.extend(value)
                merged[primitive_name] = list(dict.fromkeys(existing))
            elif isinstance(value, dict):
                merged.setdefault(primitive_name, {}).update(value)

    return merged


def compile_powerfields(
    declarations: list[PowerField | PowerOverride],
) -> dict[str, Any]:
    """Compile PowerField declarations into primitive PowerCRUD config."""
    if not declarations:
        return {}
    if not isinstance(declarations, (list, tuple)):
        raise ValueError("power_fields must be a list of PowerField declarations")

    overrides = [
        declaration
        for declaration in declarations
        if isinstance(declaration, PowerOverride)
    ]
    unsupported_entries = [
        index
        for index, declaration in enumerate(declarations)
        if not isinstance(declaration, (PowerField, PowerOverride))
    ]
    if unsupported_entries:
        positions = ", ".join(str(index) for index in unsupported_entries)
        raise ValueError(
            "power_fields entries must be PowerField or PowerOverride instances; "
            f"invalid entries at positions: {positions}"
        )
    if len(overrides) > 1:
        raise ValueError("power_fields can include at most one PowerOverride")
    if overrides and not isinstance(declarations[0], PowerOverride):
        raise ValueError("PowerOverride must be the first power_fields entry")

    merged: dict[str, Any] = {}
    active_override_dimensions: set[str] = set()
    field_declarations: list[PowerField] = []

    first_declaration = declarations[0]
    if isinstance(first_declaration, PowerOverride):
        merged.update(first_declaration.to_primitive_fragment())
        active_override_dimensions = {
            dimension
            for dimension in OVERRIDE_DIMENSIONS
            if getattr(first_declaration, dimension) is not None
        }
        field_declarations = [
            declaration
            for declaration in declarations[1:]
            if isinstance(declaration, PowerField)
        ]
    else:
        field_declarations = [
            declaration
            for declaration in declarations
            if isinstance(declaration, PowerField)
        ]

    for power_field in field_declarations:
        field_fragment = power_field.to_primitive_fragment()
        for primitive_name, value in field_fragment.items():
            if isinstance(value, list):
                existing = merged.get(primitive_name)
                if existing is None:
                    merged[primitive_name] = list(dict.fromkeys(value))
                elif isinstance(existing, list):
                    existing.extend(value)
                    merged[primitive_name] = list(dict.fromkeys(existing))
            elif isinstance(value, dict):
                merged.setdefault(primitive_name, {}).update(value)

        for dimension in active_override_dimensions:
            exclude_name = EXCLUDE_DIMENSIONS.get(dimension)
            if exclude_name and power_field.exclude.get(dimension):
                existing = merged.setdefault(exclude_name, [])
                existing.append(power_field.name)
                merged[exclude_name] = list(dict.fromkeys(existing))

    return merged


__all__ = [
    "PowerField",
    "PowerOverride",
    "compile_powerfields",
    "merge_powerfield_fragments",
]
