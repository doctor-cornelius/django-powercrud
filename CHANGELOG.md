## 0.2.27 (2025-07-28)

### Fix

- **(bulk_edit_process_post)**:  clear session of selected_ids after successful delete
- **(object_list)**:  add handlers for hx-triggers refreshTable and bulkEditSuccess
- **(form_mixin)**:  ensure _apply_widget_classes method is applied properly for form opens
- **(bulk_edit_process)**:  correct location of template file
- **(sessions)**:  fix bugs in previous backend work
- **(sessions)**:  revert to complete first draft of tasks 1 & 2
- **(object_confirm_delete)**:  fix behavkiour for async conflict detection
- **(pcrud_help)**:  add docs url
- **(pagination)**:  ensure page change persists existing filter, sort and pagination params

### Refactor

- **(various)**:  remove log.debug statements
- **(sessions)**:  partial incorrect implementation of task 4
- **(bulk_mixin)**:  complete first draft of tasks 1 and 2
- **(config)**:  refactor to support rename of django_powercrud to config directory
- **(sample)**:  move templates and home view to sample app
- **(bulk)**:  extract required info from request so not required in _perform_bulk_update
- **(bulk)**:  separate delete and update into separate methods called by bulk_edit_process_post
- **(mixins)**:  simplify mixins as a package with component feature mixins

### Build

- **(docker)**:  dockerize project to allow postgres, redis for full async testing

### Continuous Integration

- **(new_release.sh)**:  remove requirement to be inside poetry shell since now in docker

### Documentation

- **(bulk_operations.md)**:  explain re setting DATA_UPLOAD_MAX_NUMBER_FIELDS
- **(sample_app.md)**:  update docs on create_sample_data mgmt command
- **(blog)**:  document current 405 problem with toggles
- **(sessions)**:  revise plan and document it for simpler approach
- **(sessions)**:  finalise task list for sessions refactor
- **(sessions)**:  write blog post plan for using django sessions
- **(mkdocs)**:  add link to docs site on github pages
- **(mkdocs)**:  move docs from readme to mkdocs

### Feature

- **(async)**:  provide modal response to user on async queue success or failure
- **(sample.create_sample_data)**:  allow --books-per-author and use faker for unlimited
- **(BulkActions)**:  implement BulkActions enum for url routing of bulk toggle actions

### Style

- **(object_list)**:  restyle bulk buttons and make them smaller
- **(form_mixin)**:  remove css style blocks from templates & use tailwind classes

## 0.2.26 (2025-07-05)

### Fix

- **(object_list)**:  prevent adding null params to get url

## 0.2.25 (2025-07-05)

### Feature

- **(dropdown_sort_options)**:  implement param to sort related objects asc or desc by specified field name for filters, bulk & single edit

## 0.2.24 (2025-07-05)

### Fix

- **(bulk_edit)**:  ensure refresh table after bulk delete

### Feature

- **(bulk delete)**:  allow bulk edit and/or bulk delete (or neither) with new bulk_delete param

## 0.2.23 (2025-07-05)

### Fix

- **(bulk_edit)**:  add choices for fields with choices to _get_bulk_field_info

## 0.2.22 (2025-07-04)

### Fix

- **(bulk edit)**:  fix processing of m2m fields

## 0.2.21 (2025-07-04)

### Feature

- **(pagination)**:  enable user page size selection which persists after edits

## 0.2.20 (2025-07-03)

### Documentation

- **(README.md)**:  improve documentation of override method for get_bulk_choice_for_field

### Feature

- **(sample)**:  add Profile and ProfileCRUDView to test OneToOneField bulk edit
- **(bulk_edit_form)**:  add logic to also handle OneToOneFields

### Style

- **(list.html)**:  set checkbox all for bulk edit to have white border

## 0.2.19 (2025-07-03)

### Refactor

- **(get_bulk_choices_for_field)**:  separate out method for extracting choices for foreign key fields, to allow easier override

## 0.2.18 (2025-07-03)

### Fix

- **(targeting)**:  fix htmx targeting and table refresh after (bulk) edit save to preserve filter and sort params

## 0.2.17 (2025-07-01)

### Fix

- **(bulk_edit)**:  fix foreign key record update and document bulk edit functionality

### Feature

- **(bulk_edit)**:  add bulk edit functionality with atomic rollback on failure

## 0.2.16 (2025-05-22)

### Refactor

- **(object_list): change htmx**: afterSwap listener to add event
- **(render_to_response)**:  assuem hx trigger is always json format
- **(get_hx_trigger)**:  always return json formatted triggers

## 0.2.15 (2025-05-22)

### Style

- **(object_form)**:  do not set push-url if using modal
- **(object_confirm_delete)**:  change colour of text

## 0.2.14 (2025-05-22)

### Refactor

- **(Genre)**:  fix logic and method in clean()
- **(Genre)**:  add test field

### Style

- **(PowerCRUD)**:  make modal based form errors appear in modal not template body

## 0.2.13 (2025-05-21)

