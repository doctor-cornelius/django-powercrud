from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Union, Optional, List, Literal, Dict, Any, Callable
import re


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
    column_help_text: Optional[Dict[str, str]] = None
    list_cell_tooltip_fields: Optional[List[str]] = None
    column_sort_fields_override: Optional[Dict[str, str]] = None

    # forms
    use_crispy: Optional[bool] = None
    searchable_selects: Optional[bool] = True

    # field and property inclusion scope
    fields: Optional[Union[List[str], Literal["__all__"]]] = None
    properties: Optional[Union[List[str], Literal["__all__"]]] = None
    exclude: Optional[List[str]] = None
    properties_exclude: Optional[List[str]] = None

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

    # table display parameters
    table_pixel_height_other_page_elements: Optional[Union[int, float]] = Field(
        default=None, ge=0
    )
    table_max_height: Optional[int] = Field(default=None, ge=0, le=100)
    table_max_col_width: Optional[int] = Field(default=None, gt=0)
    table_classes: Optional[str] = None
    action_button_classes: Optional[str] = None
    extra_button_classes: Optional[str] = None
    extra_actions_mode: Optional[Literal["buttons", "dropdown"]] = None
    extra_actions_dropdown_open_upward_bottom_rows: Optional[int] = Field(
        default=None, ge=0
    )
    show_record_count: Optional[bool] = None
    show_bulk_selection_meta: Optional[bool] = None

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
    filter_null_fields_exclude: Optional[List[str]] = None
    m2m_filter_and_logic: Optional[bool] = None
    inline_preserve_required_fields: Optional[bool] = None
    async_manager_class: Optional[Any] = None
    async_manager_class_path: Optional[str] = None
    async_manager_config: Optional[Dict[str, Any]] = None
    paginate_by: Optional[int] = None

    @field_validator("fields", "properties", "detail_fields", "detail_properties")
    @classmethod
    def validate_field_specs(cls, v):
        if v is None:
            return v
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("List must contain only strings")
        return v

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

    @field_validator("column_help_text", "column_sort_fields_override")
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
        return v

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

    @field_validator("list_cell_tooltip_fields")
    @classmethod
    def validate_list_cell_tooltip_fields(cls, v):
        """Require tooltip field declarations to be non-empty strings."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("list_cell_tooltip_fields must be a list of strings")
        for value in v:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    "list_cell_tooltip_fields must contain only non-empty strings"
                )
        return v

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
