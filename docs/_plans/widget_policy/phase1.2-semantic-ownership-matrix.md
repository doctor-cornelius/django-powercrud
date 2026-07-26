# Phase 1.2: Semantic and Ownership Matrix

## Status

Complete. This page interprets the Phase 1.1 inventory as design input. It does
not yet define the policy API or treat unverified behaviour as contractual.

## Interpretation

The inventory records where controls happen to be created today. The future
boundary is simpler: Django and generic PowerCRUD retain form meaning and
lifecycle, while the selected pack owns the visible control used to express that
meaning. The surface is part of the input because the same semantic category may
need different presentation on a normal form, inline row, filter, or bulk form.

Current implementation details are classified as one of:

- **Preserve:** observable behaviour that must remain equivalent through Phase 4.
- **Migrate:** presentation that must move into the selected pack while remaining
  visibly equivalent.
- **Verify:** behaviour that the source inventory could not establish as a safe
  contract.
- **Exclude:** behaviour outside this project's policy boundary.

## Semantic Categories

| Category | Django or generic PowerCRUD retains | Selected pack owns |
| --- | --- | --- |
| Text | String value, initial value, validation, required and disabled state. | Single-line control, attributes, classes, layout and sizing. |
| Textarea | Multiline value and validation semantics. | Textarea widget variant, rows, classes and layout. |
| Number | Numeric parsing, value, constraints and validation. | Compatible number presentation, step, input mode, classes and sizing. |
| Date | Date value, parsing and validation. | Compatible date control and its presentation attributes. |
| Datetime | Datetime value, timezone handling, parsing and validation. | Compatible datetime control and its presentation attributes. |
| Time | Time value, parsing and validation. | Compatible time control and its presentation attributes. |
| Boolean | Boolean or nullable-boolean values, choices and validation. | Checkbox or select presentation appropriate to the surface. |
| Select | Single-value submission, choices or queryset, dependency and validation. | Select presentation, classes, layout and any searchable enhancement. |
| Multiselect | Multi-value submission, choices or queryset and validation; bulk add/remove/replace semantics remain generic. | Multi-value control, sizing, layout and any searchable enhancement. |
| File | Uploaded value, clear semantics, validation and multipart form handling. | Compatible file control, classes and layout. |

Hidden fields and submission plumbing are not semantic presentation categories.
Application-supplied custom forms and custom filtersets remain outside this
project's widget policy.

## Surface Matrix

| Surface | Django or generic PowerCRUD retains | Selected pack owns | Interpretation of current state |
| --- | --- | --- | --- |
| Create/update form | Generated form fields, values, validation, choices, querysets and submission. | Widget presentation, native rendering and supported Crispy presentation. | Preserve current output. Migrate the generic temporal widget classes and other pack-sensitive display choices. |
| Inline form | Form semantics plus row identity, dependency resolution, validation and HTMX replacement lifecycle. | Compact field presentation, inline sizing and enhanced-control behaviour. | Preserve current output through Phase 4. Treat the tall inline M2M as the deliberate Phase 5 improvement. |
| Automatic filter form | Filter meaning, lookups, choices/querysets and HTMX request semantics. | Filter control, framework attributes, sizing and enhancement choice. | Migrate current pack styles and multiselect presentation. Verify datetime and file fallback behaviour first. |
| Bulk form | Field eligibility, selected update fields, values and add/remove/replace operations. | Visible bulk-control markup, classes, layout and browser toggling/enhancement. | Existing bulk markup is already pack-owned. Preserve it while verifying time/file fallback behaviour. |

Native and supported Crispy rendering are two presentation paths through the
same selected pack; they are not separate semantic categories.

## Current Behaviour Decisions

| Current observation | Decision |
| --- | --- |
| Generic date, datetime and time widgets include `form-control`. | **Migrate.** This is pack-sensitive presentation in generic code; preserve the current visible result during the move. |
| Ordinary generated forms use Django's default widgets. | **Preserve semantics.** Exact widget presentation may be supplied by the selected pack, with neutral and Django fallbacks retained. |
| Inline numbers are rendered as text inputs with numeric input hints. | **Migrate.** Preserve the behaviour initially, but treat the widget type and input hints as presentation policy. |
| Filter widgets are created generically but receive pack-specific attributes. | **Split.** Keep filter semantics generic and move the complete visible-control decision into the selected pack. |
| Generic code marks eligible selects while pack adapters provide Tom Select. | **Split.** Keep semantic capability and lifecycle generic; the pack owns whether and how that capability is presented. The exact marker boundary is finalized in Phase 1.4. |
| DaisyUI and Bootstrap bulk templates create their own controls. | **Preserve.** This already follows the intended presentation ownership boundary. |
| Current native and supported Crispy paths differ between packs. | **Preserve.** Each pack may implement its presentation path differently while maintaining the same form semantics. |
| Datetime filter routing and filter/bulk time or file fallbacks are uncertain. | **Verify.** Phase 1.3 must establish actual runtime behaviour before it becomes a parity target. |
| Hidden inputs, submission plumbing and application custom forms/filtersets. | **Exclude.** They do not enter the widget-policy resolution path. |

## Result

Phase 2 may assume that its policy input consists of a semantic category plus a
surface context. It must preserve the generic semantics in these matrices while
allowing the selected pack to supply the visible control and any presentation
enhancement. Phase 1.3 still needs to establish the uncertain runtime and browser
baseline; Phase 1.4 will then lock the exact resolution and adapter contract.
