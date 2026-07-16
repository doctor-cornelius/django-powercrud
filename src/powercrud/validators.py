from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Union, Optional, List, Literal, Dict, Any, Callable
import re

from powercrud.modal_presentation import normalize_modal_presentation


DEFAULT_PAGINATE_BY = 25

VIEW_HELP_COLOR_NAMES = {
    "base",
    "primary",
    "secondary",
    "accent",
    "neutral",
    "info",
    "success",
    "warning",
    "error",
}
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")
CSS_SIZE_RE = re.compile(r"^\d+(\.\d+)?(px|rem|em|ch|%)$")


def validate_view_help_color(value: str, field_name: str) -> str:
    """Return a normalized view-help color token or raise ValueError."""
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = normalized.lower()
    if lowered in VIEW_HELP_COLOR_NAMES:
        return lowered
    if HEX_COLOR_RE.match(normalized):
        return lowered
    raise ValueError(
        f"{field_name} must be a daisyUI semantic color or hex color"
    )


def validate_view_help_min_width(value: str, field_name: str) -> str:
    """Return a normalized safe CSS size token or raise ValueError."""
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    if not CSS_SIZE_RE.match(normalized):
        raise ValueError(
            f"{field_name} must be a CSS size using px, rem, em, ch, or %"
        )
    return normalized


