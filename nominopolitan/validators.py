from pydantic import BaseModel, Field, field_validator
from typing import Union, Optional, List, Literal

class NominopolitanMixinValidator(BaseModel):
    """Validation model for NominopolitanMixin settings"""
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
    
    # modals
    use_modal: Optional[bool]
    modal_id: Optional[str]
    modal_target: Optional[str]
    
    # table display parameters
    table_pixel_height_other_page_elements: Optional[Union[int, float]] = Field(ge=0)
    table_max_height: Optional[int] = Field(ge=0, le=100)
    table_font_size: Optional[Union[int, float]] = Field(gt=0)
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

    @field_validator('form_fields_exclude')
    @classmethod
    def validate_form_fields_exclude(cls, v):
        if v is None:
            return v
        if not all(isinstance(x, str) for x in v):
            raise ValueError("form_fields_exclude must contain only strings")
        return v

    class Config:
        validate_assignment = True
