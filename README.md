# Nominopolitan

This is an opinionated extension package for the excellent [`neapolitan`](https://github.com/carltongibson/neapolitan/tree/main) package.

It is a **very early alpha** release. No tests. Limited docs. Expect many breaking changes. You might prefer to just fork or copy and use whatever you need. Hopefully some features may make their way into `neapolitan` over time.

## Features

**Namespacing**
- Namespaced URL handling `namespace="my_app_name"`

**Templates**
- Allow specification of `base_template_path` (to your `base.html` template)
- Allow override of all `nominopolitan` templates by specifying `templates_path`
- Management command `nm_mktemplate` to copy required `nominopolitan` template (analagous to `neapolitan`'s `mktemplate`)

**Display**
- Display related field name (using `str()`) in lists and details (instead of numeric id)
- Header title context for partial updates (so the title is updated without a page reload)

**Extended `fields` and `properties` attributes**
- `fields=<'__all__' | [..]>` to specify which fields to include in list view
- `properties=<'__all__' | [..]>` to specify which properties to include in list view
- `detail_fields` and `detail_properties` to specify which to include in detail view. If not set, then:
    - `detail_fields` defaults to the resolved setting for `fields`
    - `detail_properties` defaults to `None`
- Support exclusions via `exclude`, `exclude_properties`, `detail_exclude`, `detail_exclude_properties`

**Additional Buttons**
- Support for `extra_actions` to add additional actions for each record to list views
- Support for `extra_buttons` to add additional buttons to the list view, applicable across records

**Filtersets**
- `object_list.html` styled for bootstrap to show filters.
- if `filterset_fields` is specified, style with crispy_forms if present and set htmx attributes if applicable
- if `filterset_class` is provided, then option to subclass `HTMXFilterSetMixin` and use `self.setup_htmx_attrs()` in `__init__()`
- You can now override the method `get_filter_queryset_for_field(self, field_name, model_field)` to restrict the available options for a filter field.
    - `field_name`: The name of the field being filtered (str)
    - `model_field`: The actual Django model field instance (e.g., ForeignKey, CharField)
    - For example, if you're already restricting the returned objects by overriding `get_queryset()`, then you want the filter options for foreign key fields to also be subject to this restriction.
    - So you can override `get_filter_queryset_for_field()` to return the queryset for the field, but filtered by the same restriction as your overridden `get_queryset()` method.
  
        ```python
        # Example of overrides of get_queryset and get_filter_queryset_for_field
        # def get_queryset(self):
        #     qs = super().get_queryset()
        #     qs = qs.filter(author__id=20)
        #     return qs.select_related('author')

        # def get_filter_queryset_for_field(self, field_name, model_field):
        #     """Override to restrict the available options if the field is author.
        #     """
        #     qs = super().get_filter_queryset_for_field(field_name, model_field)
        #     print(field_name)
        #     if field_name == 'author':
        #         qs = qs.filter(id=20)
        #     return qs
        ```

**`htmx` and modals**
- Support for rendering templates using `htmx`
- Support for modal display of CRUD view actions (requires `htmx` -- and Alpine for bulma)
- htmx supported pagination (requires `use_htmx = True`) for reactive loading
- Support to specify `hx_trigger` and set `response['HX-Trigger']` for every response

**Styled Templates**
- Supports `bootstrap5` (default framework). To use a different CSS framework:
    - Set `NOMINOPOLITAN_CSS_FRAMEWORK = '<framework_name>'` in `settings.py`
    - Create corresponding templates in your `templates_path` directory
    - Override `NominopolitanMixin.get_framework_styles()` in your view to add your framework's styles,  
      set the `framework` key to the name of your framework and add the required values.

**Forms**
- if `form_class` is specified, it will be used 
- if `form_class` is not specified, then there are 2 additional potential attributes: 
    - `form_fields = <'__all__' | '__fields__' | [..]>` to specify which fields to include in form
        - `'__all__'`: includes all editable fields from the model
        - `'__fields__'`: includes only editable fields that are in the resolved value for `fields`
        - Default: includes only editable fields from the resolved value for `detail_fields`
    - `form_fields_exclude = [..]` to specify which fields to exclude from the generated form
    - the resolved value of these parameters is used to generate a form class with HTML5 widgets for `date`, `datetime` and `time` fields
- Optional `create_form_class` for create operations:
    - Allows a separate form class specifically for create views
    - Useful when create and update forms need different: Field sets, Validation logic, Base classes
    - Falls back to `form_class` if not specified
- Support for `crispy-forms` if installed in project and `use_crispy` parameter is not `False`
    - make sure you have `crispy_bootstrap5` also installed if you want
    - if you have set up a different library use the correct crispy package (eg `crispy_bulma`, `crispy_tailwind`)

**Styled Table Options**
- set `table_font_size`, measured in `rem`.
    - eg `table_font_size = 0.875`. (default = 1, set in `get_table_font_size()`)
    - This will be applied to buttons, filters and the table data itself using the custom style in `object_list.html`: `.table-font-size {font-size: {{ table_font_size }};}`.
- set `table_max_col_width` as a parameter, measured in `ch` (ie number of `0` characters in the current font). 
    - eg `table_max_col_width = 10` (default = 25, set in `get_table_max_col_width()`) 
    - limit the width of the column to these characters and truncate the data text if needed.
    - if a field is truncated, a popover will be shown with the full text (**requires [`popper.js`](https://popper.js.org/docs/v2/) be installed**)
    - column headers will be wrapped to the width of the column (as determined by width of data items)
- to calculate the maximum height of the `object_list` table, we allow setting of 2 parameters:
    - `table_pixel_height_other_page_elements`, expressed in pixels (default = 0, set in `get_table_pixel_height_other_page_elements()`)
    - `table_max_height`: (default = 70, set in `get_table_max_height()`)
        - expressed as vh units (ie percentage) of the remaining blank space after subtracting `table_pixel_height_other_page_elements`
    - In the partial `list.html` these parameters are used to calculate `table-max-height` as below:
    
    ```css
    <style>
        .table-max-height {
            /* max-height: {{ table_max_height }}; */
            max-height: calc((100vh - {{ table_pixel_height_other_page_elements }}) * {{ table_max_height }} / 100);
        }
    </style>
    ```
    - You can tune these parameters depending on the page that the table is appearing on to get the right table height.
    - crazy right?.

**Table Sorting**
- click table header to toggle sorting direction (columns start off unsorted)
- the method always includes a secondary sort by primary key for stable pagination
- will use `htmx` if `use_htmx is True`
- current `list.html` template will display bootstrap icons (if installed) for sorting direction:
    - you must [install bootstrap icons](https://getbootstrap.com/docs/5.3/getting-started/introduction/#cdn-links) to use this feature
- if filter options are set, the returned queryset will be sorted and filters
    - *current issue where if filters are displayed and you sort, the filters are hidden; just redisplay them with the button*

**`sample` App**
- `sample` app is a simple example of how to use `django_nominopolitan`. It's available in the repository and not part of the package.
- it includes management commands `create_sample_data` and `delete_sample_data`

**Management Commands**

- `nm_mktemplate`:
    - Bootstraps CRUD templates from `nominopolitan` templates instead of `neapolitan` templates
    - Basic syntax:
        ```bash
        python manage.py nm_mktemplate <target>
        ```
    - The `target` can be either:
        - An app name (e.g., `myapp`) to copy the entire template structure
        - An app.Model combination (e.g., `myapp.Book`) for model-specific templates
    
    - Options for model-specific templates:
        ```bash
        # Copy all CRUD templates for a model
        python manage.py nm_mktemplate myapp.Book --all

        # Copy individual templates
        python manage.py nm_mktemplate myapp.Book --list      # List view template
        python manage.py nm_mktemplate myapp.Book --detail    # Detail view template
        python manage.py nm_mktemplate myapp.Book --form      # Form template
        python manage.py nm_mktemplate myapp.Book --delete    # Delete confirmation template
        ```

    - Templates will be copied to your app's template directory following Django's template naming conventions
    - If the target directory already exists, files will be overwritten with a warning

- `nm_clear_session_keys`
    - Used to clear all user session keys related to nominopolitan

- `nm_help`
    - Displays the Nominopolitan README.md documentation in a paginated format
    - `--lines` to specify number of lines to display per page (default: 20)
    - `--all` to display entire content without pagination


## Installation and Dependencies

Check [`pypoetry.toml`](https://github.com/doctor-cornelius/django-nominopolitan/blob/main/pyproject.toml) for the versions being used.

### Basic Installation

Basic installation with pip:
```bash
pip install django-nominopolitan
```

This will automatically install:
- `django`
- `django-template-partials`
- `pydantic`

### Required Dependencies

You must install `neapolitan` (version 24.8) as it's required for core functionality:
```bash
pip install "django-nominopolitan[neapolitan]"
```

### Optional Dependencies

- HTMX support:
```bash
pip install "django-nominopolitan[htmx]"
```

- Crispy Forms support (includes both `django-crispy-forms` and `crispy-bootstrap5`):
```bash
pip install "django-nominopolitan[crispy]"
```

You can combine multiple optional dependencies:
```bash
pip install "django-nominopolitan[neapolitan,htmx,crispy]"
```

### Frontend Dependencies
These JavaScript and CSS libraries must be included in your base template:

1. Required JavaScript libraries:
   - Popper.js - Required for table column text truncation popovers
   - HTMX - Required if `use_htmx=True`
   - Alpine.js - Required if using modals

2. If using default templates:
   - Bootstrap 5 CSS and JS
   - Bootstrap Icons (for sorting indicators)

See the example base template in `django_nominopolitan/templates/django_nominopolitan/base.html` for a complete implementation with CDN links.

## Configuration

Add to your `settings.py`:
```python
INSTALLED_APPS = [
    ...
    "nominopolitan",  # must come before neapolitan
    "neapolitan",     # required for NominopolitanMixin
    "django_htmx",    # if using htmx features
    ...
]
```

Additional configuration:
1. For HTMX features (`use_htmx=True`): 
   - Install HTMX in your base template
   - Ensure `django-htmx` is installed
2. For modal support (`use_modal=True`):
   - Requires `use_htmx=True`
   - Install Alpine.js in your base template

## Usage

The best starting point is [`neapolitan`'s docs](https://noumenal.es/neapolitan/). The basic idea is to specify model-based CRUD views using:

```python
# neapolitan approach
class ProjectView(CRUDView):
    model = projects.models.Project
    fields = ["name", "owner", "last_review", "has_tests", "has_docs", "status"]
```

The `nominopolitan` mixin adds a number of features to this. The values below are indicative examples.

```python
from nominopolitan.mixins import NominopolitanMixin
from neapolitan.views import CRUDView

class ProjectCRUDView(NominopolitanMixin, CRUDView):
    # *******************************************************************
    # Standard neapolitan attributes
    model = models.Project # this is mandatory

    # examples of other available neapolitan class attributes
    url_base = "different_project" # use this to override the property url_base
        # which will default to the model name. Useful if you want multiple CRUDViews 
        # for the same model
    form_class = ProjectForm # if you want to use a custom form

    # check the code in neapolitan.views.CRUDView for all available attributes

    # ******************************************************************
    # nominopolitan attributes
    namespace = "my_app_name" # specify the namespace (optional)
        # if your urls.py has app_name = "my_app_name"

    # which fields and properties to include in the list view
    fields = '__all__' # if you want to include all fields
        # you can omit the fields attribute, in which case it will default to '__all__'

    exclude = ["description",] # list of fields to exclude from list

    properties = ["is_overdue",] # if you want to include @property fields in the list view
        # properties = '__all__' if you want to include all @property fields

    properties_exclude = ["is_overdue",] # if you want to exclude @property fields from the list view

    # sometimes you want additional fields in the detail view
    detail_fields = ["name", "project_owner", "project_manager", "due_date", "description",]
        # or '__all__' to use all model fields
        # or '__fields__' to use the fields attribute
        # if you leave detail_fields to None, it will default be treated as '__fields__'

    detail_exclude = ["description",] # list of fields to exclude from detail view

    detail_properties = '__all__' # if you want to include all @property fields
        # or a list of valid properties
        # or '__properties__' to use the properties attribute

    detail_properties_exclude = ["is_overdue",] # if you want to exclude @property fields from the detail view

    # you can specify the fields to include in forms if no form_class is specified.
    # note if a fom_class IS specified then it will be used
    form_fields = ["name", "project_owner", "project_manager", "due_date", "description",]
    # form_fields = '__all__' if you want to include all model fields (only editable fields will be included)
    # form_fields = '__fields__' if you want to use the fields attribute (only editable fields will be included)
    # if not specified, it will default to only editable fields in the resolved versin of detail_fields (ie excluding detail_exclude)
    form_fields_exclude = ["description",] # list of fields to exclude from forms

    create_form_class = forms.ProjectCreateForm # if you want a separate create form
        # the update form always uses specified form_class OR the generated form class based on form_fields and form_fields_exclude

    # filtersets
    filterset_fields = ["name", "project_owner", "project_manager", "due_date",]
        # this is a standard neapolitan parameter, but nominopolitan converts this 
        # to a more elaborate filterset class

    # Forms
    use_crispy = True # will default to True if you have `crispy-forms` installed
        # if you set it to True without crispy-forms installed, it will resolve to False
        # if you set it to False with crispy-forms installed, it will resolve to False

    # Templates
    base_template_path = "core/base.html" # defaults to inbuilt "nominopolitan/base.html"
    templates_path = "myapp" # if you want to override all the templates in another app
        # or include one of your own apps; eg templates_path = "my_app_name/nominopolitan" 
        # and then place in my_app_name/templates/my_app_name/nominopolitan

    # table display parameters
    table_pixel_height_other_page_elements = 100 # this will be expressed in pixels
    table_max_height = 80 # as a percentage of remaining viewport height
    table_font_size = '1.05' # expressed as rem
    table_max_col_width = '25' # expressed as `ch` (characters wide)

    # htmx & modals
    use_htmx = True # if you want the View, Detail, Delete and Create forms to use htmx
        # if you do not set use_modal = True, the CRUD templates will be rendered to the
        # hx-target used for the list view
        # Requires:
            # htmx installed in your base template
            # django_htmx installed and configured in your settings

    hx_trigger = 'changedMessages'  # Single event trigger (strings, numbers converted to strings)
        # Or trigger multiple events with a dict:
            # hx_trigger = {
            #     'changedMessages': None,    # Event without data
            #     'showAlert': 'Success!',    # Event with string data
            #     'updateCount': 42           # Event with numeric data
            # }
        # hx_trigger finds its way into every response as:
            # request['HX-Trigger'] = self.get_hx_trigger() in self.render_to_response()
        # valid types are (str, int, float, dict)
            # but dict must be of form {k:v, k:v, ...} where k is a string and v can be any valid type


    use_modal = True #If you want to use the modal specified in object_list.html for all action links.
        # This will target the modal (id="nominopolitanModalContent") specified in object_list.html
        # Requires:
            # use_htmx = True
            # Alpine installed in your base template
            # htmx installed in your base template
            # django_htmx installed and configured in your settings

    modal_id = "myCustomModalId" # Allows override of the default modal id "nominopolitanBaseModal"

    modal_target = "myCustomModalContent" # Allows override of the default modal target
        # which is #nominopolitanModalContent. Useful if for example
        # the project has a modal with a different id available
        # eg in the base template. This is where the modal content will be rendered.

    # extra buttons that appear at the top of the page next to the Create or filters buttons
    extra_buttons = [
        {
            "url_name": "fstp:home",        # namespace:url_pattern
            "text": "Home Again",           # text to display on button
            "button_class": "btn-success",  # intended as semantic colour for button
                # defaults to NominopolitanMixin.get_framework_styles()['extra_default']
            "htmx_target": "content",       # relevant only if use_htmx is True. Disregarded if display_modal is True
            "display_modal": False,         # if the button should display a modal.
                # Note: modal will auto-close after any form submission
                # Note: if True then htmx_target is ignored
            "needs_pk": False,              # if the URL needs the object's primary key
            "extra_class_attrs": "bg-warning text-dark rounded-pill border border-dark", # any additional class attributes
        },
    ]
    # extra actions (extra buttons for each record in the list)
    extra_actions = [ # adds additional actions for each record in the list
        {
            "url_name": "fstp:do_something",  # namespace:url_pattern
            "text": "Do Something",
            "needs_pk": False,  # if the URL needs the object's primary key
            "hx_post": True, # use POST request instead of the default GET
            "button_class": "btn-primary", # semantic colour for button (defaults to "is-link")
            "htmx_target": "content", # htmx target for the extra action response 
                # (if use_htmx is True)
                # NB if you have use_modal = True and do NOT specify htmx_target, then response
                # will be directed to the modal 
            "display_modal": False, # when use_modal is True but for this action you do not
                # want to use the modal for whatever is returned from the view, set this to False
                # the default if empty is whatever get_use_modal() resolves to
        },
    ]
```
