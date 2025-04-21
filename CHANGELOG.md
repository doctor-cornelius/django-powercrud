## 0.2.2 (2025-04-21)

### Style

- **(object_list)**:  adjust padding to separate filters from table

## 0.2.1 (2025-04-21)

## 0.2.0 (2025-04-21)

### Fix

- **(get_filter_queryset_for_field)**:  make method more robust with filter and sort options

### Style

- **(object_list)**:  completely restyle filterset elements in template and get_framework_styles

## 0.1.43 (2025-04-15)

## 0.1.42 (2025-04-15)

### Fix

- **(object_list)**:  guartd against non-existent filter in initializeFilterToggle

## 0.1.41 (2025-04-14)

### Fix

- **(nominopolitan.py)**:  add in missing models import from django.db

## 0.1.40 (2025-04-09)

### Feature

- **(NominopolitanMixin, nominopolitan.py)**:  handle M2M fields in object list, forms and filtersets

## 0.1.39 (2025-04-08)

### Fix

- **(object_list)**:  remove debug paragraph

### Refactor

- **(Author)**:  set table column width parameters

## 0.1.38 (2025-04-08)

### Style

- **(object_list)**:  apply styling for boolean and date, date fields also for properties
- **(object_list)**:  use svg for boolean fields
- **(table_header_min_wrap_width)**:  support parameter for minimum wrap point for table headers

## 0.1.37 (2025-04-07)

### Fix

- **(list)**:  make properties not sortable

### Refactor

- **(Book)**:  add property with very long header name

### Style

- **(object_list)**:  improve css for header wrapping
- **(object_detail)**:  use text-primary-content not !text-primary-content for header

## 0.1.36 (2025-04-07)

### Style

- **(modal)**:  remove modal header and format individual form header text colours
-  improve formatting
- **(object_form)**:  make heading bold

## 0.1.35 (2025-04-04)

### Fix

- **(nm_extract_tailwind_classes)**:  include json and text files in scan

## 0.1.34 (2025-04-04)

### Documentation

- **(README.md)**:  document tailwindcss considerations

### Style

- **(crispy_tailwind_safelist.json)**:  add json file with safelist of all the class names in crispy_tailwind that I could find

## 0.1.33 (2025-04-02)

### Refactor

- **(remove post-install because package manager does not support such things)**: 

## 0.1.32 (2025-04-02)

### Refactor

- **(post_install)**:  add post_install script to package to run nm_extract_tailwind_classes

## 0.1.31 (2025-04-02)

### Fix

- **(nm_extract_tailwind_classes)**:  make --pretty option also save in pretty format

## 0.1.30 (2025-04-02)

### Refactor

- **(nm_extract_tailwind_classes)**:  change default filename to nominopolitan_tailwind_safelist.json

## 0.1.29 (2025-04-02)

### Feature

- **(nm_extract_tailwind_classes)**:  allow options --output and --package-dir to set file save destination

## 0.1.28 (2025-04-02)

### Refactor

- **(nm_extract_tailwind_classes)**:  save file in non-pretty format and allow print of file in normal or --pretty format

## 0.1.27 (2025-04-02)

### Documentation

- **(new_release.sh)**:  add comment

### Feature

- **(nm_extract_tailwind_classes)**:  create management command to extract classes for downstream to include in safelist

## 0.1.26 (2025-04-02)

### Build

- **(webpoack.config.js)**:  add minimisers
- **(webpack)**:  use webpack

### Feature

- **(nm_generate_tailwind_config)**:  write mgmt command to identify locations of files with tw classes

## 0.1.25 (2025-04-01)

### Feature

- **(django_nominopolitan)**:  add parameters table_classes, action_button_classes, extra_button_classes and drop table_font_size

## 0.1.24 (2025-03-31)

### Fix

- **(new_release.sh)**:  ensure correct path to static css files

## 0.1.23 (2025-03-31)

### Fix

- **(new_release.sh)**:  ensure production css files built via npx

### Feature

- **(daisy)**:  add daisyUI framework capability and templates

## 0.1.22 (2025-03-19)

### Feature

- **(render_to_response)**:  add original_template to session data, retrievable via template tag or get_session_data_key('original_target')

## 0.1.21 (2025-03-18)

### Refactor

- **(extra_buttons)**:  put extra_attrs and extra_class attrs first so they override calculated attributes

## 0.1.20 (2025-03-18)