### Refactor

- **(mixins)**:  comment out debug statements

### Documentation

- **(README)**:  document correct way to use @source instead of management command

### Style

- **(object_list)**:  ensure css styles have loaded before tooltips are initialised

## 0.2.12 (2025-05-10)

### Build

- **(tailwind)**:  explicitly include crispy_tailwind from .venv using @source

## 0.2.11 (2025-05-08)

### Documentation

- **(README.md)**:  document how mixins._apply_crispy_helper() works

## 0.2.10 (2025-05-08)

### Feature

- **ure(get_form_class)**:  add FormHelper to form class if not already there; drop create_form_class option

## 0.2.9 (2025-05-07)

## 0.2.8 (2025-05-06)

### Refactor

- **(pcrud_extract_tailwind_classes)**:  use generated css file instead of simulating

## 0.2.7 (2025-05-06)

### Build

- **(vite)**:  set env vars before running npm for new release

## 0.2.6 (2025-05-06)

### Refactor

- **(crispy)**:  use crispy_daisyui (not working)
- **(crispy)**:  use crispy_daisyui instead (makes no difference)

### Build

- **(vite)**:  switch to vite instead of webpack

## 0.2.5 (2025-05-04)

### Feature

- **(object_detail)**:  support property.fget.short_description for column header if it exists

## 0.2.4 (2025-05-03)

### Style

- **(delete)**:  restyle the delete confirmation template

## 0.2.3 (2025-04-21)

### Refactor

- **(object_list)**:  remove unnecessary js given recent fix in backend

### Feature

- **(PowerCRUDMixin)**:  amend get_queryset and add override paginate_queryset to allow filters and pagination to coexist

### Style

- **(object_list)**:  refactor javascript to remove redundant functions
- **(object_list)**:  add js to reset pagination when filter changes

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

- **(powercrud.py)**:  add in missing models import from django.db

## 0.1.40 (2025-04-09)

### Feature

- **(PowerCRUDMixin, powercrud.py)**:  handle M2M fields in object list, forms and filtersets

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

- **(pcrud_extract_tailwind_classes)**:  include json and text files in scan

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

- **(post_install)**:  add post_install script to package to run pcrud_extract_tailwind_classes

## 0.1.31 (2025-04-02)

### Fix

- **(pcrud_extract_tailwind_classes)**:  make --pretty option also save in pretty format

## 0.1.30 (2025-04-02)

### Refactor

- **(pcrud_extract_tailwind_classes)**:  change default filename to PowerCRUD_tailwind_safelist.json

## 0.1.29 (2025-04-02)

### Feature

- **(pcrud_extract_tailwind_classes)**:  allow options --output and --package-dir to set file save destination

## 0.1.28 (2025-04-02)

### Refactor

- **(pcrud_extract_tailwind_classes)**:  save file in non-pretty format and allow print of file in normal or --pretty format

## 0.1.27 (2025-04-02)

### Documentation

- **(new_release.sh)**:  add comment

### Feature

- **(pcrud_extract_tailwind_classes)**:  create management command to extract classes for downstream to include in safelist

## 0.1.26 (2025-04-02)

### Build

- **(webpoack.config.js)**:  add minimisers
- **(webpack)**:  use webpack

### Feature

- **(pcrud_generate_tailwind_config)**:  write mgmt command to identify locations of files with tw classes

## 0.1.25 (2025-04-01)

### Feature

- **(django_powercrud)**:  add parameters table_classes, action_button_classes, extra_button_classes and drop table_font_size

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

- **(pcrud_help)**:  include README.md in package so it can be read when imported

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

- **(pcrud_mktemplate)**:  enhance management command options with app_name --all and app_name.model --all

## 0.1.14 (2025-03-10)

### Refactor

- **(sample)**:  set form_class for Book but not for Author

### Documentation

- **(README)**:  update docs re form_fields and form_fields_exclude attributes
- **(get_form_class)**:  write code comments to improve maintainability
- **(README)**:  update docs re url_base

## 0.1.13 (2025-03-10)

### Fix

- **(render_to_response)**:  change all template partial names to pcrud_content and specify in response logic

### Refactor

- **(refactor session key to single 'PowerCRUD' session key)**: 

## 0.1.12 (2025-03-10)

### Fix

- **(list.html)**:  apply sort logic to th header not just the <a> tag with header text

## 0.1.11 (2025-03-09)

### Fix

- **(sort)**:  maintain selected filter display when sorting with htmx

## 0.1.10 (2025-03-09)

### Fix

- **(pypoetry)**:  correct extras syntax
- **(PowerCRUDMixinValidator)**:  remove defaults from validator class and set custom validator for hx_trigger

### Build

- **(pypoetry)**:  change extras

### Documentation

- **(README)**:  update installation section

## 0.1.9 (2025-03-09)

### Feature

- **(PowerCRUDMixin)**:  validate all class attributes with pydantic PowerCRUDMixinValidator

## 0.1.8 (2025-03-07)

### Fix

