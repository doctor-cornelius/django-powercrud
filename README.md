# Nominopolitan

This is an opinionated extension package for the excellent [`neapolitan`](https://github.com/carltongibson/neapolitan/tree/main) package. It adds these features:

- Namespaced URL handling
- Display related field str() value in lists and details (instead of numeric id)
- Property fields in list views
- Separate create form class if specified
- Support for `crispy-forms` if installed in project
- Support for rendering templates using `htmx`
- Header title context for partial updates (so the title is updated without a page reload)
- Allow specification of `base_template_path` (to your `base.html` template)
- Allow override of all `nominopolitan` templates by specifying `templates_path`

At the moment the templates are styled using Bulma. I aim to also support the native `neapolitan` templates in a future release. FYI it uses `django-template-partials` under the hood. 

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

## Usage

The best starting point is [`neapolitan`'s docs](https://noumenal.es/neapolitan/). The basic idea is to specify model-based CRUD views using:

```python
# neapolitan approach
class ProjectView(CRUDView):
    model = projects.models.Project
    fields = ["name", "owner", "last_review", "has_tests", "has_docs", "status"]
```

The `nominopolitan` mixin adds a number of features to this.

```python
from nominopolitan.mixins import NominopolitanMixin
from neapolitan.views import CRUDView

class ProjectCRUDView(NominopolitanMixin, CRUDView):
    model = models.Project
    fields = [
        "name", "owner", "last_review", "has_tests", "has_docs", "status",
        ]
    form_class = forms.ProjectUpdateForm # standard neapolitan setting if needed
    # ...other standard neapolitan attributes

    namespace = "my_app_name" # specify the namespace if your urls.py has app_name = "my_app_name"

    properties = ["selected_scenario",] # if you want to include @property fields in the list view

    use_crispy = True # will default to True if you have `crispy-forms` installed
        # if you set it to True without crispy-forms installed, it will resolve to False

    create_form_class = forms.TenderCreateForm # if you want a separate create form
        # the update form always uses form_class

    base_template_path = "core/base_with_nav.html" # optional, defaults to "nominopolitan/base.html"
    templates_path = "neapolitan" # if you want to override all the templates in another app

    use_htmx = True # if you want the View, Detail, Delete and Create forms to use htmx
        # you must have `htmx` installed in your base template
        # Will only work if use_htmx is True AND you call the list view using htmx
        # in which case these templates will be returned to the same hx-target as used for the list view
```

## Status

Extremely early alpha. No tests. Limited docs. Suggest at this stage just use it as a reference and take what you need. It works for me.
