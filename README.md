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
    - If you hae a property `myprop` and you set `myprop.fget.short_description="Special Title"`, then that will be used as the column title if included in the table
- `detail_fields` and `detail_properties` to specify which to include in detail view. If not set, then:
    - `detail_fields` defaults to the resolved setting for `fields`
    - `detail_properties` defaults to `None`
- Support exclusions via `exclude`, `exclude_properties`, `detail_exclude`, `detail_exclude_properties`

**Filtersets**
- `object_list.html` styled to show filters.
- if `filterset_class` is provided, then option to subclass `HTMXFilterSetMixin` and use `self.setup_htmx_attrs()` in `__init__()- if `filterset_fields` is specified, style with crispy_forms if present and set htmx attributes if applicable. Optionally, can also set:
  -  `filter_queryset_options` to control which options appear in filter dropdowns. For example:

    ```python
    filter_queryset_options = {
        # Only show specific author in dropdown
        'author': {'name': 'Nancy Wilson'},
        
        # Only show genres containing "fiction"
        'genres': {'name__icontains': 'fiction'},
    }
    ```

  - `filter_sort_options` to control how filter options are sorted
      - takes a field name with optional `-` prefix for descending order
`
- **M2M filters**
    - `m2m_filter_and_logic = True` to use AND logic for M2M filters (default is OR logic)
  
- **Overrides**
    - You can override the method `get_filter_queryset_for_field(self, field_name, model_field)` to restrict the available options for a filter field.
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
- Supports `bootstrap5` (default framework) and `daisyUI` (v5, which uses tailwindcss v4). To use a different CSS framework:
    - Set `NOMINOPOLITAN_CSS_FRAMEWORK = '<framework_name>'` in `settings.py`
    - Create corresponding templates in your `templates_path` directory
    - Override `NominopolitanMixin.get_framework_styles()` in your view to add your framework's styles,  
      set the `framework` key to the name of your framework and add the required values.