class PowerCRUDMixinValidator(BaseModel):
    """Validation model for PowerCRUDMixin settings"""

    model_config = ConfigDict(validate_assignment=True)
    # namespace settings
    namespace: Optional[str] = None

    # template parameters
    templates_path: Optional[str] = None
    base_template_path: Optional[str] = None
    view_title: Optional[str] = None
    view_instructions: Optional[str] = None
    view_help: Optional[Dict[str, Any]] = None
    view_help_default_color: Optional[str] = "base"
    view_help_min_width: Optional[str] = "40rem"
    column_help_text: Optional[Dict[str, str]] = None
    field_labels: Optional[Dict[str, str]] = None
    column_alignments: Optional[Dict[str, Literal["left", "center", "right"]]] = None
    column_value_formats: Optional[
        Dict[str, Literal["date", "time", "datetime"]]
    ] = None
    default_datetime_value_format: Literal["date", "time", "datetime"] = "date"
    list_cell_tooltip_fields: Optional[Union[List[str], Dict[str, Any]]] = None
    list_cell_link_default_open_in: Optional[Literal["current", "new", "modal"]] = "new"
    link_fields: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None
    column_sort_fields_override: Optional[Dict[str, str]] = None

    # forms
    use_crispy: Optional[bool] = None
    searchable_selects: Optional[bool] = True

    # field and property inclusion scope
    fields: Optional[Union[List[str], Literal["__all__"]]] = None
    properties: Optional[Union[List[str], Literal["__all__"]]] = None
    exclude: Optional[List[str]] = None
    properties_exclude: Optional[List[str]] = None
    list_options_enabled: Optional[bool] = None
    default_list_fields: Optional[List[str]] = None

    # Detail view settings
    detail_fields: Optional[Union[List[str], Literal["__all__", "__fields__"]]] = None
    detail_exclude: Optional[List[str]] = None
    detail_properties: Optional[
        Union[List[str], Literal["__all__", "__properties__"]]
    ] = None
    detail_properties_exclude: Optional[List[str]] = None

    # htmx
    use_htmx: Optional[bool] = None
    default_htmx_target: Optional[str] = None
    hx_trigger: Optional[Union[str, int, float, dict]] = None

    # inline editing
    inline_edit_fields: Optional[Union[List[str], Literal["__all__", "__fields__"]]] = (
        None
    )
    field_queryset_dependencies: Optional[Dict[str, Dict[str, Any]]] = None
    inline_edit_requires_perm: Optional[str] = None
    inline_edit_allowed: Optional[Callable] = None
    inline_edit_always_visible: Optional[bool] = True
    inline_edit_highlight_accent: Optional[str] = "#14b8a6"
    inline_save_refresh_policy: Optional[
        Literal["reset_if_filtered_out", "keep_page", "reset_page"]
    ] = "reset_if_filtered_out"

    # modals
    use_modal: Optional[bool] = None
    modal_id: Optional[str] = None
    modal_target: Optional[str] = None
    modal_classes: Optional[str] = None
    modal_box_classes: Optional[str] = None
    modal_body_classes: Optional[str] = None
    bulk_modal_box_classes: Optional[str] = None
    modal_presentation: Optional[Dict[str, Any]] = None
    bulk_modal_presentation: Optional[Dict[str, Any]] = None

    # table display parameters
    table_pixel_height_other_page_elements: Optional[Union[int, float]] = Field(
        default=None, ge=0
    )
    table_max_height: Optional[int] = Field(default=None, ge=0, le=100)
    table_max_col_width: Optional[int] = Field(default=None, gt=0)
    table_header_min_wrap_width: Optional[int] = Field(default=None, gt=0)
    table_classes: Optional[str] = None
    action_button_classes: Optional[str] = None
    extra_button_classes: Optional[str] = None
    extra_buttons_mode: Optional[Literal["buttons", "dropdown"]] = None
    extra_actions_mode: Optional[Literal["buttons", "dropdown"]] = None
    extra_actions_dropdown_open_upward_bottom_rows: Optional[int] = Field(
        default=None, ge=0
    )
    show_record_count: Optional[bool] = None
    show_bulk_selection_meta: Optional[bool] = None
    extra_button_selection_controls_disabled: Optional[bool] = False

    # form fields
    form_fields: Optional[Union[List[str], Literal["__all__", "__fields__"]]] = None
    form_fields_exclude: Optional[List[str]] = None
    form_display_fields: Optional[List[str]] = None
    form_disabled_fields: Optional[List[str]] = None

    # advanced configuration
    bulk_fields: Optional[List[str]] = None
    bulk_delete: Optional[bool] = None
    bulk_full_clean: Optional[bool] = None
    bulk_async: Optional[bool] = None
    bulk_async_conflict_checking: Optional[bool] = None
    bulk_min_async_records: Optional[int] = None
    bulk_async_backend: Optional[str] = None
    bulk_async_notification: Optional[str] = None
    bulk_async_allow_anonymous: Optional[bool] = None
    bulk_update_persistence_backend_path: Optional[str] = None
    bulk_update_persistence_backend_config: Optional[Dict[str, Any]] = None
    dropdown_sort_options: Optional[Dict[str, str]] = None
    default_filterset_fields: Optional[List[str]] = None
    filter_null_fields_exclude: Optional[List[str]] = None
    m2m_filter_and_logic: Optional[bool] = None
    inline_preserve_required_fields: Optional[bool] = None
    async_manager_class: Optional[Any] = None
    async_manager_class_path: Optional[str] = None
    async_manager_config: Optional[Dict[str, Any]] = None
    paginate_by: Optional[int] = DEFAULT_PAGINATE_BY
    page_size_options: Optional[List[int]] = None
    page_size_all_enabled: Optional[bool] = True

    @field_validator("fields", "properties", "detail_fields", "detail_properties")
    @classmethod
    def validate_field_specs(cls, v):
        if v is None:
            return v
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("List must contain only strings")
        return v

    @field_validator("default_list_fields")
    @classmethod
    def validate_default_list_fields(cls, v):
        """Validate the opt-in default visible list-column declaration."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("default_list_fields must be a list of strings")
        if not v:
            raise ValueError("default_list_fields cannot be empty")
        for value in v:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("default_list_fields must contain non-empty strings")
        return [value.strip() for value in v]

    @field_validator("page_size_options", mode="before")
    @classmethod
    def validate_page_size_options(cls, v):
        """Validate explicit page-size selector choices."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("page_size_options must be a list of positive integers")
        if not v:
            raise ValueError("page_size_options cannot be empty")
        if not all(type(value) is int and value > 0 for value in v):
            raise ValueError("page_size_options must contain only positive integers")
        return sorted(set(v))

    @model_validator(mode="after")
    def validate_page_size_defaults(self):
        """Ensure page-size controls always leave a valid default state."""
        if self.page_size_options is not None and self.paginate_by is not None:
            if self.paginate_by not in self.page_size_options:
                raise ValueError(
                    "paginate_by must be included in explicit page_size_options"
                )
        if self.paginate_by is None and self.page_size_all_enabled is False:
            raise ValueError(
                "page_size_all_enabled cannot be False when paginate_by is None"
            )
        return self

    @field_validator("hx_trigger")
    @classmethod
    def validate_hx_trigger(cls, v):
        if v is None:
            return v
        if isinstance(v, dict):
            if not all(isinstance(k, str) for k in v.keys()):
                raise ValueError("HX-Trigger dict keys must be strings")
        return v

    @field_validator("default_htmx_target")
    @classmethod
    def validate_default_htmx_target(cls, v, info):
        if info.data.get("use_htmx") is True and v is None:
            raise ValueError("default_htmx_target is required when use_htmx is True")
        return v

    @field_validator("base_template_path")
    @classmethod
    def validate_base_template_path(cls, v):
        """
        base_template_path should point at the project’s actual base template.
        We allow None in low-level or test harnesses, but reject empty strings.
        """
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(
                "base_template_path must be a non-empty string when provided"
            )
        return v

    @field_validator("view_title")
    @classmethod
    def validate_view_title(cls, v):
        """Ensure the optional list heading override is non-empty when set."""
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError("view_title must be a non-empty string when provided")
        return v

    @field_validator("view_instructions")
    @classmethod
    def validate_view_instructions(cls, v):
        """Ensure the optional list helper text is non-empty when set."""
        if v is None:
            return v
        if isinstance(v, str) and not v.strip():
            raise ValueError(
                "view_instructions must be a non-empty string when provided"
            )
        return v

    @field_validator("view_help")
    @classmethod
    def validate_view_help(cls, v):
        """Validate optional collapsed screen-help configuration."""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("view_help must be a dict when provided")

        allowed_keys = {"summary", "details", "default_open", "color", "min_width"}
        unknown_keys = set(v.keys()) - allowed_keys
        if unknown_keys:
            raise ValueError(
                "view_help only supports summary, details, default_open, color, and min_width"
            )

        summary = v.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("view_help summary must be a non-empty string")

        details = v.get("details")
        if not isinstance(details, str) or not details.strip():
            raise ValueError("view_help details must be a non-empty string")

        default_open = v.get("default_open", False)
        if not isinstance(default_open, bool):
            raise ValueError("view_help default_open must be a boolean")

        normalized = {
            "summary": summary.strip(),
            "details": details.strip(),
            "default_open": default_open,
        }
        if "color" in v:
            color = v.get("color")
            if not isinstance(color, str):
                raise ValueError("view_help color must be a string")
            normalized["color"] = validate_view_help_color(color, "view_help color")
        if "min_width" in v:
            min_width = v.get("min_width")
            if not isinstance(min_width, str):
                raise ValueError("view_help min_width must be a string")
            normalized["min_width"] = validate_view_help_min_width(
                min_width,
                "view_help min_width",
            )
        return normalized

    @field_validator("view_help_default_color")
    @classmethod
    def validate_view_help_default_color(cls, v):
        """Validate the default collapsed screen-help color."""
        if v is None:
            return "base"
        if not isinstance(v, str):
            raise ValueError("view_help_default_color must be a string")
        return validate_view_help_color(v, "view_help_default_color")

    @field_validator("view_help_min_width")
    @classmethod
    def validate_view_help_min_width(cls, v):
        """Validate the default collapsed screen-help minimum width."""
        if v is None:
            return "40rem"
        if not isinstance(v, str):
            raise ValueError("view_help_min_width must be a string")
        return validate_view_help_min_width(v, "view_help_min_width")

    @field_validator("modal_presentation", "bulk_modal_presentation")
    @classmethod
    def validate_modal_presentation(cls, value, info):
        """Validate a partial portable modal-presentation mapping."""
        return normalize_modal_presentation(value, info.field_name)

    @field_validator(
        "column_help_text",
        "field_labels",
        "column_sort_fields_override",
        "column_alignments",
        "column_value_formats",
    )
    @classmethod
    def validate_string_mapping(cls, v, info):
        """Ensure optional mapping-style config values are string-to-string."""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError(f"{info.field_name} must be a dict when provided")
        for key, value in v.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(
                    f"{info.field_name} keys must be non-empty strings"
                )
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{info.field_name} values must be non-empty strings"
                )
            if info.field_name == "column_alignments":
                normalized = value.strip().lower()
                if normalized not in {"left", "center", "right"}:
                    raise ValueError(
                        "column_alignments values must be 'left', 'center', or 'right'"
                    )
                v[key.strip()] = normalized
                continue
            v[key.strip()] = value.strip()
        return v

    @field_validator("link_fields")
    @classmethod
    def validate_link_fields(cls, v):
        """Ensure link_fields stays on the narrow public declarative contract."""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("link_fields must be a dict when provided")

        normalized: Dict[str, Dict[str, str]] = {}
        for key, value in v.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("link_fields keys must be non-empty strings")

            field_name = key.strip()
            if isinstance(value, str):
                view_name = value.strip()
                if not view_name:
                    raise ValueError(
                        "link_fields string values must be non-empty view names"
                    )
                normalized[field_name] = {"view_name": view_name}
                continue

            if not isinstance(value, dict):
                raise ValueError(
                    "link_fields values must be either a view-name string or a dict"
                )

            unsupported_keys = set(value.keys()) - {
                "view_name",
                "url",
                "pk_attr",
                "open_in",
                "modal_box_classes",
                "modal_presentation",
            }
            if unsupported_keys:
                raise ValueError(
                    "link_fields dict values only support one of 'view_name' or "
                    "'url', plus optional 'pk_attr', 'open_in', and "
                    "'modal_box_classes', or 'modal_presentation'. Unsupported keys: "
                    f"{', '.join(sorted(unsupported_keys))}"
                )

            view_name = value.get("view_name")
            url = value.get("url")
            has_view_name = isinstance(view_name, str) and bool(view_name.strip())
            has_url = isinstance(url, str) and bool(url.strip())
            if has_view_name == has_url:
                raise ValueError(
                    "link_fields dict values must include exactly one non-empty "
                    "'view_name' or 'url'"
                )

            normalized_value = {}
            if has_view_name:
                normalized_value["view_name"] = view_name.strip()
            if has_url:
                normalized_value["url"] = url.strip()

            pk_attr = value.get("pk_attr")
            if pk_attr is not None:
                if not has_view_name:
                    raise ValueError(
                        "link_fields.pk_attr is only supported with view_name links"
                    )
                if not isinstance(pk_attr, str) or not pk_attr.strip():
                    raise ValueError(
                        "link_fields.pk_attr must be a non-empty string when provided"
                    )
                normalized_value["pk_attr"] = pk_attr.strip()

            open_in = value.get("open_in")
            if open_in is not None:
                if not isinstance(open_in, str) or open_in.strip() not in {
                    "current",
                    "new",
                    "modal",
                }:
                    raise ValueError(
                        "link_fields.open_in must be 'current', 'new', or 'modal'"
                    )
                normalized_value["open_in"] = open_in.strip()

            modal_box_classes = value.get("modal_box_classes")
            modal_presentation = value.get("modal_presentation")
            if modal_box_classes is not None and modal_presentation is not None:
                raise ValueError(
                    "link_fields cannot combine modal_box_classes with modal_presentation"
                )
            if modal_box_classes is not None:
                if normalized_value.get("open_in") not in {None, "modal"}:
                    raise ValueError(
                        "link_fields.modal_box_classes is only supported when "
                        "open_in is 'modal'"
                    )
                if (
                    not isinstance(modal_box_classes, str)
                    or not modal_box_classes.strip()
                ):
                    raise ValueError(
                        "link_fields.modal_box_classes must be a non-empty string "
                        "when provided"
                    )
                normalized_value["modal_box_classes"] = modal_box_classes.strip()
            if modal_presentation is not None:
                if normalized_value.get("open_in") not in {None, "modal"}:
                    raise ValueError(
                        "link_fields.modal_presentation is only supported when "
                        "open_in is 'modal'"
                    )
                normalized_value["modal_presentation"] = normalize_modal_presentation(
                    modal_presentation,
                    "link_fields.modal_presentation",
                    allow_none=False,
                )

            normalized[field_name] = normalized_value

        return normalized

    @field_validator("form_fields")
    @classmethod
    def validate_form_fields(cls, v):
        if v is None:
            return v
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("form_fields must contain only strings")
        return v

    @field_validator("inline_edit_fields")
    @classmethod
    def validate_inline_edit_fields(cls, v):
        if v is None:
            return v
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("inline_edit_fields must contain only strings")
        return v

    @field_validator("list_cell_tooltip_fields", mode="before")
    @classmethod
    def validate_list_cell_tooltip_fields(cls, v):
        """Require tooltip declarations to use legacy, eager, or rich map shape."""
        if v is None:
            return v
        if isinstance(v, list):
            for value in v:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        "list_cell_tooltip_fields legacy list form must contain "
                        "only non-empty strings"
                    )
            return v
        if isinstance(v, dict):
            for field_name, config in v.items():
                if not isinstance(field_name, str) or not field_name.strip():
                    raise ValueError(
                        "list_cell_tooltip_fields dict keys must be non-empty strings"
                    )

                if isinstance(config, str):
                    if not config.strip():
                        raise ValueError(
                            "list_cell_tooltip_fields dict values must be "
                            "non-empty strings"
                        )
                    continue

                if not isinstance(config, dict):
                    raise ValueError(
                        "list_cell_tooltip_fields dict values must be non-empty "
                        "strings or tooltip config dictionaries"
                    )

                unknown_keys = set(config) - {"hook", "mode"}
                if unknown_keys:
                    raise ValueError(
                        "list_cell_tooltip_fields tooltip config supports only "
                        f"hook and mode; unknown keys: {', '.join(sorted(unknown_keys))}"
                    )

                hook_name = config.get("hook")
                if not isinstance(hook_name, str) or not hook_name.strip():
                    raise ValueError(
                        "list_cell_tooltip_fields tooltip config hook must be a "
                        "non-empty string"
                    )

                mode = config.get("mode", "eager")
                if not isinstance(mode, str) or not mode.strip():
                    raise ValueError(
                        "list_cell_tooltip_fields tooltip config mode must be "
                        "'eager' or 'lazy'"
                    )
                if mode.strip() not in {"eager", "lazy"}:
                    raise ValueError(
                        "list_cell_tooltip_fields tooltip config mode must be "
                        "'eager' or 'lazy'"
                    )
            return v
        raise ValueError(
            "list_cell_tooltip_fields must be either a dict of field names to "
            "hook names/config dictionaries or a deprecated list of field names"
        )

    @field_validator("inline_edit_highlight_accent")
    @classmethod
    def validate_inline_edit_highlight_accent(cls, v):
        """Require a hex color string for the inline-edit highlight accent."""
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError(
                "inline_edit_highlight_accent must be a hex color string"
            )
        value = v.strip()
        if not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", value):
            raise ValueError(
                "inline_edit_highlight_accent must be a hex color like '#14b8a6' or '#1ba'"
            )
        return value.lower()

    @field_validator("field_queryset_dependencies")
    @classmethod
    def validate_field_queryset_dependencies(cls, v):
        """Ensure field queryset dependencies use a string->dict mapping."""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("field_queryset_dependencies must be a dictionary")
        for field_name, config in v.items():
            if not isinstance(field_name, str):
                raise ValueError("field_queryset_dependencies keys must be strings")
            if not isinstance(config, dict):
                raise ValueError(
                    "field_queryset_dependencies values must be dictionaries"
                )
        return v

    @field_validator("form_fields_exclude")
    @classmethod
    def validate_form_fields_exclude(cls, v):
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError("form_fields_exclude must contain only strings")
        return v

    @field_validator("form_display_fields", "form_disabled_fields")
    @classmethod
    def validate_form_field_name_lists(cls, v, info):
        """Ensure auxiliary form field lists contain only strings."""
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError(f"{info.field_name} must contain only strings")
        return v

    @field_validator("bulk_fields")
    @classmethod
    def validate_bulk_fields(cls, v):
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError("bulk_fields must contain only strings")
        return v

    @field_validator("dropdown_sort_options")
    @classmethod
    def validate_dropdown_sort_options(cls, v):
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("dropdown_sort_options must be a dictionary")
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    "dropdown_sort_options keys and values must be strings"
                )
        return v

    @field_validator("filter_null_fields_exclude")
    @classmethod
    def validate_filter_null_fields_exclude(cls, v):
        """Ensure nullable filter exclusions are provided as field-name strings."""
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError("filter_null_fields_exclude must contain only strings")
        return v

    @field_validator("default_filterset_fields")
    @classmethod
    def validate_default_filterset_fields(cls, v):
        """Ensure default filter visibility config is provided as filter-name strings."""
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError("default_filterset_fields must contain only strings")
        return v
