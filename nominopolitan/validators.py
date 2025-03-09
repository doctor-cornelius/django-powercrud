from pydantic import BaseModel, Field, field_validator
from typing import Union, Optional, List, Literal

class NominopolitanMixinValidator(BaseModel):
    """Validation model for NominopolitanMixin settings"""
    # namespace settings
    namespace: Optional[str] = None
    
    # template parameters
    templates_path: str = Field(
        default="nominopolitan/bootstrap5",
        description="Path to template directory"
    )
    base_template_path: Optional[str] = None
    
    # forms
    use_crispy: Optional[bool] = None
    
    # field and property inclusion scope
    fields: Union[List[str], Literal['__all__']] = []
    properties: Union[List[str], Literal['__all__']] = []
    exclude: List[str] = []
    properties_exclude: List[str] = []
    
    # Detail view settings
    detail_fields: Union[List[str], Literal['__all__', '__fields__']] = '__fields__'
    detail_exclude: List[str] = []
    detail_properties: Union[List[str], Literal['__all__', '__properties__']] = '__properties__'
    detail_properties_exclude: List[str] = []

    @field_validator('fields', 'properties', 'detail_fields', 'detail_properties')
    @classmethod
    def validate_field_specs(cls, v):
        if isinstance(v, list) and not all(isinstance(x, str) for x in v):
            raise ValueError("List must contain only strings")
        return v
    
    # htmx
    use_htmx: Optional[bool] = None
    default_htmx_target: str = '#content'
    hx_trigger: Optional[Union[str, int, float, dict]] = None
    
    # modals
    use_modal: Optional[bool] = None
    modal_id: Optional[str] = None
    modal_target: Optional[str] = None
    
    # table display parameters
    table_pixel_height_other_page_elements: Union[int, float] = Field(
        default=0,
        ge=0,
        description="Height of other page elements in pixels (px)"
    )
    table_max_height: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Maximum table height as percentage (vh units)"
    )
    table_font_size: Union[int, float] = Field(
        default=1,
        gt=0,
        description="Table font size in rem units"
    )
    table_max_col_width: int = Field(
        default=25,
        gt=0,
        description="Maximum column width in ch units"
    )

    @field_validator('hx_trigger')
    @classmethod
    def validate_hx_trigger(cls, v):
        if isinstance(v, dict):
            if not all(isinstance(k, str) for k in v.keys()):
                raise ValueError("HX-Trigger dict keys must be strings")
        return v

    class Config:
        validate_assignment = True
