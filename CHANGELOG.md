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
