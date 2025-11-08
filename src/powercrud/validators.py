from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Union, Optional, List, Literal, Dict, Any, Callable

class PowerCRUDMixinValidator(BaseModel):
    """Validation model for PowerCRUDMixin settings"""
    model_config = ConfigDict(validate_assignment=True)
    # namespace settings
    namespace: Optional[str]
    
    # template parameters
    templates_path: Optional[str]
    base_template_path: Optional[str]
    
    # forms
    use_crispy: Optional[bool]
    
    # field and property inclusion scope
    fields: Optional[Union[List[str], Literal['__all__']]]
    properties: Optional[Union[List[str], Literal['__all__']]]
    exclude: Optional[List[str]]
    properties_exclude: Optional[List[str]]
    
    # Detail view settings
    detail_fields: Optional[Union[List[str], Literal['__all__', '__fields__']]]
    detail_exclude: Optional[List[str]]
    detail_properties: Optional[Union[List[str], Literal['__all__', '__properties__']]]
    detail_properties_exclude: Optional[List[str]]
    
    # htmx
    use_htmx: Optional[bool]
    default_htmx_target: Optional[str]
    hx_trigger: Optional[Union[str, int, float, dict]]

    # inline editing
    inline_edit_enabled: Optional[bool] = None
    inline_edit_fields: Optional[Union[List[str], Literal['__all__', '__fields__']]] = None
    inline_field_dependencies: Optional[Dict[str, Dict[str, Any]]] = None
    inline_edit_requires_perm: Optional[str] = None
    inline_edit_allowed: Optional[Callable] = None

    # modals
    use_modal: Optional[bool]
    modal_id: Optional[str]
    modal_target: Optional[str]
    
    # table display parameters
    table_pixel_height_other_page_elements: Optional[Union[int, float]] = Field(ge=0)
    table_max_height: Optional[int] = Field(ge=0, le=100)
    table_max_col_width: Optional[int] = Field(gt=0)

    # form fields
    form_fields: Optional[Union[List[str], Literal['__all__', '__fields__']]]
    form_fields_exclude: Optional[List[str]]

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
