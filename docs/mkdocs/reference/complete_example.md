# 'Kitchen Sink' Example Class Definition

Below is an example of a class definition for a CRUD view with an unrealistic number of parameters, to illustrate syntax.


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

