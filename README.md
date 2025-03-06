# Nominopolitan

This is an opinionated extension package for the excellent [`neapolitan`](https://github.com/carltongibson/neapolitan/tree/main) package. It adds these features:

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
- `detail_fields` and `detail_properties` to specify which to include in detail view
- Support exclusions via `exclude`, `exclude_properties`, `detail_exclude`, `detail_exclude_properties`
- Support for `extra_actions` to add additional actions to list views

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
- if `form_class` is not specified, then non-editable fields are automatically excluded from forms
- Optional `create_form_class` for create operations:
    - Allows a separate form class specifically for create views
    - Useful when create and update forms need different: Field sets, Validation logic, Base classes
    - Falls back to `form_class` if not specified
- Support for `crispy-forms` if installed in project and `use_crispy` parameter is not `False`
    - make sure you have `crispy_bootstrap5` also installed if you want
    - if you have set up a different library use the correct crispy package (eg `crispy_bulma`, `crispy_tailwind`)

**Styled Table Options**
- set `table_font_size` as a parameter, measured in `rem`. eg `table_font_size = 0.875`. This will be applied to buttons, filters and the table data itself using the custom style in `object_list.html`: `.table-font-size {font-size: {{ table_font_size }};}`.
- set `table_max_col_width` as a parameter, measured in `ch` (ie number of `0` characters in the current font). eg `table_max_col_width = 10`: 
    - limit the width of the column to these characters and truncate the data text if needed.
    - if a field is truncated, a popover will be shown with the full text (**requires `popper.js` be installed**)
    - column headers will be wrapped to the width of the column (as determined by width of data items)

**Table Sorting**
- click table header to toggle sorting direction (columns start off unsorted)
- the method always includes a secondary sort by primary key for stable pagination
- will use `htmx` if `use_htmx is True`
- current `list.html` template will display bootstrap icons (if installed) for sorting direction:
    - you must [install bootstrap icons](https://getbootstrap.com/docs/5.3/getting-started/introduction/#cdn-links) to use this feature

**`sample` App**
- `sample` app is a simple example of how to use `django_nominopolitan`. It's available in the repository and not part of the package.
- it includes management commands `create_sample_data` and `delete_sample_data`

This is a **very early alpha** release; expect many breaking changes. You might prefer to just fork or copy and use whatever you need. Hopefully some or all of these features may make their way into `neapolitan` over time.

## Installation

With `pip`:
`pip install django-nominopolitan`

Poetry:
`poetry add django-nominopolitan`

## Configuration
Add these to your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "nominopolitan", # put this before neapolitan
    "neapolitan",    # this is required to use the `NominopolitanMixin`
    ...
]
```

In addition:

1. If you want to set `use_htmx = True`, then make sure `htmx` is installed in your base template and `django_htmx` is installed.
2. If you want to set `use_modal = True`, it requires `use_htmx=True` (see above) **and** `alpinejs` is installed in your base template.

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
    model = models.Project
    fields = [
        "name", "project_owner", "project_manager", "due_date",
        ]

    form_class = forms.ProjectForm # standard neapolitan setting if needed
    # ...other standard neapolitan attributes
    # ******************************************************************
    # nominopolitan attributes

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

    namespace = "my_app_name" # specify the namespace 
        # if your urls.py has app_name = "my_app_name"

    create_form_class = forms.ProjectCreateForm # if you want a separate create form
        # the update form always uses form_class


    use_crispy = True # will default to True if you have `crispy-forms` installed
        # if you set it to True without crispy-forms installed, it will resolve to False
        # if you set it to False with crispy-forms installed, it will resolve to False

    base_template_path = "core/base.html" # defaults to inbuilt "nominopolitan/base.html"
    templates_path = "myapp" # if you want to override all the templates in another app
        # or include one of your own apps; eg templates_path = "my_app_name/nominopolitan" 
        # and then place in my_app_name/templates/my_app_name/nominopolitan

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

    extra_actions = [ # adds additional actions for each record in the list
        {
            "url_name": "fstp:do_something",  # namespace:url_pattern
            "text": "Do Something",
            "needs_pk": False,  # if the URL needs the object's primary key
            "hx_post": True, # use POST request instead of the default GET
            "button_class": "is-primary", # semantic colour for button (defaults to "is-link")
            "htmx_target": "content", # htmx target for the extra action response 
                # (if use_htmx is True)
                # NB if you have use_modal = True and do NOT specify htmx_target, then response
                # will be directed to the modal 
            "display_modal": False, # when use_modal is True but for this action you do not
                # want to use the modal for whatever is returned from the view, set this to False
                # the default if empty is True
        },
    ]
```

### Management Commands

#### `nm_mktemplate` management command

- This is the same as `neapolitan`'s `mktemplate` command except it copies from the `nominopolitan` templates instead of the `neapolitan` templates.
- It's the same syntax as `neapolitan`'s `mktemplate` command:

`python manage.py nm_mktemplate <app_name>.<model_name> --<suffix>`

#### `nm_clear_session_keys` management command

- Used to clear all user session keys related to nominopolitan 

## Status

Extremely early alpha. No tests. Limited docs. Suggest at this stage just use it as a reference and take what you need. It works for me.