### Fix

- **(extra_buttons)**:  set extra_attrs as last added to buttons

## 0.1.19 (2025-03-18)

### Fix

- **(extra_buttons)**:  fix logic for setting htmx_target

## 0.1.18 (2025-03-18)

### Feature

- **(extra_buttons)**:  add support for extra_attrs (eg if want to use own modal)

## 0.1.17 (2025-03-18)

### Fix

- **(nm_help)**:  include README.md in package so it can be read when imported

### Refactor

- **(extra_buttons)**:  disregard htmx_target if display_modal is True

### Feature

- **(extra_buttons)**:  support parameter extra_class_attrs

## 0.1.16 (2025-03-14)

### Feature

- **(extra_buttons)**:  allow extra buttons to be implemented next to Create button via class attribute

## 0.1.15 (2025-03-10)

### Refactor

- **(object_form)**:  use framework_template_path context var for relative include of crispy forms
- **(render_to_response)**:  change logic to pick up overridden forms

### Feature

- **(nm_mktemplate)**:  enhance management command options with app_name --all and app_name.model --all

## 0.1.14 (2025-03-10)

### Refactor

- **(sample)**:  set form_class for Book but not for Author

### Documentation

- **(README)**:  update docs re form_fields and form_fields_exclude attributes
- **(get_form_class)**:  write code comments to improve maintainability
- **(README)**:  update docs re url_base

## 0.1.13 (2025-03-10)

### Fix

- **(render_to_response)**:  change all template partial names to nm_content and specify in response logic

### Refactor

- **(refactor session key to single 'nominopolitan' session key)**: 

## 0.1.12 (2025-03-10)

### Fix

- **(list.html)**:  apply sort logic to th header not just the <a> tag with header text

## 0.1.11 (2025-03-09)

### Fix

- **(sort)**:  maintain selected filter display when sorting with htmx

## 0.1.10 (2025-03-09)

### Fix

- **(pypoetry)**:  correct extras syntax
- **(NominopolitanMixinValidator)**:  remove defaults from validator class and set custom validator for hx_trigger

### Build

- **(pypoetry)**:  change extras

### Documentation

- **(README)**:  update installation section

## 0.1.9 (2025-03-09)

### Feature

- **(NominopolitanMixin)**:  validate all class attributes with pydantic NominopolitanMixinValidator

## 0.1.8 (2025-03-07)

### Fix

- **(list.html)**:  make sort click on header not just header text

### Documentation

- **(README)**:  update re nm_help
- **(nm_help)**:  create management command to display README.md
- **(README)**:  add url for popper.js installation instructions page

### Feature

- **(list.html)**:  enable sort to apply any selected filters to returned data set

## 0.1.7 (2025-03-06)

### Feature

- **(django_nominopolitan)**:  add new parameters to calculate max-table-height css parameter in list.html

## 0.1.6 (2025-03-06)

### Documentation

- **(README)**:  update docs re nm_clear_session_keys

### Feature

- **(nm_clear_session_keys)**:   add management command to clear nominopolitan session keys

## 0.1.5 (2025-03-06)

### Fix

- **(list.html)**:  use original_target for htmx for header sort when clicked

### Refactor

- **(object_list)**:  remove debug statement

## 0.1.4 (2025-03-06)

### Fix

- **(filtering)**:  fix bug in filtering by setting original htmx target correctly in session variable

## 0.1.3 (2025-03-05)

### Fix

- **(get sorting working with underscored fields and include secondary sort by id for stable pagination)**: 

## 0.1.2 (2025-03-05)

### Feature

- **(django_nominopolitan)**:  enable sort toggle on object list

## 0.1.1 (2025-03-01)

### Refactor

- **(DynamicFilterSet)**:  use icontains for 'else' CharFilter
- **(get_table_font_size)**:  set default to 1rem instead of 0.875rem

### Documentation

- **(README)**:  update docs re ability to override get_filter_queryset_for_field

### Feature

- **(get_filterset_for_field)**:  separate out method for easier override to restrict foreign key fields if needed

## 0.1.0 (2025-02-22)

### Feature

- **(bulma)**:  Remove support for bulma in base package

## 0.0.43 (2025-02-22)

### Documentation

-  add docstrings and type hints

## 0.0.42 (2025-02-19)

### Refactor

- **(mixins)**:  remove debug comments

## 0.0.41 (2025-02-19)

### Feature