**Bulk Edit**
- Support for bulk edit of multiple records
- include `bulk_fields` list in view definition with names of fields to be updated
- row selection survives pagination and both htmx and full page reloads (actually it's kind of permanent for a model until you explicitly clear selection ;)
- bulk update is atomic: either all pass or no edits are made
- bulk delete also supported (with confirmation step and safety verification)
- Clear separation between update and delete operations in the UI
- bulk update process runs `full_clean()` and `save()` on every record
    - you can specify `bulk_full_clean = False` (default is `True`) to skip full clean step

**Tailwind CSS Considerations**

Tailwind needs to scan all the classes used in your project. To do this @TODO

If using a `tailwindcss` framework (including `daisyUI`) then you need to make sure that the classes from this package `nominopolitan` are included in your project's tailwind build. There are two ways to do this.

1. **Explicitly add using @source**. For `tailwindcss` v4, as per [these instructions](https://tailwindcss.com/docs/detecting-classes-in-source-files#explicitly-registering-sources), you need to use the `@source` command in your `tailwind.css` (or `main.css` or whatever you've called it).

    To detect the correct path for your package, you can use:

    ```python
    >>>import django_nominopolitan 
    >>>print(django_nominopolitan.__path__)
    ['/usr/local/lib/python3.12/site-packages/nominopolitan']
    ```

    In which case you would enter `@source: "/usr/local/lib/python3.12/site-packages/nominopolitan";`, so the top part of your `tailwind.css` file would look like this:

    ```css
    @import "tailwindcss";`
    @source "/usr/local/lib/python3.12/site-packages/nominopolitan";
    ```

2. **Management Command**. If you prefer not to follow the tailwindcss instructions (!) then you can run the included management command `nm_extract_tailwind_classes` as discussed in the management commands section below.

**Forms**
- if `form_class` is specified, it will be used 
- if `form_class` is not specified, then there are 2 additional potential attributes: 
    - `form_fields = <'__all__' | '__fields__' | [..]>` to specify which fields to include in form
        - `'__all__'`: includes all editable fields from the model
        - `'__fields__'`: includes only editable fields that are in the resolved value for `fields`
        - Default: includes only editable fields from the resolved value for `detail_fields`
    - `form_fields_exclude = [..]` to specify which fields to exclude from the generated form
    - the resolved value of these parameters is used to generate a form class with HTML5 widgets for `date`, `datetime` and `time` fields

**Using `crispy-forms`**

Support for `crispy-forms` is enabled if it's installed in your project and the `use_crispy` parameter is not explicitly set to `False`. There are some important details about how this works:

- The template `object_form.html` already includes:
  - A `<form>` tag (needed for HTMX attributes)
  - A `{% csrf_token %}` tag
  - Conditional inclusion of crispy rendering via `{% include framework_template_path|add:"/crispy_partials.html#crispy_form" %}`

- The `crispy_partials.html` template uses `{% crispy form %}` syntax which by default would:
  - Generate its own `<form>` tag (causing nested forms)
  - Add its own CSRF token (causing duplicate tokens)

- To prevent duplicating `<form>` and CSRF token issues, `nominopolitan` automatically adds a FormHelper to your form class with:
  
  ```python
  self.helper = FormHelper()
  self.helper.form_tag = False     # Don't generate a form tag
  self.helper.disable_csrf = True  # Don't add a CSRF token
  ```

- **Important**: You do NOT need to add a FormHelper to your form class. Nominopolitan will add one for you.

- **More Important**: If you DO have a FormHelper in your form class, be aware that `mixins._apply_crispy_helper()` will override your settings for `form_tag` and `disable_csrf`, **even if you have set them explicitly**

    - If you need to retain the default FormHelper settings for `form_tag` and `disable_csrf`, override the `_apply_crispy_helper()` method:

    ```python
    class MyClassName(NominopolitanMixin, CRUDView):
        def _apply_crispy_helper(self, form_class):
            # Either skip the parent method entirely:
            return form_class
            
            # Or call it but then restore your settings:
            form_class = super()._apply_crispy_helper(form_class)
            # Then in the __init__ method, restore your preferred settings:
            old_init = form_class.__init__
            def new_init(self, *args, **kwargs):
                old_init(self, *args, **kwargs)
                self.helper.form_tag = True      # If you want crispy to generate the form tag
                self.helper.disable_csrf = False # If you want crispy to add the CSRF token
            form_class.__init__ = new_init
            return form_class
    ```

**Additional Buttons**
- Support for `extra_actions` to add additional actions for each record to list views
    - `action_button_classes` parameter allows you to add additional button classes (to the base specified in `get_framework_styles`) and control how extra_actions (ie per-record) buttons appear
- Support for `extra_buttons` to add additional buttons to the list view, applicable across records
    - `extra_button_classes` parameter allows you to add additional button classes (to the base specified for each button in `object_list.html` adn well as for each extra button in `extra_buttons`). 

**Styled Table Options**
- set `table_classes` as a parameter and add additional table classes (the base is `table` in `partials/list.html`)
    - eg `table_classes = 'table-zebra table-sm'`
- set `table_max_col_width` as a parameter, measured in `ch` (ie number of `0` characters in the current font). 
    - eg `table_max_col_width = 25` (default = 25, set in `get_table_max_col_width()`) 
    - limit the width of the column to these characters and truncate the data text if needed.
    - if a field is truncated, a popover will be shown with the full text (**requires [`popper.js`](https://popper.js.org/docs/v2/) be installed**)
- set `table_header_min_wrap_width` as a parameter, measured in `ch` (ie number of `0` characters in the current font). 
    - eg `table_header_min_wrap_width = 15` (default = `get_table_max_col_width()`, set in `get_table_header_min_wrap_width()`)
    - if a table column header needs to wrap, then:
        - if the column width based on data elements is < this value then the column width will be set to `table_header_min_wrap_width`
        - if the column width based on data elements is > this value (which be capped by `table_max_col_width`) then the column width will stay at that value
    - Basically just think about say a 4-char wide column with a really long name: its title will wrap at whatever you've set for `table_header_min_wrap_width`
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
- current `list.html` template will display hero icons (SVG) to indicate sorting direction. No install needed.
- if filter options are set, the returned queryset will be sorted and filters
    - *current issue where if filters are displayed and you sort, the filters are hidden; just redisplay them with the button*

**`sample` App**
- `sample` app is a simple example of how to use `django_nominopolitan`. It's available in the repository and not part of the package.
- it includes management commands `create_sample_data` and `delete_sample_data`

**Management Commands**

- `nm_extract_tailwind_classes`:
    - Extracts all Tailwind CSS class names used in your templates and Python files
    - Useful for generating a safelist of classes that Tailwind should not purge during build
    - Scans both HTML templates and Python files for class="..." patterns
    - IMPORTANT: Requires output location to be specified via either:
        - `NM_TAILWIND_SAFELIST_JSON_LOC` in Django settings (recommended), or
        - `--output` command line parameter
    - Basic syntax:
        ```bash
        python manage.py nm_extract_tailwind_classes [options]
        ```
    - Options:
        ```bash
        --pretty          # Print the output in a formatted, readable way
        --output PATH     # Specify custom output path (relative or absolute)
                         # If directory is specified, nominopolitan_tailwind_safelist.json will be created inside it
                         # Examples:
                         #   --output ./config            # Creates ./config/nominopolitan_tailwind_safelist.json
                         #   --output config/safelist.json # Uses exact filename
        ```
    - Output location priority:
        1. Custom path if `--output` is specified
           - If directory: creates nominopolitan_tailwind_safelist.json inside it
           - If file path: uses exact path
        2. Location specified in `NM_TAILWIND_SAFELIST_JSON_LOC` setting (relative to BASE_DIR)
        3. Raises an error if neither location is specified
    - The generated safelist file can be used in your `tailwind.config.js`:
        ```javascript
        //tailwind.config.js
        module.exports = {
          content: [
            // ... your content paths
          ],
          safelist: require('./nominopolitan_tailwind_safelist.json')
        }
        ```

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
# Required settings
INSTALLED_APPS = [
    ...
    "nominopolitan",
    "neapolitan",
    "django_htmx",    # if using htmx features
    ...
]

# Optional: Configure Tailwind safelist location (relative to BASE_DIR)
# Example: if BASE_DIR = '/home/user/myproject'
NM_TAILWIND_SAFELIST_JSON_LOC = 'config/templates/nominopolitan/'  
# This will create: /home/user/myproject/config/templates/nominopolitan/nominopolitan_tailwind_safelist.json
# when the management command ./manage.oy 

# Important: After adding the setting, you must manually run the following command
# to extract Tailwind classes from your templates and prevent them from being purged:
python manage.py nm_extract_tailwind_classes --pretty

# Note: This command requires either:
# 1. The NM_TAILWIND_SAFELIST_JSON_LOC setting above, or
# 2. The --output parameter
# See the "Management Commands" section below for detailed usage and options.
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
    table_max_col_width = '25' # expressed as `ch` (characters wide)

    table_classes = 'table-sm'
    action_button_classes = 'btn-sm'
    extra_button_classes = 'btn-sm'

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
            "display_modal": True,         # if the button should display a modal.
                # Note: modal will auto-close after any form submission
                # Note: if True then htmx_target is ignored
            "needs_pk": True,              # if the URL needs the object's primary key

            # extra class attributes will override automatically determined class attrs if duplicated
            "extra_class_attrs": "rounded-pill border border-dark", 
        },
        # below example if want to use own modal not nominopolitan's
        {
            "url_name": "fstp:home",
            "text": "Home in Own Modal!",
            "button_class": "btn-danger",
            "htmx_target": "myModalContent",
            "display_modal": False, # NB if True then htmx_target is ignored
            "extra_class_attrs": "rounded-circle ",

            # extra_attrs will override other attributes if duplicated
            "extra_attrs": "data-bs-toggle='modal' data-bs-target='#modal-home'",
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
