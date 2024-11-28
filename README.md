# Nominopolitan

This is an opinionated extension package for the excellent [`neapolitan`](https://github.com/carltongibson/neapolitan/tree/main) package. It adds these features:

- Namespaced URL handling
- Display related field name (using `str()`) in lists and details (instead of numeric id)
- Support `@property` values in list view
- Separate create form if `create_form_class` specified
- Support for `crispy-forms` if installed in project
- Support for rendering templates using `htmx`
- Support for modal display of CRUD view actions (requires `htmx` and Alpine)
- Allow specification of `base_template_path` (to your `base.html` template)
- Allow override of all `nominopolitan` templates by specifying `templates_path`
- Support for `extra_actions` to add additional actions to list views
- Styled using `bulma` (I know, it would be better with `tailwind` - let me know if you want to help)
- Header title context for partial updates (so the title is updated without a page reload)
- Management command `nm_mktemplate` to copy required `nominopolitan` template (analagous to `neapolitan`'s `mktemplate`)
- FYI it uses `django-template-partials` under the hood.

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
        "name", "project_owner", "project_manager", "due_date", "description",
        ]

    form_class = forms.ProjectForm # standard neapolitan setting if needed
    # ...other standard neapolitan attributes
    # ******************************************************************
    # nominopolitan attributes

    namespace = "my_app_name" # specify the namespace 
        # if your urls.py has app_name = "my_app_name"

    create_form_class = forms.ProjectCreateForm # if you want a separate create form
        # the update form always uses form_class

    properties = ["is_overdue",] # if you want to include @property fields in the list view

    use_crispy = True # will default to True if you have `crispy-forms` installed
        # if you set it to True without crispy-forms installed, it will resolve to False
        # if you set it to False with crispy-forms installed, it will resolve to False

    base_template_path = "core/base.html" # defaults to inbuilt "nominopolitan/base.html"
    templates_path = "neapolitan" # if you want to override all the templates in another app
        # including one of your own apps; eg templates_path = "my_app_name/nominopolitan" 
        # and then place in my_app_name/templates/my_app_name/nominopolitan

    use_htmx = True # if you want the View, Detail, Delete and Create forms to use htmx
        # if you do not set use_modal = True, the CRUD templates will be rendered to the
        # hx-target used for the list view
        # Requires:
            # htmx installed in your base template
            # django_htmx installed and configured in your settings

    use_modal = True #If you want to use the modal specified in object_list.html for all action links.
        # This will target the modal (id="modalContent") specified in object_list.html
        # Requires:
            # use_htmx = True
            # Alpine installed in your base template
            # htmx installed in your base template
            # django_htmx installed and configured in your settings

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
        },
    ]
```

### nm_mktemplate management command

This is the same as `neapolitan`'s `mktemplate` command except it copies from the `nominopolitan` templates instead of the `neapolitan` templates.

It's the same syntax as `neapolitan`'s `mktemplate` command:

`python manage.py nm_mktemplate <app_name>.<model_name> --<suffix>`

## Status

Extremely early alpha. No tests. Limited docs. Suggest at this stage just use it as a reference and take what you need. It works for me.