- **(filter)**:  toggle display of filter fields

## 0.0.40 (2025-02-19)

### Feature

- **(list)**:  truncate columns based on table_max_col_width and provide tooltips

## 0.0.39 (2025-02-18)

### Feature

- **(get_filterset)**:  accommodate GeneratedField types for filter widget determination

## 0.0.38 (2025-02-18)

### Fix

- **(get_filterset)**:  make all filter field args be applied to filtering

### Refactor

- **(AuthorCRUDView)**:  use filterset class for sample purposes
- **(HTMXFilterSetMixin)**:  apply htmx mixin to sample AuthorFilterSet class
-  update main before merge
- **(get_framework_styles)**:  define css framework styles as method in NominoPolitanMixin

### Feature

- **(object_list)**:  drive font size of table using attribute table_font_size
- **(object_list)**:  place buttons conditionally inline
- **(get_filterset)**:  create dynamic filterset class based on filterset_fields to set htmx triggers

### Style

- **(object_list)**:  style filter and create buttons inline above filter fields

## 0.0.37 (2025-02-17)

### Fix

- **(filters)**:  filters working with htmx only but no non-htmx option. also fonts too large

### Feature

- **(filterset)**:  support filterset_fields with styling or filterset_class, both with htmx attrs as needed
- **(filter)**:  300ms delay works for text filter

### Style

- **(filters)**:  get filter fields in same inline row

## 0.0.36 (2025-02-15)

### Feature

- **(object_list.html)**:  add code to display filterset if exists

### Style

- **(object_list.html)**:  move filter above create button

## 0.0.35 (2025-02-12)

### Style

- **(list.html)**:  add actions header and make table only as wide as needed

## 0.0.34 (2025-02-12)

### Style

- **(list.html)**:  style to more compact tables

## 0.0.33 (2025-02-11)

### Documentation

- **(action_links)**:  comment future option to use hx-disable for simplified logic

### Feature

- **(modal_id)**:  allow override of default modal_id 'nominopolitanBaseModal'

## 0.0.32 (2025-02-10)

### Fix

- **(use_htmx)**:  make logic work for use_htmx and/or use_modal being False

## 0.0.31 (2025-02-10)

### Feature

- **(modal_target)**:  allow custom modal_target

### Style

- **(README)**:  format sub-headings in README

## 0.0.30 (2025-02-04)

### Feature

- **(Nominopolitan)**:  support hx_trigger as value to pass as response['HX-Trigger'] with every response

## 0.0.29 (2025-02-04)

### Documentation

- **(README)**:  update with details of display_modal for extra_actions

### Feature

- **(render_to_response)**:  add hx-trigger messagesChanged to allow trigger of message display in base.html

## 0.0.28 (2025-01-25)

### Feature

- **(modal): allow extra_actions to specify display_modal**:  False

## 0.0.27 (2025-01-25)

### Style

- **(modal)**:  include modal backdrop and js code in object_list.html to remove backdrop on submit

## 0.0.26 (2025-01-25)

### Style

- **(actions)**:  group buttons so they don't stack vertically on smaller displays
- **(AuthorCRUDView)**:  use bootstrap instead of bulma style for extra_action

## 0.0.25 (2025-01-24)

### Fix

- **(modal)**:  remove modal backdrop because it would not close after modal closed

### Style

- **(modal)**:  keep buttons in modal content not mixed across content and footer

## 0.0.24 (2025-01-23)

### Fix

- **(create form)**:  get bootstrap modal working

## 0.0.23 (2025-01-23)

### Build

- **(poetry.locl)**:  run poetry lock

### Continuous Integration

- **(github)**:  add poetry lock command to github actions

### Documentation

- **(README)**:  write up changes in readme

## 0.0.22 (2025-01-23)

### Fix

- **(bootstrap)**:  get bootstrap modal working
-  get modal working ok for bulma

### Refactor

- **(object_list)**:  add z-index to make modal work properly

### Style

- **(bootstrap)**:  add in bootstrap5 option as default
- **(styling)**:  put in framework in templatetags for flexible css framework for fragments

## 0.0.21 (2024-12-05)

### Feature

- **(nominopolitan)**:  exclude non-editable fields from forms if no form_class is specified

## 0.0.20 (2024-12-05)

### Feature

- **(nominopolitan)**:  add parameters exclude, properties_exclude, detail_exclude, detail_properties_exclude

