# Changelog

PowerCRUD is still evolving quickly, and the early release history was cut at a high patch cadence while the package moved from `nominopolitan` to `powercrud`.

Version numbers below correspond to published git tags. The more important releases include a little extra narrative and upgrade context; smaller patch releases remain deliberately brief. For full detail between any two versions, use the GitHub compare view for the matching tags.

## 0.5.42 (2026-04-19)
- **Fix (favourites)**: filter favourites guard and documentation (#92)

## 0.5.41 (2026-04-18)
- **Feature**: ensure styling of filter class filters and fix More button dropdown

## 0.5.40 (2026-04-18)
- **Fix (favourites)**: make name migration mssql-safe

## 0.5.39 (2026-04-18)
- **Documentation**: streamline filter docs
- **Feature (favourites)**: support named filter favourites through optional contrib app

## 0.5.38 (2026-04-17)
- **Fix**: trigger multiselect updates
- **Feature (filters)**: support optional filters and browser display retention

## 0.5.36 (2026-04-17)

Tooltip defaults were shifted to a more neutral palette, with follow-up test coverage to keep the styling override path stable.

## 0.5.35 (2026-04-17)

Tooltip styling variables can now be overridden from CSS without patching the shipped templates.

## 0.5.34 (2026-04-16)
- **Feature (tooltips)**: provide params and hook for specifying field level tooltip contents

## 0.5.33 (2026-04-13)
- **Feature (hooks)**: add built-in update guard hooks and improve docs for sync and async
- **Feature (hooks)**: implement delete guard hooks

## 0.5.32 (2026-04-13)
- **Feature (delete)**: for standard single delete action pass validation errors to modal form

## 0.5.31 (2026-04-08)
- **Documentation**: move internal notes outside mkdocs tree
- **Documentation**: clarify async scope boundaries

## 0.5.30 (2026-04-08)
- **Documentation (hooks)**: clarify interaction of various hooks with class params
- **Feature (buttons)**: implement selection-aware extra_buttons and conditional extra_actions

## 0.5.29 (2026-04-04)
- **Fix (core_mixin)**: sort relation columns by name

## 0.5.28 (2026-04-04)
- **Fix (inline_editing_mixin)**: refresh lists after inline saves

## 0.5.27 (2026-04-04)
- **Documentation (persistence)**: update docs with migration guides for persistence hooks

## 0.5.26 (2026-04-03)
- **Documentation (plans)**: remove standalone asyncmanager phase
- **Feature (hooks)**: implement bulk async persistence hooks

## 0.5.25 (2026-04-03)
- **Refactor**: implement de-duplication of fieldname entries in class param lists
- **Feature (hooks)**: implement synchronous persistence hooks for single & bulk updates

## 0.5.24 (2026-04-01)
- **Fix (template)**: make empty-state create prompt conditional
- **Fix (deps)**: update dependency mkdocs-enumerate-headings-plugin to >=0.7,<0.8 (#82)

## 0.5.23 (2026-03-30)
- **Fix**: use daisyui select wrapper for page size control

## 0.5.22 (2026-03-30)
- **Fix**: harden bulk and inline editable field validation
- **Fix (inline)**: fix truncation of text in inline field contents
- **Fix (deps)**: update python-packages (#79)
- **Fix (deps)**: update python-packages (#72)
- **Documentation**: clarify strict bulk and inline field rules

## 0.5.21 (2026-03-21)
- **Fix (inline)**: ensure inline edit POST carry full form fields

## 0.5.20 (2026-03-19)

Follow-up maintenance release for the new non-editable and display-only form field work, focused on stabilising tests and async cache behaviour.

## 0.5.19 (2026-03-19)
- **Fix**: fix race condition with tooltips under htmx
- **Fix (inline)**: ensure form_disabled_fields is not applied to inline editing
- **Feature**: implement support to specify non-editable form fields and display-only fields

## 0.5.18 (2026-03-18)
- **Feature (column)**: support help text tooltips on specified column headers
- **Feature (powercrud)**: add view_instructions list helper text
- **Feature (inline)**: parameterise editable inline field background visibility and colour
- **Feature**: Add view_title parameter to set title at top of crud view page

## 0.5.17 (2026-03-17)
- **Documentation**: mention shift-click bulk range selection
- **Documentation**: add static queryset sample app example
- **Feature**: add loading spinners to bulk action buttons
- **Feature**: add static queryset rules to field dependencies

## 0.5.16 (2026-03-17)
- **Feature (extra_actions)**: provide option to display extra_actions as dropdown

## 0.5.15 (2026-03-16)
- **Fix (list)**: remove sticky header paint seams

## 0.5.14 (2026-03-16)

Filter layout spacing and presentation were tightened up.

## 0.5.13 (2026-03-16)
- **Feature (bulk)**: implement bulk select all feature

## 0.5.12 (2026-03-16)
- **Feature (show_record_count)**: implement boolean parameter to display filtered record count at top of table

## 0.5.11 (2026-03-16)
- **Refactor (inline)**: remove debug msg

## 0.5.10 (2026-03-16)
- **Refactor (inline)**: implement backward compatibility and deprecation warnings re inline_edit_enabled

## 0.5.9 (2026-03-12)
- **Documentation**: improve reference config options table
- **Feature (inline)**: drop need for boolean inline_edit_enabled & improve docs consistency

## 0.5.8 (2026-03-12)

Maintenance release focused on stabilising the Playwright tooltip coverage in CI.

## 0.5.7 (2026-03-12)
- **Fix (tippy)**: extract object list runtime into packaged JS
- **Documentation**: improve docs related to edit field dependencies parameterisation

## 0.5.6 (2026-03-11)

Compatibility release tightening the supported Django 4.2 / Python matrix.

## 0.5.5 (2026-03-11)
- **Fix (inline)**: serialize locked guard trigger payloads

## 0.5.4 (2026-03-11)
- **Fix (deps)**: update js-packages (#73)
- **Feature (forms)**: add declarative dependent queryset scoping
- **Feature (filtering)**: add nullable auto-filter controls

## 0.5.3 (2026-03-07)
- **Documentation**: provide detailed instructions on frontend bundled vs manual install

## 0.5.2 (2026-03-07)
- **Fix (frontend)**: move runtime assets into package static namespace

## 0.5.1 (2026-03-06)
- **Fix (test)**: use tomselect API path for stable bulk selection tests

## 0.5.0 (2026-03-06)

This was the Tom Select rollout release. Searchable filter controls moved onto a richer frontend widget, and this is the point where projects with manual asset integration needed to pay closer attention to the frontend setup notes.

### Upgrade Notes
- If you are not using the bundled PowerCRUD frontend assets, make sure Tom Select assets are included in your own build.
- **Fix (test)**: harden playwright tomselect interactions
- **Documentation (setup)**: remove unused frontend deps and clarify frontend bundle guidance
- **Feature (release)**: support breaking change notes in changelog flow
- **Feature (tooling)**: allow runproj exec command passthrough
- **Feature (test)**: add runtests mode flags for pytest and playwright
- **Feature (filters)**: add tomselect-powered searchable filter controls

## 0.4.19 (2026-03-06)
- **Fix (bulk)**: refresh positioning and preserve filters after bulk edit

## 0.4.18 (2026-03-06)
- **Feature (inline)**: implement inline dynamic field dependency updates with doc updates

## 0.4.17 (2026-03-06)
- **Fix (inline)**: harden dependent field refresh state and preserve dependency metadata on swap

## 0.4.16 (2026-03-06)
- **Fix (inline)**: preserve row context in dependency refresh and remove stray template artifact
- **Fix (deps)**: update js-packages (#70)

## 0.4.15 (2026-02-25)
- **Fix (deps)**: update python-packages (#68)
- **Fix (deps)**: update dependency pytest-django to >=4.12.0,<5 (#66)
- **Fix (deps)**: lock file maintenance js-packages (#64)
- **Documentation (docs)**: make settings config for core dependencies clearer in docs
- **Feature (ruff.sh)**: implement ruff and run across all files

## 0.4.14 (2026-02-09)
- **Fix (config_mixin)**: put in guard and test for non-async config
- **Fix (deps)**: lock file maintenance js-packages (#61)
- **Fix (deps)**: update js-packages (#38)
- **Fix (deps)**: lock file maintenance js-packages (#54)
- **Fix (deps)**: lock file maintenance js-packages (#52)
- **Fix (deps)**: lock file maintenance js-packages (#50)
- **Fix (deps)**: lock file maintenance js-packages (#47)
- **Fix (deps)**: lock file maintenance js-packages (#45)
- **Fix (deps)**: lock file maintenance js-packages (#42)

## 0.4.13 (2025-11-26)

Administrative release with no additional code changes beyond the published tag boundary.

## 0.4.12 (2025-11-26)
- **Fix (FormMixin)**: do guarded import of rcrispy-forms in case not needed
- **Fix (conf.py)**: do not require presence of settings.POWERCRUD_SETTINGS

## 0.4.11 (2025-11-26)
- **Refactor (ConfigMixin)**: consolidate config params, validation and resolution in ConfigMixin
- **Documentation (async)**: write plan to fix async guards
- **Documentation (templatePacks)**: finalise plan for new templatePack modularisation
- **Feature (PowerCRUDAsyncMixin)**: split AsyncMixin out from PowerCRUDMixin and include in new PowerCRUDAsyncMixin

## 0.4.10 (2025-11-15)
- **Documentation (README)**: use correct url for ci tests badge [skip tests]
- **Feature (InlineEditingMixin)**: add feature to inject missing required fields as hidden form fields

## 0.4.9 (2025-11-15)

Maintenance release covering CI skip-test handling and docs deployment workflow tweaks.

## 0.4.8 (2025-11-15)

Maintenance release to make documentation publishing run on every release.

## 0.4.7 (2025-11-15)
- **Fix (sample.BookCRUDView)**: add expected fields to form_fields
- **Fix (sample.BookCRUDView)**: remove author and genre unused methods
- **Fix (deps)**: lock file maintenance js-packages (#24)
- **Fix (deps)**: lock file maintenance js-packages (#23)
- **Refactor (inline_editing)**: reformat warning message
- **Documentation (inline multi)**: document plan for customising inline multiselect element
- **Documentation (getting_started.md)**: correct minor discrepancies
- **Documentation (powercrud)**: rewrite and simplify docs
- **Documentation (blog)**: add post about possible enhancements
- **Feature (inline)**: ensure clicked field gets edit focus and <Enter>, <Esc> mirror Save, Cancel

## 0.4.6 (2025-11-09)
- **Refactor (CoreMixin)**: tighten up get_inline_edit_fields method
- **Refactor (InlineEditingMixin)**: move inline methods in
- **Refactor (inline_editing_mixin)**: consolidate all inline methods
- **Refactor (InlineEditingMixin)**: validate inline dependency fields against get_inline_editing_fields
- **Documentation (inline)**: document inline editing and remove guide prefix numbers
- **Documentation (docs)**: fix up cross-referencing errors
- **Documentation (inline_editing)**: add more detail around how inline_edit_fields must match form fields
- **Documentation (04_bulk_edit_async)**: clarify docs for downstream configuration of bulk async
- **Feature (inline_editing)**: implement inline editing in table of 1 row at a time

## 0.4.5 (2025-11-03)
- **Refactor (AsyncManager)**: have get_urls also include powercrud namespace
- **Documentation (enhancements)**: remove completed enhancements testing matrix and renovate

## 0.4.4 (2025-11-03)

Maintenance release covering packaging and dependency housekeeping after the inline-editing rollout.

## 0.4.3 (2025-11-02)
- **Documentation (README.md)**: correct link to codecov

## 0.4.2 (2025-11-01)

Maintenance release simplifying the publish workflow so releases are cut from the lowest tested Python version.

## 0.4.1 (2025-10-28)

Administrative release with no additional code changes beyond the published tag boundary.

## 0.4.0 (2025-10-28)

This was more of a consolidation point than a big feature drop. It followed the async and packaging work in the `0.3.x` line and helped settle the renamed package's tooling baseline.
- **Fix (deps)**: lock file maintenance js-packages
- **Fix (deps)**: lock file maintenance js-packages

## 0.3.6 (2025-10-27)

Maintenance release fixing publish-workflow syntax after the large async and tooling work in `0.3.5`.

## 0.3.5 (2025-10-27)

This was the major async architecture release in the early `powercrud` era. It introduced task context, cleanup, lifecycle-aware dashboard work, and paired that with a much more serious test and tooling baseline.
- **Fix (get_logger)**: refactor all programs to use powercrud.get_logger
- **Fix (async)**: fix test problems. BEFORE check completeness
- **Fix (async_dashboard)**: get user label displaying correctly
- **Documentation (docs)**: restructure and update docs
- **Feature (async)**: implement async task context
- **Feature (async)**: implement async cleanup cli and schedule
- **Feature (async)**: implement refactored async with dashboard and lifecycle hooks

## 0.3.4 (2025-08-10)

Infrastructure release moving the project into `src/`, tightening container naming, and adding the dedicated `q2` service needed for fuller async development.

## 0.3.3 (2025-08-03)
- **Fix (object_list)**: fix reset not updating page size and sort not working

## 0.3.2 (2025-08-03)
- **Refactor (powercrud)**: rename PowerCRUD to powercrud throughout except PowerCRUDMixin

## 0.3.1 (2025-07-30)
- **Fix (FormMixin)**: revert hard-coded tailwind widget classes; use correct imports
- **Fix (templates)**: use correct powercrud templatetag name
- **Documentation (docs)**: make small updates to docs content and formatting
- **Documentation (README)**: fix links to docs
- **Documentation (README)**: make slight edit to tag

## 0.3.0 (2025-07-29)

This release marks the rename boundary from the older `nominopolitan` identity toward `powercrud`. The release itself was small, but it is a useful historical checkpoint when reading later changelog entries.
- **Documentation (docs)**: make slight changes to docs

## 0.2.27 (2025-07-28)
- **Fix (bulk_edit_process_post)**: clear session of selected_ids after successful delete
- **Fix (object_list)**: add handlers for hx-triggers refreshTable and bulkEditSuccess
- **Fix (form_mixin)**: ensure _apply_widget_classes method is applied properly for form opens
- **Fix (bulk_edit_process)**: correct location of template file
- **Fix (sessions)**: fix bugs in previous backend work
- **Fix (sessions)**: revert to complete first draft of tasks 1 & 2
- **Fix (object_confirm_delete)**: fix behavkiour for async conflict detection
- **Fix (nm_help)**: add docs url
- **Fix (pagination)**: ensure page change persists existing filter, sort and pagination params
- **Refactor (various)**: remove log.debug statements
- **Refactor (sessions)**: partial incorrect implementation of task 4
- **Refactor (bulk_mixin)**: complete first draft of tasks 1 and 2
- **Refactor (config)**: refactor to support rename of django_nominopolitan to config directory
- **Refactor (sample)**: move templates and home view to sample app
- **Refactor (bulk)**: extract required info from request so not required in _perform_bulk_update
- **Refactor (bulk)**: separate delete and update into separate methods called by bulk_edit_process_post
- **Refactor (mixins)**: simplify mixins as a package with component feature mixins
- **Documentation (bulk_operations.md)**: explain re setting DATA_UPLOAD_MAX_NUMBER_FIELDS
- **Documentation (sample_app.md)**: update docs on create_sample_data mgmt command
- **Documentation (blog)**: document current 405 problem with toggles
- **Documentation (sessions)**: revise plan and document it for simpler approach
- **Documentation (sessions)**: finalise task list for sessions refactor
- **Documentation (sessions)**: write blog post plan for using django sessions
- **Documentation (mkdocs)**: add link to docs site on github pages
- **Documentation (mkdocs)**: move docs from readme to mkdocs
- **Feature (async)**: provide modal response to user on async queue success or failure
- **Feature (sample.create_sample_data)**: allow --books-per-author and use faker for unlimited
- **Feature (BulkActions)**: implement BulkActions enum for url routing of bulk toggle actions

## 0.2.26 (2025-07-05)
- **Fix (object_list)**: prevent adding null params to get url

## 0.2.25 (2025-07-05)
- **Feature (dropdown_sort_options)**: implement param to sort related objects asc or desc by specified field name for filters, bulk & single edit

## 0.2.24 (2025-07-05)
- **Fix (bulk_edit)**: ensure refresh table after bulk delete
- **Feature (bulk delete)**: allow bulk edit and/or bulk delete (or neither) with new bulk_delete param

## 0.2.23 (2025-07-05)
- **Fix (bulk_edit)**: add choices for fields with choices to _get_bulk_field_info

## 0.2.22 (2025-07-04)
- **Fix (bulk edit)**: fix processing of m2m fields

## 0.2.21 (2025-07-04)
- **Feature (pagination)**: enable user page size selection which persists after edits

## 0.2.20 (2025-07-03)
- **Documentation (README.md)**: improve documentation of override method for get_bulk_choice_for_field
- **Feature (sample)**: add Profile and ProfileCRUDView to test OneToOneField bulk edit
- **Feature (bulk_edit_form)**: add logic to also handle OneToOneFields

## 0.2.19 (2025-07-03)
- **Refactor (get_bulk_choices_for_field)**: separate out method for extracting choices for foreign key fields, to allow easier override

## 0.2.18 (2025-07-03)
- **Fix (targeting)**: fix htmx targeting and table refresh after (bulk) edit save to preserve filter and sort params

## 0.2.17 (2025-07-01)
- **Fix (bulk_edit)**: fix foreign key record update and document bulk edit functionality
- **Feature (bulk_edit)**: add bulk edit functionality with atomic rollback on failure

## 0.2.16 (2025-05-22)
- **Refactor (object_list)**: change htmx:afterSwap listener to add event
- **Refactor (render_to_response)**: assuem hx trigger is always json format
- **Refactor (get_hx_trigger)**: always return json formatted triggers

## 0.2.15 (2025-05-22)

Small UI polish release for modal forms and delete confirmation presentation.

## 0.2.14 (2025-05-22)
- **Refactor (Genre)**: fix logic and method in clean()
- **Refactor (Genre)**: add test field

## 0.2.13 (2025-05-21)
- **Refactor (mixins)**: comment out debug statements
- **Documentation (README)**: document correct way to use @source instead of management command

## 0.2.12 (2025-05-10)

Build release improving Tailwind source discovery for downstream `crispy_tailwind` integration.

## 0.2.11 (2025-05-08)
- **Documentation (README.md)**: document how mixins._apply_crispy_helper() works

## 0.2.10 (2025-05-08)
- **Feature (get_form_class)**: add `FormHelper` automatically when needed and drop the separate `create_form_class` option

## 0.2.9 (2025-05-07)

Styling-path release that moved the package toward `crispy_tailwind`, with sample-app work to validate the new direction.

## 0.2.8 (2025-05-06)
- **Refactor (nm_extract_tailwind_classes)**: use generated css file instead of simulating

## 0.2.7 (2025-05-06)

Build release to ensure Vite receives the required environment variables during packaged frontend builds.

## 0.2.6 (2025-05-06)
- **Refactor (crispy)**: use crispy_daisyui (not working)
- **Refactor (crispy)**: use crispy_daisyui instead (makes no difference)

## 0.2.5 (2025-05-04)
- **Feature (object_detail)**: support property.fget.short_description for column header if it exists

## 0.2.4 (2025-05-03)

Delete confirmation template restyle for a cleaner modal flow.

## 0.2.3 (2025-04-21)
- **Refactor (object_list)**: remove unnecessary js given recent fix in backend
- **Feature (NominopolitanMixin)**: amend get_queryset and add override paginate_queryset to allow filters and pagination to coexist

## 0.2.2 (2025-04-21)

Small layout tidy-up separating the filter controls from the table more clearly.

## 0.2.1 (2025-04-21)

Administrative release with no additional code changes beyond the published tag boundary.

## 0.2.0 (2025-04-21)

This was the point where filtering started to feel like a first-class part of the package rather than just a convenience around the list view. It paired a filter UI refresh with more robust queryset handling for sortable, filterable relations.
- **Fix (get_filter_queryset_for_field)**: make method more robust with filter and sort options

## 0.1.43 (2025-04-15)

Maintenance release for dependency refresh only.

## 0.1.42 (2025-04-15)
- **Fix (object_list)**: guartd against non-existent filter in initializeFilterToggle

## 0.1.41 (2025-04-14)
- **Fix (nominopolitan.py)**: add in missing models import from django.db

## 0.1.40 (2025-04-09)
- **Feature (NominopolitanMixin, nominopolitan.py)**: handle M2M fields in object list, forms and filtersets

## 0.1.39 (2025-04-08)
- **Fix (object_list)**: remove debug paragraph
- **Refactor (Author)**: set table column width parameters

## 0.1.38 (2025-04-08)

Table-display polish for booleans and dates, plus better control over header wrapping.

## 0.1.37 (2025-04-07)
- **Fix (list)**: make properties not sortable
- **Refactor (Book)**: add property with very long header name

## 0.1.36 (2025-04-07)

Modal and form-heading styling refresh.

## 0.1.35 (2025-04-04)
- **Fix (nm_extract_tailwind_classes)**: include json and text files in scan

## 0.1.34 (2025-04-04)
- **Documentation (README.md)**: document tailwindcss considerations

## 0.1.33 (2025-04-02)

Refactor release removing an unsupported post-install approach after learning more about package-manager constraints.

## 0.1.32 (2025-04-02)
- **Refactor (post_install)**: add post_install script to package to run nm_extract_tailwind_classes

## 0.1.31 (2025-04-02)
- **Fix (nm_extract_tailwind_classes)**: make --pretty option also save in pretty format

## 0.1.30 (2025-04-02)
- **Refactor (nm_extract_tailwind_classes)**: change default filename to nominopolitan_tailwind_safelist.json

## 0.1.29 (2025-04-02)
- **Feature (nm_extract_tailwind_classes)**: allow options --output and --package-dir to set file save destination

## 0.1.28 (2025-04-02)
- **Refactor (nm_extract_tailwind_classes)**: save file in non-pretty format and allow print of file in normal or --pretty format

## 0.1.27 (2025-04-02)
- **Documentation (new_release.sh)**: add comment
- **Feature (nm_extract_tailwind_classes)**: create management command to extract classes for downstream to include in safelist

## 0.1.26 (2025-04-02)
- **Feature (nm_generate_tailwind_config)**: write mgmt command to identify locations of files with tw classes

## 0.1.25 (2025-04-01)
- **Feature (django_nominopolitan)**: add parameters table_classes, action_button_classes, extra_button_classes and drop table_font_size

## 0.1.24 (2025-03-31)
- **Fix (new_release.sh)**: ensure correct path to static css files

## 0.1.23 (2025-03-31)
- **Fix (new_release.sh)**: ensure production css files built via npx
- **Feature (daisy)**: add daisyUI framework capability and templates

## 0.1.22 (2025-03-19)
- **Feature (render_to_response)**: add original_template to session data, retrievable via template tag or get_session_data_key('original_target')

## 0.1.21 (2025-03-18)
- **Refactor (extra_buttons)**: put extra_attrs and extra_class attrs first so they override calculated attributes

## 0.1.20 (2025-03-18)
- **Fix (extra_buttons)**: set extra_attrs as last added to buttons

## 0.1.19 (2025-03-18)
- **Fix (extra_buttons)**: fix logic for setting htmx_target

## 0.1.18 (2025-03-18)
- **Feature (extra_buttons)**: add support for extra_attrs (eg if want to use own modal)

## 0.1.17 (2025-03-18)
- **Fix (nm_help)**: include README.md in package so it can be read when imported
- **Refactor (extra_buttons)**: disregard htmx_target if display_modal is True
- **Feature (extra_buttons)**: support parameter extra_class_attrs

## 0.1.16 (2025-03-14)
- **Feature (extra_buttons)**: allow extra buttons to be implemented next to Create button via class attribute

## 0.1.15 (2025-03-10)
- **Refactor (object_form)**: use framework_template_path context var for relative include of crispy forms
- **Refactor (render_to_response)**: change logic to pick up overridden forms
- **Feature (nm_mktemplate)**: enhance management command options with app_name --all and app_name.model --all

## 0.1.14 (2025-03-10)
- **Refactor (sample)**: set form_class for Book but not for Author
- **Documentation (README)**: update docs re form_fields and form_fields_exclude attributes
- **Documentation (get_form_class)**: write code comments to improve maintainability
- **Documentation (README)**: update docs re url_base

## 0.1.13 (2025-03-10)
- **Fix (render_to_response)**: change all template partial names to nm_content and specify in response logic

## 0.1.12 (2025-03-10)
- **Fix (list.html)**: apply sort logic to th header not just the <a> tag with header text

## 0.1.11 (2025-03-09)
- **Fix (sort)**: maintain selected filter display when sorting with htmx

## 0.1.10 (2025-03-09)
- **Fix (pypoetry)**: correct extras syntax
- **Fix (NominopolitanMixinValidator)**: remove defaults from validator class and set custom validator for hx_trigger
- **Documentation (README)**: update installation section

## 0.1.9 (2025-03-09)
- **Feature (NominopolitanMixin)**: validate all class attributes with pydantic NominopolitanMixinValidator

## 0.1.8 (2025-03-07)
- **Fix (list.html)**: make sort click on header not just header text
- **Documentation (README)**: update re nm_help
- **Documentation (nm_help)**: create management command to display README.md
- **Documentation (README)**: add url for popper.js installation instructions page
- **Feature (list.html)**: enable sort to apply any selected filters to returned data set

## 0.1.7 (2025-03-06)
- **Feature (django_nominopolitan)**: add new parameters to calculate max-table-height css parameter in list.html

## 0.1.6 (2025-03-06)
- **Documentation (README)**: update docs re nm_clear_session_keys
- **Feature (nm_clear_session_keys)**: add management command to clear nominopolitan session keys

## 0.1.5 (2025-03-06)
- **Fix (list.html)**: use original_target for htmx for header sort when clicked
- **Refactor (object_list)**: remove debug statement

## 0.1.4 (2025-03-06)
- **Fix (filtering)**: fix bug in filtering by setting original htmx target correctly in session variable

## 0.1.3 (2025-03-05)
- **Fix**: improve sorting for underscored fields and add a stable secondary sort by `id`

## 0.1.2 (2025-03-05)
- **Feature (django_nominopolitan)**: enable sort toggle on object list

## 0.1.1 (2025-03-01)
- **Refactor (DynamicFilterSet)**: use icontains for 'else' CharFilter
- **Refactor (get_table_font_size)**: set default to 1rem instead of 0.875rem
- **Documentation (README)**: update docs re ability to override get_filter_queryset_for_field
- **Feature (get_filterset_for_field)**: separate out method for easier override to restrict foreign key fields if needed

## 0.1.0 (2025-02-22)

First minor release after the exploratory patch series. It effectively committed the package to a Tailwind-oriented direction by removing Bulma support from the base package.
- **Feature (bulma)**: Remove support for bulma in base package

## 0.0.43 (2025-02-22)
- **Documentation**: add docstrings and type hints

## 0.0.42 (2025-02-19)
- **Refactor (mixins)**: remove debug comments

## 0.0.41 (2025-02-19)
- **Feature (filter)**: toggle display of filter fields

## 0.0.40 (2025-02-19)
- **Feature (list)**: truncate columns based on table_max_col_width and provide tooltips

## 0.0.39 (2025-02-18)
- **Feature (get_filterset)**: accommodate GeneratedField types for filter widget determination

## 0.0.38 (2025-02-18)
- **Fix (get_filterset)**: make all filter field args be applied to filtering
- **Refactor (AuthorCRUDView)**: use filterset class for sample purposes
- **Refactor (HTMXFilterSetMixin)**: apply htmx mixin to sample AuthorFilterSet class
- **Refactor**: update main before merge
- **Refactor (get_framework_styles)**: define css framework styles as method in NominoPolitanMixin
- **Feature (object_list)**: drive font size of table using attribute table_font_size
- **Feature (object_list)**: place buttons conditionally inline
- **Feature (get_filterset)**: create dynamic filterset class based on filterset_fields to set htmx triggers

## 0.0.37 (2025-02-17)
- **Fix (filters)**: filters working with htmx only but no non-htmx option. also fonts too large
- **Feature (filterset)**: support filterset_fields with styling or filterset_class, both with htmx attrs as needed
- **Feature (filter)**: 300ms delay works for text filter

## 0.0.36 (2025-02-15)
- **Feature (object_list.html)**: add code to display filterset if exists

## 0.0.35 (2025-02-12)

Table layout polish adding a clearer actions header and keeping the table width tighter to its content.

## 0.0.34 (2025-02-12)

Early styling pass to make the object list tables more compact.

## 0.0.33 (2025-02-11)
- **Documentation (action_links)**: comment future option to use hx-disable for simplified logic
- **Feature (modal_id)**: allow override of default modal_id 'nominopolitanBaseModal'

## 0.0.32 (2025-02-10)
- **Fix (use_htmx)**: make logic work for use_htmx and/or use_modal being False

## 0.0.31 (2025-02-10)
- **Feature (modal_target)**: allow custom modal_target

## 0.0.30 (2025-02-04)
- **Feature (Nominopolitan)**: support hx_trigger as value to pass as response['HX-Trigger'] with every response

## 0.0.29 (2025-02-04)
- **Documentation (README)**: update with details of display_modal for extra_actions
- **Feature (render_to_response)**: add hx-trigger messagesChanged to allow trigger of message display in base.html

## 0.0.28 (2025-01-25)
- **Feature (modal)**: allow extra_actions to specify display_modal: False

## 0.0.27 (2025-01-25)

Modal release adding backdrop cleanup so submissions do not leave stale overlays behind.

## 0.0.26 (2025-01-25)

Action-button layout polish, including better grouping on small screens.

## 0.0.25 (2025-01-24)
- **Fix (modal)**: remove modal backdrop because it would not close after modal closed

## 0.0.24 (2025-01-23)
- **Fix (create form)**: get bootstrap modal working

## 0.0.23 (2025-01-23)
- **Documentation (README)**: write up changes in readme

## 0.0.22 (2025-01-23)
- **Fix (bootstrap)**: get bootstrap modal working
- **Fix**: get modal working ok for bulma
- **Refactor (object_list)**: add z-index to make modal work properly

## 0.0.21 (2024-12-05)
- **Feature (nominopolitan)**: exclude non-editable fields from forms if no form_class is specified

## 0.0.20 (2024-12-05)
- **Feature (nominopolitan)**: add parameters exclude, properties_exclude, detail_exclude, detail_properties_exclude

## 0.0.19 (2024-12-04)

Pagination presentation polish using Django's proper elided page-range helper.

## 0.0.18 (2024-12-04)
- **Feature (nominopolitan)**: add htmx pagination for object list template

## 0.0.17 (2024-12-04)
- **Fix (nominopolitan)**: add htmx directives to object_confirm_delete template form
- **Fix (nominopolitan)**: add delete_view_url context variable and fix modal delete not working

## 0.0.16 (2024-12-03)
- **Refactor (nominopolitan)**: change parameters for fields, properties, detail_fields, detail_properties

## 0.0.15 (2024-12-03)
- **Feature (nominopolitan)**: Support fields or properties = 'all'; support detail_fields, detail_properties

## 0.0.14 (2024-12-02)
- **Refactor (django-nominopolitan)**: prefix all modal names with nominopolitan
- **Documentation (README)**: update and correct instructions

## 0.0.13 (2024-11-27)
- **Fix (nominopolitan)**: fix problem where non-htmx call initiated list for view where use_htmx is True
- **Refactor (nominopolitan)**: remove debug statement
- **Feature (nominopolitan)**: Allow hx-post parameter on extra_actions

## 0.0.12 (2024-11-27)
- **Fix (nominopolitan)**: use elif in get_htmx_target to ensure non-htmx target is None not "#None"

## 0.0.11 (2024-11-27)
- **Refactor (nominopolitan)**: put object_list modal inside #content partial

## 0.0.10 (2024-11-27)

Template cleanup release removing a stray `>` from `object_form.html`.

## 0.0.9 (2024-11-27)
- **Fix (nominopolitan)**: get_success_url now correctly targets original hx-target of the list view if used
- **Fix (nominopolitan)**: get update_view_url correctly into context
- **Fix (sample)**: correct date widgets in forms
- **Fix (nominopolitan)**: fix up when to prepend # to htmx_target
- **Documentation (nominopolitan)**: update docs with minimal detail on use_modal
- **Feature (nominopolitan)**: implement use_modal functionality for CRUD and other actions

## 0.0.8 (2024-11-26)
- **Refactor (nominopolitan)**: remove debug statement
- **Feature (nominopolitan)**: style action links as small buttons and allow extra_buttons to be specified
- **Feature (NominoPolitanMixin)**: Allow specification of new actions

## 0.0.7 (2024-11-22)
- **Documentation (README)**: minimally document nm_mktemplate command
- **Feature (nm_mktemplate)**: nm_mktemplate to make copy of nominopolitan templates using same syntax as mktemplate

## 0.0.6 (2024-11-22)
- **Refactor (NominopolitanMixin)**: set context for htmx_target in get_context_data
- **Documentation (README)**: update minimal docs re htmx_crud_target
- **Feature (NominoPolitanMixin)**: support new attribute htmx_crud_target to allow separate target from object list
- **Feature (NominoPolitanMixin)**: get create form working with htmx if use_htmx and htmx_target exists

## 0.0.5 (2024-11-22)
- **Fix (action_links)**: set links conditionally on whether htmx_target exists

## 0.0.4 (2024-11-21)
- **Refactor (nominpolitan)**: remove debug statement

## 0.0.3 (2024-11-20)
- **Fix (use_htmx_partials)**: remove this option as not used

## 0.0.2 (2024-11-20)
- **Feature (NominopolitanMixin)**: add logic for use of crispy forms depending on whether installed or overridden via use_crispy

## 0.0.1 (2024-11-20)

Initial packaged release under the earlier `nominopolitan` name, establishing the first configurable crispy-forms support and the basic CRUD customization shape the project grew from.
- **Feature (nominopolitan)**: allow parameterisation of use_crispy
- **Feature (nominopolitan)**: Initial Commit
