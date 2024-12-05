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