## 0.0.19 (2024-12-04)

### Style

- **(nominopolitan)**:  use template tag get_proper_elided_page_range for pagination list

## 0.0.18 (2024-12-04)

### Feature

- **(nominopolitan)**:  add htmx pagination for object list template

## 0.0.17 (2024-12-04)

### Fix

- **(nominopolitan)**:  add htmx directives to object_confirm_delete template form
- **(nominopolitan)**:  add delete_view_url context variable and fix modal delete not working

### Style

- **(nominopolitan)**:  remove debug paragraph in object_confirm_delete.html

## 0.0.16 (2024-12-03)

### Refactor

- **(nominopolitan)**:  change parameters for fields, properties, detail_fields, detail_properties

## 0.0.15 (2024-12-03)

### Feature

- **(nominopolitan)**:  Support fields or properties = 'all'; support detail_fields, detail_properties
- **(support fields = 'all' and properties = 'all')**: 

## 0.0.14 (2024-12-02)

### Refactor

- **(django-nominopolitan)**:  prefix all modal names with nominopolitan

### Build

- **(tornado)**:  poetry update tornado

### Documentation

- **(README)**:  update and correct instructions
- **(update README with all current features)**: 

## 0.0.13 (2024-11-27)

### Fix

- **(nominopolitan)**:  fix problem where non-htmx call initiated list for view where use_htmx is True

### Refactor

- **(nominopolitan)**:  remove debug statement

### Feature

- **(nominopolitan)**:  Allow hx-post parameter on extra_actions

## 0.0.12 (2024-11-27)

### Fix

- **(nominopolitan)**:  use elif in get_htmx_target to ensure non-htmx target is None not "#None"

## 0.0.11 (2024-11-27)

### Refactor

- **(nominopolitan)**:  put object_list modal inside #content partial

## 0.0.10 (2024-11-27)

### Style

- **(nominopolitan)**:  remove stray > from object_form template

## 0.0.9 (2024-11-27)

### Fix

- **(nominopolitan)**:  get_success_url now correctly targets original hx-target of the list view if used
- **(nominopolitan)**:  get update_view_url correctly into context
- **(sample)**:  correct date widgets in forms
- **(nominopolitan)**:  fix up when to prepend # to htmx_target

### Documentation

- **(nominopolitan)**:  update docs with minimal detail on use_modal

### Feature

- **(nominopolitan)**:  implement use_modal functionality for CRUD and other actions

### Style

- **(nominopolitan)**:  style modal close X
- **(sample)**:  load template builtins to save having to load tags each time

## 0.0.8 (2024-11-26)

### Refactor

- **(nominopolitan)**:  remove debug statement

### Feature

- **(nominopolitan)**:  style action links as small buttons and allow extra_buttons to be specified
- **(NominoPolitanMixin)**:  Allow specification of new actions

### Style

- **(modal)**:  add modal partial to object_list with no trigger yet to open

## 0.0.7 (2024-11-22)

### Documentation

- **(README)**:  minimally document nm_mktemplate command

### Feature

- **(nm_mktemplate)**:  nm_mktemplate to make copy of nominopolitan templates using same syntax as mktemplate

## 0.0.6 (2024-11-22)

### Refactor

- **(NominopolitanMixin)**:  set context for htmx_target in get_context_data

### Documentation

- **(README)**:  update minimal docs re htmx_crud_target

### Feature

- **(NominoPolitanMixin)**:  support new attribute htmx_crud_target to allow separate target from object list
- **(NominoPolitanMixin)**:  get create form working with htmx if use_htmx and htmx_target exists

## 0.0.5 (2024-11-22)

### Fix

- **(action_links)**:  set links conditionally on whether htmx_target exists

## 0.0.4 (2024-11-21)

### Refactor

- **(nominpolitan)**:  remove debug statement

## 0.0.3 (2024-11-20)

### Fix

- **(use_htmx_partials)**:  remove this option as not used

## 0.0.2 (2024-11-20)

### Feature

- **(NominopolitanMixin)**:  add logic for use of crispy forms depending on whether installed or overridden via use_crispy

## 0.0.1 (2024-11-20)

### Build

- **(ci)**:  change pypi token name
- **(ci)**:  set up for pypi
- **(ci)**:  add release action to github actions

### Feature

- **(nominopolitan)**:  allow parameterisation of use_crispy
- **(nominopolitan)**:  Initial Commit
