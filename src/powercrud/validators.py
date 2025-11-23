from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Union, Optional, List, Literal, Dict, Any, Callable

class PowerCRUDMixinValidator(BaseModel):
    """Validation model for PowerCRUDMixin settings"""
    model_config = ConfigDict(validate_assignment=True)
    # namespace settings
    namespace: Optional[str] = None
    
    # template parameters
    templates_path: Optional[str] = None
    base_template_path: Optional[str] = None
    
    # forms
    use_crispy: Optional[bool] = None
    
    # field and property inclusion scope
    fields: Optional[Union[List[str], Literal['__all__']]] = None
    properties: Optional[Union[List[str], Literal['__all__']]] = None
    exclude: Optional[List[str]] = None
    properties_exclude: Optional[List[str]] = None
    
    # Detail view settings
    detail_fields: Optional[Union[List[str], Literal['__all__', '__fields__']]] = None
    detail_exclude: Optional[List[str]] = None
    detail_properties: Optional[Union[List[str], Literal['__all__', '__properties__']]] = None
    detail_properties_exclude: Optional[List[str]] = None
    
    # htmx
    use_htmx: Optional[bool] = None
    default_htmx_target: Optional[str] = None
    hx_trigger: Optional[Union[str, int, float, dict]] = None

    # inline editing
    inline_edit_enabled: Optional[bool] = None
    inline_edit_fields: Optional[Union[List[str], Literal['__all__', '__fields__']]] = None
    inline_field_dependencies: Optional[Dict[str, Dict[str, Any]]] = None
    inline_edit_requires_perm: Optional[str] = None
    inline_edit_allowed: Optional[Callable] = None

    # modals
    use_modal: Optional[bool] = None
    modal_id: Optional[str] = None
    modal_target: Optional[str] = None
    
    # table display parameters
    table_pixel_height_other_page_elements: Optional[Union[int, float]] = Field(default=None, ge=0)
    table_max_height: Optional[int] = Field(default=None, ge=0, le=100)
    table_max_col_width: Optional[int] = Field(default=None, gt=0)
    table_classes: Optional[str] = None
    action_button_classes: Optional[str] = None
    extra_button_classes: Optional[str] = None

    # form fields
    form_fields: Optional[Union[List[str], Literal['__all__', '__fields__']]] = None
    form_fields_exclude: Optional[List[str]] = None

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
    dropdown_sort_options: Optional[Dict[str, str]] = None
    m2m_filter_and_logic: Optional[bool] = None
    inline_preserve_required_fields: Optional[bool] = None
    async_manager_class: Optional[Any] = None
    async_manager_class_path: Optional[str] = None
    async_manager_config: Optional[Dict[str, Any]] = None
    paginate_by: Optional[int] = None

    @field_validator('fields', 'properties', 'detail_fields', 'detail_properties')
    @classmethod
    def validate_field_specs(cls, v):
        if v is None:
            return v
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("List must contain only strings")
        return v

    @field_validator('hx_trigger')
    @classmethod
    def validate_hx_trigger(cls, v):
        if v is None:
            return v
        if isinstance(v, dict):
            if not all(isinstance(k, str) for k in v.keys()):
                raise ValueError("HX-Trigger dict keys must be strings")
        return v

    @field_validator('default_htmx_target')
    @classmethod
    def validate_default_htmx_target(cls, v, info):
        if info.data.get('use_htmx') is True and v is None:
            raise ValueError("default_htmx_target is required when use_htmx is True")
        return v

    @field_validator('form_fields')
    @classmethod
    def validate_form_fields(cls, v):
        if v is None:
            return v
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("form_fields must contain only strings")
        return v

    @field_validator('inline_edit_fields')
    @classmethod
    def validate_inline_edit_fields(cls, v):
        if v is None:
            return v
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("inline_edit_fields must contain only strings")
        return v

    @field_validator('inline_field_dependencies')
    @classmethod
    def validate_inline_field_dependencies(cls, v):
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("inline_field_dependencies must be a dictionary")
        for field_name, config in v.items():
            if not isinstance(field_name, str):
                raise ValueError("inline_field_dependencies keys must be strings")
            if not isinstance(config, dict):
                raise ValueError("inline_field_dependencies values must be dictionaries")
        return v

    @field_validator('form_fields_exclude')
    @classmethod
    def validate_form_fields_exclude(cls, v):
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError("form_fields_exclude must contain only strings")
        return v

    @field_validator('bulk_fields')
    @classmethod
    def validate_bulk_fields(cls, v):
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError("bulk_fields must contain only strings")
        return v

    @field_validator('dropdown_sort_options')
    @classmethod
    def validate_dropdown_sort_options(cls, v):
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("dropdown_sort_options must be a dictionary")
        for key, value in v.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("dropdown_sort_options keys and values must be strings")
        return v
