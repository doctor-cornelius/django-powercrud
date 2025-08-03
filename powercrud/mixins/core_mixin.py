import logging

from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.reverse_related import ManyToOneRel
from django.conf import settings

from ..validators import PowerCRUDMixinValidator
from django.http import Http404

log = logging.getLogger("powercrud")

class CoreMixin:
    """
    The core mixin for powercrud. Contains the fundamental setup,
    initialization, and queryset logic.
    """
    # namespace if appropriate
    namespace: str | None = None

    # template parameters
    templates_path: str = f"powercrud/{getattr(settings, 'NOMINOPOLITAN_CSS_FRAMEWORK', 'daisyui')}"
    base_template_path: str = f"{templates_path}/base.html"

    # forms
    use_crispy: bool | None = None

    # field and property inclusion scope
    exclude: list[str] = []
    properties: list[str] = []
    properties_exclude: list[str] = []

    # for the detail view
    detail_fields: list[str] = []
    detail_exclude: list[str] = []
    detail_properties: list[str] = []
    detail_properties_exclude: list[str] = []

    # form fields (if no form_class is specified)
    form_fields: list[str] = []
    form_fields_exclude: list[str] = []

    # bulk edit parameters
    bulk_fields: list[str] = []
    bulk_delete: bool = False
    bulk_full_clean: bool = True  # If True, run full_clean() on each object during bulk edit

    # async processing parameters
    bulk_async: bool = False
    bulk_async_conflict_checking = True  # Default enabled
    bulk_min_async_records: int = 20
    bulk_async_backend: str = 'q2' # currently only 'q2' is supported; future 'celery' backend proposed
    bulk_async_notification: str = 'status_page' # 'status_page' or 'email' or 'messages'
    bulk_async_allow_anonymous = True # default is to allow anonymous async operations

    # htmx
    use_htmx: bool | None = None
    default_htmx_target: str = '#content'
    hx_trigger: str | dict[str, str] | None = None

    # modals (if htmx is active)
    use_modal: bool | None = None
    modal_id: str | None = None
    modal_target: str | None = None

    # table display parameters
    table_pixel_height_other_page_elements: int | float = 0  # px pixels
    table_max_height: int = 70 # expressed as vh units (ie percentage) of the remaining blank space 
    # after subtracting table_pixel_height_other_page_elements

    table_max_col_width: int = None # Expressed in ch units
    table_header_min_wrap_width: int = None  # Expressed in ch units

    table_classes: str = ''
    action_button_classes: str = ''
    extra_button_classes: str = ''

    # Add this class attribute to control M2M filter logic
    m2m_filter_and_logic = False  # False for OR logic (default), True for AND logic
    dropdown_sort_options: dict = {} # field to store dict of related object fields to sort

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get all attributes that should be validated
        config_dict = {
            attr: getattr(self, attr)
            for attr in PowerCRUDMixinValidator.__fields__.keys()
            if hasattr(self, attr)
        }

        try:
            validated_settings = PowerCRUDMixinValidator(**config_dict)
            # Update instance attributes with validated values
            for field_name, value in validated_settings.dict().items():
                setattr(self, field_name, value)
        except ValueError as e:
            class_name = self.__class__.__name__
            raise ImproperlyConfigured(
                f"Invalid configuration in class '{class_name}': {str(e)}"
            )

        # determine the starting list of fields (before exclusions)
        if not self.fields or self.fields == '__all__':
            # set to all fields in model
            self.fields = self._get_all_fields()
        elif type(self.fields) == list:
            # check all are valid fields
            all_fields = self._get_all_fields()
            for field in self.fields:
                if field not in all_fields:
                    raise ValueError(f"Field {field} not defined in {self.model.__name__}")
        elif type(self.fields) != list:
            raise TypeError("fields must be a list")        
        else:
            raise ValueError("fields must be '__all__', a list of valid fields or not defined")

        # exclude fields
        if type(self.exclude) == list:
            self.fields = [field for field in self.fields if field not in self.exclude]
        else:
            raise TypeError("exclude must be a list")

        if self.properties:
            if self.properties == '__all__':
                # Set self.properties to a list of every property in self.model
                self.properties = self._get_all_properties()
            elif type(self.properties) == list:
                # check all are valid properties
                all_properties = self._get_all_properties()
                for prop in self.properties:
                    if prop not in all_properties:
                        raise ValueError(f"Property {prop} not defined in {self.model.__name__}")
            elif type(self.properties) != list:
                raise TypeError("properties must be a list or '__all__'")

        # exclude properties
        if type(self.properties_exclude) == list:
            self.properties = [prop for prop in self.properties if prop not in self.properties_exclude]
        else:
            raise TypeError("properties_exclude must be a list")

        # determine the starting list of detail_fields (before exclusions)
        if self.detail_fields == '__all__':
            # Set self.detail_fields to a list of every field in self.model
            self.detail_fields = self._get_all_fields()        
        elif not self.detail_fields or self.detail_fields == '__fields__':
            # Set self.detail_fields to self.fields
            self.detail_fields = self.fields
        elif type(self.detail_fields) == list:
            # check all are valid fields
            all_fields = self._get_all_fields()
            for field in self.detail_fields:
                if field not in all_fields:
                    raise ValueError(f"detail_field {field} not defined in {self.model.__name__}")
        elif type(self.detail_fields) != list:
            raise TypeError("detail_fields must be a list or '__all__' or '__fields__' or a list of fields")

        # exclude detail_fields
        if type(self.detail_exclude) == list:
            self.detail_fields = [field for field in self.detail_fields 
                                  if field not in self.detail_exclude]
        else:
            raise TypeError("detail_fields_exclude must be a list")

        # add specified detail_properties
        if self.detail_properties:
            if self.detail_properties == '__all__':
                # Set self.detail_properties to a list of every property in self.model
                self.detail_properties = self._get_all_properties()
            elif self.detail_properties == '__properties__':
                # Set self.detail_properties to a list of every property in self.model
                self.detail_properties = self.properties
            elif type(self.detail_properties) == list:
                # check all are valid properties
                all_properties = self._get_all_properties()
                for prop in self.detail_properties:
                    if prop not in all_properties:
                        raise ValueError(f"Property {prop} not defined in {self.model.__name__}")
            elif type(self.detail_properties) != list:
                raise TypeError("detail_properties must be a list or '__all__' or '__properties__'")

        # exclude detail_properties
        if type(self.detail_properties_exclude) == list:
            self.detail_properties = [prop for prop in self.detail_properties 
                                  if prop not in self.detail_properties_exclude]
        else:
            raise TypeError("detail_properties_exclude must be a list")

        # validate bulk_fields list if present
        if self.bulk_fields:
            if isinstance(self.bulk_fields, list):
                all_fields = self._get_all_fields()
                for field_name in self.bulk_fields:
                    if not isinstance(field_name, str):
                        raise ValueError(f"Invalid bulk field configuration: {field_name}. Must be a string.")

                    if field_name not in all_fields:
                        raise ValueError(f"Bulk field '{field_name}' not defined in {self.model.__name__}")

        # Process form_fields last, after all other field processing is complete
        all_editable = self._get_all_editable_fields()

        if not self.form_fields:
            # Default to editable fields from detail_fields
            self.form_fields = [
                f for f in self.detail_fields 
                if f in all_editable
            ]
        elif self.form_fields == '__all__':
            self.form_fields = all_editable
        elif self.form_fields == '__fields__':
            self.form_fields = [
                f for f in self.fields 
                if f in all_editable
            ]
        else:
            # Validate that specified fields exist and are editable
            invalid_fields = [f for f in self.form_fields if f not in all_editable]
            if invalid_fields:
                raise ValueError(
                    f"The following form_fields are not editable fields in {self.model.__name__}: "
                    f"{', '.join(invalid_fields)}"
                )

        # Process form fields exclusions
        if self.form_fields_exclude:
            self.form_fields = [
                f for f in self.form_fields 
                if f not in self.form_fields_exclude
            ]

        # check async if enabled
        if self.bulk_async:
            if not self.get_bulk_async_enabled():
                log.warning(f"bulk_async is enabled but backend '{self.get_bulk_async_backend()}' is not available")

    def _get_all_fields(self):
        fields = [field.name for field in self.model._meta.get_fields()]

        # Exclude reverse relations
        fields = [
            field.name for field in self.model._meta.get_fields()
            if not isinstance(field, ManyToOneRel)
        ]
        return fields

    def _get_all_editable_fields(self):
        """Gets all editable fields in model"""
        return [
            field.name
            for field in self.model._meta.get_fields()
            if hasattr(field, 'editable') and field.editable
        ]

    def _get_all_properties(self):
        return [name for name in dir(self.model)
                    if isinstance(getattr(self.model, name), property) and name != 'pk'
                ]
    
    def get_queryset(self):
        """
        Get the queryset for the view, applying sorting if specified.
        Always includes a secondary sort by primary key for stable pagination.
        """
        queryset = super().get_queryset()
        sort_param = self.request.GET.get('sort')

        if sort_param:
            # Handle descending sort (prefixed with '-')
            descending = sort_param.startswith('-')
            field_name = sort_param[1:] if descending else sort_param

            # Get all valid field names and properties
            valid_fields = {f.name: f.name for f in self.model._meta.fields}
            # Add any properties that are sortable
            valid_fields.update({p: p for p in getattr(self, 'properties', [])})

            # Try to match the sort parameter to a valid field
            # First try exact match
            if field_name in valid_fields:
                sort_field = valid_fields[field_name]
            else:
                # Try case-insensitive match
                matches = {k.lower(): v for k, v in valid_fields.items()}
                sort_field = matches.get(field_name.lower())

            if sort_field:
                # Re-add the minus sign if it was descending
                if descending:
                    sort_field = f'-{sort_field}'
                    # Add secondary sort by -pk for descending
                    queryset = queryset.order_by(sort_field, '-pk')
                else:
                    # Add secondary sort by pk for ascending
                    queryset = queryset.order_by(sort_field, 'pk')
        else:
            # If no sort specified, sort by pk as default
            queryset = queryset.order_by('pk')

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Handle GET requests for list view, including filtering and pagination.
        """
        queryset = self.get_queryset()
        filterset = self.get_filterset(queryset)
        if filterset is not None:
            queryset = filterset.qs

        if not self.allow_empty and not queryset.exists():
            raise Http404

        paginate_by = self.get_paginate_by()
        if paginate_by is None:
            # Unpaginated response
            self.object_list = queryset
            context = self.get_context_data(
                page_obj=None,
                is_paginated=False,
                paginator=None,
                filterset=filterset,
                sort=request.GET.get('sort', ''),  # Add sort to context
                use_htmx=self.get_use_htmx(),
                request=request,
            )
        else:
            # Paginated response
            page = self.paginate_queryset(queryset, paginate_by)
            self.object_list = page.object_list
            context = self.get_context_data(
                page_obj=page,
                is_paginated=page.has_other_pages(),
                paginator=page.paginator,
                filterset=filterset,
                sort=request.GET.get('sort', ''),  # Add sort to context
                use_htmx=self.get_use_htmx(),
                request=request,
            )

        return self.render_to_response(context)