- **(list.html)**:  make sort click on header not just header text

### Documentation

- **(README)**:  update re pcrud_help
- **(pcrud_help)**:  create management command to display README.md
- **(README)**:  add url for popper.js installation instructions page

### Feature

- **(list.html)**:  enable sort to apply any selected filters to returned data set

## 0.1.7 (2025-03-06)

### Feature

- **(django_powercrud)**:  add new parameters to calculate max-table-height css parameter in list.html

## 0.1.6 (2025-03-06)

### Documentation

- **(README)**:  update docs re pcrud_clear_session_keys

### Feature

- **(pcrud_clear_session_keys)**:   add management command to clear PowerCRUD session keys

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

- **(django_powercrud)**:  enable sort toggle on object list

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

- **(modal_id)**:  allow override of default modal_id 'powercrudBaseModal'

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

- **(PowerCRUD)**:  support hx_trigger as value to pass as response['HX-Trigger'] with every response

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

- **(PowerCRUD)**:  exclude non-editable fields from forms if no form_class is specified

## 0.0.20 (2024-12-05)

### Feature

- **(PowerCRUD)**:  add parameters exclude, properties_exclude, detail_exclude, detail_properties_exclude

## 0.0.19 (2024-12-04)

### Style

- **(PowerCRUD)**:  use template tag get_proper_elided_page_range for pagination list

## 0.0.18 (2024-12-04)

### Feature

- **(PowerCRUD)**:  add htmx pagination for object list template

## 0.0.17 (2024-12-04)

### Fix

- **(PowerCRUD)**:  add htmx directives to object_confirm_delete template form
- **(PowerCRUD)**:  add delete_view_url context variable and fix modal delete not working

### Style

- **(PowerCRUD)**:  remove debug paragraph in object_confirm_delete.html

## 0.0.16 (2024-12-03)

### Refactor

- **(PowerCRUD)**:  change parameters for fields, properties, detail_fields, detail_properties

## 0.0.15 (2024-12-03)

### Feature

- **(PowerCRUD)**:  Support fields or properties = 'all'; support detail_fields, detail_properties
- **(support fields = 'all' and properties = 'all')**: 

## 0.0.14 (2024-12-02)

### Refactor

- **(django-PowerCRUD)**:  prefix all modal names with PowerCRUD

### Build

- **(tornado)**:  poetry update tornado

### Documentation

- **(README)**:  update and correct instructions
- **(update README with all current features)**: 

## 0.0.13 (2024-11-27)

### Fix

- **(PowerCRUD)**:  fix problem where non-htmx call initiated list for view where use_htmx is True

### Refactor

- **(PowerCRUD)**:  remove debug statement

### Feature

- **(PowerCRUD)**:  Allow hx-post parameter on extra_actions

## 0.0.12 (2024-11-27)

### Fix

- **(PowerCRUD)**:  use elif in get_htmx_target to ensure non-htmx target is None not "#None"

## 0.0.11 (2024-11-27)

### Refactor

- **(PowerCRUD)**:  put object_list modal inside #content partial

## 0.0.10 (2024-11-27)

### Style

- **(PowerCRUD)**:  remove stray > from object_form template

## 0.0.9 (2024-11-27)

### Fix

- **(PowerCRUD)**:  get_success_url now correctly targets original hx-target of the list view if used
- **(PowerCRUD)**:  get update_view_url correctly into context
- **(sample)**:  correct date widgets in forms
- **(PowerCRUD)**:  fix up when to prepend # to htmx_target

### Documentation

- **(PowerCRUD)**:  update docs with minimal detail on use_modal

### Feature

- **(PowerCRUD)**:  implement use_modal functionality for CRUD and other actions

### Style

- **(PowerCRUD)**:  style modal close X
- **(sample)**:  load template builtins to save having to load tags each time

## 0.0.8 (2024-11-26)

### Refactor

- **(PowerCRUD)**:  remove debug statement

### Feature

- **(PowerCRUD)**:  style action links as small buttons and allow extra_buttons to be specified
- **(NominoPolitanMixin)**:  Allow specification of new actions

### Style

- **(modal)**:  add modal partial to object_list with no trigger yet to open

## 0.0.7 (2024-11-22)

### Documentation

- **(README)**:  minimally document pcrud_mktemplate command

### Feature

- **(pcrud_mktemplate)**:  pcrud_mktemplate to make copy of PowerCRUD templates using same syntax as mktemplate

## 0.0.6 (2024-11-22)

### Refactor

- **(PowerCRUDMixin)**:  set context for htmx_target in get_context_data

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

- **(PowerCRUDMixin)**:  add logic for use of crispy forms depending on whether installed or overridden via use_crispy

## 0.0.1 (2024-11-20)

### Build

- **(ci)**:  change pypi token name
- **(ci)**:  set up for pypi
- **(ci)**:  add release action to github actions

### Feature

- **(PowerCRUD)**:  allow parameterisation of use_crispy
- **(PowerCRUD)**:  Initial Commit
