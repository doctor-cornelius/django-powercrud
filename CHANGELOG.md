## 0.4.14 (2026-02-09)

### Fix

- **(config_mixin)**: put in guard and test for non-async config
- **(deps)**: lock file maintenance js-packages (#61)
- **(deps)**: update js-packages (#38)
- **(deps)**: lock file maintenance js-packages (#54)
- **(deps)**: lock file maintenance js-packages (#52)
- **(deps)**: lock file maintenance js-packages (#50)
- **(deps)**: lock file maintenance js-packages (#47)
- **(deps)**: lock file maintenance js-packages (#45)
- **(deps)**: lock file maintenance js-packages (#42)

## 0.4.13 (2025-11-26)

## 0.4.12 (2025-11-26)

### Fix

- **(FormMixin)**: do guarded import of rcrispy-forms in case not needed
- **(conf.py)**: do not require presence of settings.POWERCRUD_SETTINGS

## 0.4.11 (2025-11-26)

### Refactor

- **(ConfigMixin)**: consolidate config params, validation and resolution in ConfigMixin

### Documentation

- **(async)**: write plan to fix async guards
- **(templatePacks)**: finalise plan for new templatePack modularisation

### Feature

- **(PowerCRUDAsyncMixin)**: split AsyncMixin out from PowerCRUDMixin and include in new PowerCRUDAsyncMixin

## 0.4.10 (2025-11-15)

### Documentation

- **(README)**: use correct url for ci tests badge [skip tests]

### Feature

- **(InlineEditingMixin)**: add feature to inject missing required fields as hidden form fields

## 0.4.9 (2025-11-15)

## 0.4.8 (2025-11-15)

## 0.4.7 (2025-11-15)

### Fix

- **(sample.BookCRUDView)**: add expected fields to form_fields
- **(sample.BookCRUDView)**: remove author and genre unused methods
- **(deps)**: lock file maintenance js-packages (#24)
- **(deps)**: lock file maintenance js-packages (#23)

### Refactor

- **(inline_editing)**: reformat warning message

### Documentation

- **(inline multi)**: document plan for customising inline multiselect element
- **(getting_started.md)**: correct minor discrepancies
- **(powercrud)**: rewrite and simplify docs
- **(blog)**: add post about possible enhancements

### Feature

- **(inline)**: ensure clicked field gets edit focus and <Enter>, <Esc> mirror Save, Cancel

## 0.4.6 (2025-11-09)

### Refactor

- **(CoreMixin)**: tighten up get_inline_edit_fields method
- **(InlineEditingMixin)**: move inline methods in
- **(inline_editing_mixin)**: consolidate all inline methods
- **(InlineEditingMixin)**: validate inline dependency fields against get_inline_editing_fields

### Documentation

- **(inline)**: document inline editing and remove guide prefix numbers
- **(docs)**: fix up cross-referencing errors
- **(inline_editing)**: add more detail around how inline_edit_fields must match form fields
- **(04_bulk_edit_async)**: clarify docs for downstream configuration of bulk async

### Feature

- **(inline_editing)**: implement inline editing in table of 1 row at a time

## 0.4.5 (2025-11-03)

### Refactor

- **(AsyncManager)**: have get_urls also include powercrud namespace

### Documentation

- **(enhancements)**: remove completed enhancements testing matrix and renovate

## 0.4.4 (2025-11-03)

## 0.4.3 (2025-11-02)

### Documentation

- **(README.md)**: correct link to codecov

## 0.4.2 (2025-11-01)

## 0.4.1 (2025-10-28)

## 0.4.0 (2025-10-28)

### Fix

- **(deps)**: lock file maintenance js-packages
- **(deps)**: lock file maintenance js-packages

## 0.3.6 (2025-10-27)

## 0.3.5 (2025-10-27)

### Fix

- **(get_logger)**: refactor all programs to use powercrud.get_logger
- **(async)**: fix test problems. BEFORE check completeness
- **(async_dashboard)**: get user label displaying correctly

### Documentation

- **(docs)**: restructure and update docs

### Feature

- **(async)**: implement async task context
- **(async)**: implement async cleanup cli and schedule
- **(async)**: implement refactored async with dashboard and lifecycle hooks

## 0.3.4 (2025-08-10)

## 0.3.3 (2025-08-03)

### Fix

- **(object_list)**: fix reset not updating page size and sort not working

## 0.3.2 (2025-08-03)

### Refactor

- **(powercrud)**: rename PowerCRUD to powercrud throughout except PowerCRUDMixin

## 0.3.1 (2025-07-30)

### Fix

- **(FormMixin)**: revert hard-coded tailwind widget classes; use correct imports
- **(templates)**: use correct powercrud templatetag name

### Documentation

- **(docs)**: make small updates to docs content and formatting
- **(README)**: fix links to docs
- **(README)**: make slight edit to tag

## 0.3.0 (2025-07-29)

### Documentation

- **(docs)**: make slight changes to docs

## 0.2.27 (2025-07-28)

### Fix

- **(bulk_edit_process_post)**: clear session of selected_ids after successful delete
- **(object_list)**: add handlers for hx-triggers refreshTable and bulkEditSuccess
- **(form_mixin)**: ensure _apply_widget_classes method is applied properly for form opens
- **(bulk_edit_process)**: correct location of template file
- **(sessions)**: fix bugs in previous backend work
- **(sessions)**: revert to complete first draft of tasks 1 & 2
- **(object_confirm_delete)**: fix behavkiour for async conflict detection
- **(nm_help)**: add docs url
- **(pagination)**: ensure page change persists existing filter, sort and pagination params

### Refactor

- **(various)**: remove log.debug statements
- **(sessions)**: partial incorrect implementation of task 4
- **(bulk_mixin)**: complete first draft of tasks 1 and 2
- **(config)**: refactor to support rename of django_nominopolitan to config directory
- **(sample)**: move templates and home view to sample app
- **(bulk)**: extract required info from request so not required in _perform_bulk_update
- **(bulk)**: separate delete and update into separate methods called by bulk_edit_process_post
- **(mixins)**: simplify mixins as a package with component feature mixins

### Documentation

- **(bulk_operations.md)**: explain re setting DATA_UPLOAD_MAX_NUMBER_FIELDS
- **(sample_app.md)**: update docs on create_sample_data mgmt command
- **(blog)**: document current 405 problem with toggles
- **(sessions)**: revise plan and document it for simpler approach
- **(sessions)**: finalise task list for sessions refactor
- **(sessions)**: write blog post plan for using django sessions
- **(mkdocs)**: add link to docs site on github pages
- **(mkdocs)**: move docs from readme to mkdocs

### Feature

- **(async)**: provide modal response to user on async queue success or failure
- **(sample.create_sample_data)**: allow --books-per-author and use faker for unlimited
- **(BulkActions)**: implement BulkActions enum for url routing of bulk toggle actions

## 0.2.26 (2025-07-05)

### Fix

- **(object_list)**: prevent adding null params to get url

## 0.2.25 (2025-07-05)

### Feature

- **(dropdown_sort_options)**: implement param to sort related objects asc or desc by specified field name for filters, bulk & single edit

## 0.2.24 (2025-07-05)

### Fix

- **(bulk_edit)**: ensure refresh table after bulk delete

### Feature

- **(bulk delete)**: allow bulk edit and/or bulk delete (or neither) with new bulk_delete param

## 0.2.23 (2025-07-05)

### Fix

- **(bulk_edit)**: add choices for fields with choices to _get_bulk_field_info

## 0.2.22 (2025-07-04)

### Fix

- **(bulk edit)**: fix processing of m2m fields

## 0.2.21 (2025-07-04)

### Feature

- **(pagination)**: enable user page size selection which persists after edits

## 0.2.20 (2025-07-03)

### Documentation

- **(README.md)**: improve documentation of override method for get_bulk_choice_for_field

### Feature

- **(sample)**: add Profile and ProfileCRUDView to test OneToOneField bulk edit
- **(bulk_edit_form)**: add logic to also handle OneToOneFields

## 0.2.19 (2025-07-03)

### Refactor

- **(get_bulk_choices_for_field)**: separate out method for extracting choices for foreign key fields, to allow easier override

## 0.2.18 (2025-07-03)

### Fix

- **(targeting)**: fix htmx targeting and table refresh after (bulk) edit save to preserve filter and sort params

## 0.2.17 (2025-07-01)

### Fix

- **(bulk_edit)**: fix foreign key record update and document bulk edit functionality

### Feature

- **(bulk_edit)**: add bulk edit functionality with atomic rollback on failure

## 0.2.16 (2025-05-22)

### Refactor

- **(object_list)**: change htmx:afterSwap listener to add event
- **(render_to_response)**: assuem hx trigger is always json format
- **(get_hx_trigger)**: always return json formatted triggers

## 0.2.15 (2025-05-22)

## 0.2.14 (2025-05-22)

### Refactor

- **(Genre)**: fix logic and method in clean()
- **(Genre)**: add test field

## 0.2.13 (2025-05-21)

### Refactor

- **(mixins)**: comment out debug statements

### Documentation

- **(README)**: document correct way to use @source instead of management command

## 0.2.12 (2025-05-10)

## 0.2.11 (2025-05-08)

### Documentation

- **(README.md)**: document how mixins._apply_crispy_helper() works

## 0.2.10 (2025-05-08)

## 0.2.9 (2025-05-07)

## 0.2.8 (2025-05-06)

### Refactor

- **(nm_extract_tailwind_classes)**: use generated css file instead of simulating

## 0.2.7 (2025-05-06)

## 0.2.6 (2025-05-06)

### Refactor

- **(crispy)**: use crispy_daisyui (not working)
- **(crispy)**: use crispy_daisyui instead (makes no difference)

## 0.2.5 (2025-05-04)

### Feature

- **(object_detail)**: support property.fget.short_description for column header if it exists

## 0.2.4 (2025-05-03)

## 0.2.3 (2025-04-21)

### Refactor

- **(object_list)**: remove unnecessary js given recent fix in backend

### Feature

- **(NominopolitanMixin)**: amend get_queryset and add override paginate_queryset to allow filters and pagination to coexist

## 0.2.2 (2025-04-21)

## 0.2.1 (2025-04-21)

## 0.2.0 (2025-04-21)

### Fix

- **(get_filter_queryset_for_field)**: make method more robust with filter and sort options

## 0.1.43 (2025-04-15)

## 0.1.42 (2025-04-15)

### Fix

- **(object_list)**: guartd against non-existent filter in initializeFilterToggle

## 0.1.41 (2025-04-14)

### Fix

- **(nominopolitan.py)**: add in missing models import from django.db

## 0.1.40 (2025-04-09)

### Feature

- **(NominopolitanMixin, nominopolitan.py)**: handle M2M fields in object list, forms and filtersets

## 0.1.39 (2025-04-08)

### Fix

- **(object_list)**: remove debug paragraph

### Refactor

- **(Author)**: set table column width parameters

## 0.1.38 (2025-04-08)

## 0.1.37 (2025-04-07)

### Fix

- **(list)**: make properties not sortable

### Refactor

- **(Book)**: add property with very long header name

## 0.1.36 (2025-04-07)

## 0.1.35 (2025-04-04)

### Fix

- **(nm_extract_tailwind_classes)**: include json and text files in scan

## 0.1.34 (2025-04-04)

### Documentation

- **(README.md)**: document tailwindcss considerations

## 0.1.33 (2025-04-02)

## 0.1.32 (2025-04-02)

### Refactor

- **(post_install)**: add post_install script to package to run nm_extract_tailwind_classes

## 0.1.31 (2025-04-02)

### Fix

- **(nm_extract_tailwind_classes)**: make --pretty option also save in pretty format

## 0.1.30 (2025-04-02)

### Refactor

- **(nm_extract_tailwind_classes)**: change default filename to nominopolitan_tailwind_safelist.json

## 0.1.29 (2025-04-02)

### Feature

- **(nm_extract_tailwind_classes)**: allow options --output and --package-dir to set file save destination

## 0.1.28 (2025-04-02)

### Refactor

- **(nm_extract_tailwind_classes)**: save file in non-pretty format and allow print of file in normal or --pretty format

## 0.1.27 (2025-04-02)

### Documentation

- **(new_release.sh)**: add comment

### Feature

- **(nm_extract_tailwind_classes)**: create management command to extract classes for downstream to include in safelist

## 0.1.26 (2025-04-02)

### Feature

- **(nm_generate_tailwind_config)**: write mgmt command to identify locations of files with tw classes

## 0.1.25 (2025-04-01)

### Feature

- **(django_nominopolitan)**: add parameters table_classes, action_button_classes, extra_button_classes and drop table_font_size

## 0.1.24 (2025-03-31)

### Fix

- **(new_release.sh)**: ensure correct path to static css files

## 0.1.23 (2025-03-31)

### Fix

- **(new_release.sh)**: ensure production css files built via npx

### Feature

- **(daisy)**: add daisyUI framework capability and templates

## 0.1.22 (2025-03-19)

### Feature

- **(render_to_response)**: add original_template to session data, retrievable via template tag or get_session_data_key('original_target')

## 0.1.21 (2025-03-18)

### Refactor

- **(extra_buttons)**: put extra_attrs and extra_class attrs first so they override calculated attributes

## 0.1.20 (2025-03-18)

### Fix

- **(extra_buttons)**: set extra_attrs as last added to buttons

## 0.1.19 (2025-03-18)

### Fix

- **(extra_buttons)**: fix logic for setting htmx_target

## 0.1.18 (2025-03-18)

### Feature

- **(extra_buttons)**: add support for extra_attrs (eg if want to use own modal)

## 0.1.17 (2025-03-18)

### Fix

- **(nm_help)**: include README.md in package so it can be read when imported

### Refactor

- **(extra_buttons)**: disregard htmx_target if display_modal is True

### Feature

- **(extra_buttons)**: support parameter extra_class_attrs

## 0.1.16 (2025-03-14)

### Feature

- **(extra_buttons)**: allow extra buttons to be implemented next to Create button via class attribute

## 0.1.15 (2025-03-10)

### Refactor

- **(object_form)**: use framework_template_path context var for relative include of crispy forms
- **(render_to_response)**: change logic to pick up overridden forms

### Feature

- **(nm_mktemplate)**: enhance management command options with app_name --all and app_name.model --all

## 0.1.14 (2025-03-10)

### Refactor

- **(sample)**: set form_class for Book but not for Author

### Documentation

- **(README)**: update docs re form_fields and form_fields_exclude attributes
- **(get_form_class)**: write code comments to improve maintainability
- **(README)**: update docs re url_base

## 0.1.13 (2025-03-10)

### Fix

- **(render_to_response)**: change all template partial names to nm_content and specify in response logic

## 0.1.12 (2025-03-10)

### Fix

- **(list.html)**: apply sort logic to th header not just the <a> tag with header text

## 0.1.11 (2025-03-09)

### Fix

- **(sort)**: maintain selected filter display when sorting with htmx

## 0.1.10 (2025-03-09)

### Fix

- **(pypoetry)**: correct extras syntax
- **(NominopolitanMixinValidator)**: remove defaults from validator class and set custom validator for hx_trigger

### Documentation

- **(README)**: update installation section

## 0.1.9 (2025-03-09)

### Feature

- **(NominopolitanMixin)**: validate all class attributes with pydantic NominopolitanMixinValidator

## 0.1.8 (2025-03-07)

### Fix

- **(list.html)**: make sort click on header not just header text

### Documentation

- **(README)**: update re nm_help
- **(nm_help)**: create management command to display README.md
- **(README)**: add url for popper.js installation instructions page

### Feature

- **(list.html)**: enable sort to apply any selected filters to returned data set

## 0.1.7 (2025-03-06)

### Feature

- **(django_nominopolitan)**: add new parameters to calculate max-table-height css parameter in list.html

## 0.1.6 (2025-03-06)

### Documentation

- **(README)**: update docs re nm_clear_session_keys

### Feature

- **(nm_clear_session_keys)**:  add management command to clear nominopolitan session keys

## 0.1.5 (2025-03-06)

### Fix

- **(list.html)**: use original_target for htmx for header sort when clicked

### Refactor

- **(object_list)**: remove debug statement

## 0.1.4 (2025-03-06)

### Fix

- **(filtering)**: fix bug in filtering by setting original htmx target correctly in session variable

## 0.1.3 (2025-03-05)

## 0.1.2 (2025-03-05)

### Feature

- **(django_nominopolitan)**: enable sort toggle on object list

## 0.1.1 (2025-03-01)

### Refactor

- **(DynamicFilterSet)**: use icontains for 'else' CharFilter
- **(get_table_font_size)**: set default to 1rem instead of 0.875rem

### Documentation

- **(README)**: update docs re ability to override get_filter_queryset_for_field

### Feature

- **(get_filterset_for_field)**: separate out method for easier override to restrict foreign key fields if needed

## 0.1.0 (2025-02-22)

### Feature

- **(bulma)**: Remove support for bulma in base package

## 0.0.43 (2025-02-22)

### Documentation

- add docstrings and type hints

## 0.0.42 (2025-02-19)

### Refactor

- **(mixins)**: remove debug comments

## 0.0.41 (2025-02-19)

### Feature

- **(filter)**: toggle display of filter fields

## 0.0.40 (2025-02-19)

### Feature

- **(list)**: truncate columns based on table_max_col_width and provide tooltips

## 0.0.39 (2025-02-18)

### Feature

- **(get_filterset)**: accommodate GeneratedField types for filter widget determination

## 0.0.38 (2025-02-18)

### Fix

- **(get_filterset)**: make all filter field args be applied to filtering

### Refactor

- **(AuthorCRUDView)**: use filterset class for sample purposes
- **(HTMXFilterSetMixin)**: apply htmx mixin to sample AuthorFilterSet class
- update main before merge
- **(get_framework_styles)**: define css framework styles as method in NominoPolitanMixin

### Feature

- **(object_list)**: drive font size of table using attribute table_font_size
- **(object_list)**: place buttons conditionally inline
- **(get_filterset)**: create dynamic filterset class based on filterset_fields to set htmx triggers

## 0.0.37 (2025-02-17)

### Fix

- **(filters)**: filters working with htmx only but no non-htmx option. also fonts too large

### Feature

- **(filterset)**: support filterset_fields with styling or filterset_class, both with htmx attrs as needed
- **(filter)**: 300ms delay works for text filter

## 0.0.36 (2025-02-15)

### Feature

- **(object_list.html)**: add code to display filterset if exists

## 0.0.35 (2025-02-12)

## 0.0.34 (2025-02-12)

## 0.0.33 (2025-02-11)

### Documentation

- **(action_links)**: comment future option to use hx-disable for simplified logic

### Feature

- **(modal_id)**: allow override of default modal_id 'nominopolitanBaseModal'

## 0.0.32 (2025-02-10)

### Fix

- **(use_htmx)**: make logic work for use_htmx and/or use_modal being False

## 0.0.31 (2025-02-10)

### Feature

- **(modal_target)**: allow custom modal_target

## 0.0.30 (2025-02-04)

### Feature

- **(Nominopolitan)**: support hx_trigger as value to pass as response['HX-Trigger'] with every response

## 0.0.29 (2025-02-04)

### Documentation

- **(README)**: update with details of display_modal for extra_actions

### Feature

- **(render_to_response)**: add hx-trigger messagesChanged to allow trigger of message display in base.html

## 0.0.28 (2025-01-25)

### Feature

- **(modal)**: allow extra_actions to specify display_modal: False

## 0.0.27 (2025-01-25)

## 0.0.26 (2025-01-25)

## 0.0.25 (2025-01-24)

### Fix

- **(modal)**: remove modal backdrop because it would not close after modal closed

## 0.0.24 (2025-01-23)

### Fix

- **(create form)**: get bootstrap modal working

## 0.0.23 (2025-01-23)

### Documentation

- **(README)**: write up changes in readme

## 0.0.22 (2025-01-23)

### Fix

- **(bootstrap)**: get bootstrap modal working
- get modal working ok for bulma

### Refactor

- **(object_list)**: add z-index to make modal work properly

## 0.0.21 (2024-12-05)

### Feature

- **(nominopolitan)**: exclude non-editable fields from forms if no form_class is specified

## 0.0.20 (2024-12-05)

### Feature

- **(nominopolitan)**: add parameters exclude, properties_exclude, detail_exclude, detail_properties_exclude

## 0.0.19 (2024-12-04)

## 0.0.18 (2024-12-04)

### Feature

- **(nominopolitan)**: add htmx pagination for object list template

## 0.0.17 (2024-12-04)

### Fix

- **(nominopolitan)**: add htmx directives to object_confirm_delete template form
- **(nominopolitan)**: add delete_view_url context variable and fix modal delete not working

## 0.0.16 (2024-12-03)

### Refactor

- **(nominopolitan)**: change parameters for fields, properties, detail_fields, detail_properties

## 0.0.15 (2024-12-03)

### Feature

- **(nominopolitan)**: Support fields or properties = 'all'; support detail_fields, detail_properties

## 0.0.14 (2024-12-02)

### Refactor

- **(django-nominopolitan)**: prefix all modal names with nominopolitan

### Documentation

- **(README)**: update and correct instructions

## 0.0.13 (2024-11-27)

### Fix

- **(nominopolitan)**: fix problem where non-htmx call initiated list for view where use_htmx is True

### Refactor

- **(nominopolitan)**: remove debug statement

### Feature

- **(nominopolitan)**: Allow hx-post parameter on extra_actions

## 0.0.12 (2024-11-27)

### Fix

- **(nominopolitan)**: use elif in get_htmx_target to ensure non-htmx target is None not "#None"

## 0.0.11 (2024-11-27)

### Refactor

- **(nominopolitan)**: put object_list modal inside #content partial

## 0.0.10 (2024-11-27)

## 0.0.9 (2024-11-27)

### Fix

- **(nominopolitan)**: get_success_url now correctly targets original hx-target of the list view if used
- **(nominopolitan)**: get update_view_url correctly into context
- **(sample)**: correct date widgets in forms
- **(nominopolitan)**: fix up when to prepend # to htmx_target

### Documentation

- **(nominopolitan)**: update docs with minimal detail on use_modal

### Feature

- **(nominopolitan)**: implement use_modal functionality for CRUD and other actions

## 0.0.8 (2024-11-26)

### Refactor

- **(nominopolitan)**: remove debug statement

### Feature

- **(nominopolitan)**: style action links as small buttons and allow extra_buttons to be specified
- **(NominoPolitanMixin)**: Allow specification of new actions

## 0.0.7 (2024-11-22)

### Documentation

- **(README)**: minimally document nm_mktemplate command

### Feature

- **(nm_mktemplate)**: nm_mktemplate to make copy of nominopolitan templates using same syntax as mktemplate

## 0.0.6 (2024-11-22)

### Refactor

- **(NominopolitanMixin)**: set context for htmx_target in get_context_data

### Documentation

- **(README)**: update minimal docs re htmx_crud_target

### Feature

- **(NominoPolitanMixin)**: support new attribute htmx_crud_target to allow separate target from object list
- **(NominoPolitanMixin)**: get create form working with htmx if use_htmx and htmx_target exists

## 0.0.5 (2024-11-22)

### Fix

- **(action_links)**: set links conditionally on whether htmx_target exists

## 0.0.4 (2024-11-21)

### Refactor

- **(nominpolitan)**: remove debug statement

## 0.0.3 (2024-11-20)

### Fix

- **(use_htmx_partials)**: remove this option as not used

## 0.0.2 (2024-11-20)

### Feature

- **(NominopolitanMixin)**: add logic for use of crispy forms depending on whether installed or overridden via use_crispy

## 0.0.1 (2024-11-20)

### Feature

- **(nominopolitan)**: allow parameterisation of use_crispy
- **(nominopolitan)**: Initial Commit
