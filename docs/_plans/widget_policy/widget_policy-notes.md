# Widget Policy Notes

## Intent

This project moves control of PowerCRUD-generated widget presentation out of the generic PowerCRUD layer and into the selected template pack.

The project has two deliberately separate outcomes:

1. A behaviour-preserving architectural change covering all currently visible widgets specified by PowerCRUD or the two first-party packs.
2. A later visible improvement to inline ManyToMany controls, used as the first proof that the new pack widget-policy architecture works.

## Agreed Scope

Phase 1 through Phase 4 cover controls generated or explicitly specified by PowerCRUD, DaisyUI, or Bootstrap on these surfaces:

1. Generated create and update forms.
2. Generated inline-edit forms.
3. Automatically generated filter forms.
4. Bulk-edit controls rendered by the first-party packs.
5. Native rendering and each pack's supported Crispy rendering path.

The visible widget categories in scope are:

1. Text inputs.
2. Textareas.
3. Number inputs.
4. Date inputs.
5. Datetime inputs.
6. Time inputs.
7. Boolean and checkbox controls.
8. Single-select controls.
9. Multi-select controls.
10. File inputs.

Hidden inputs, CSRF fields, preserved values, selected identifiers, and similar submission plumbing are not presentation-policy concerns. They remain neutral PowerCRUD or Django infrastructure.

## Explicitly Out of Scope

Application-supplied custom forms and their widget choices are out of scope.

If an application provides a custom `form_class`, this project does not attempt to replace, restyle, normalize, or provide new guarantees for its widgets. The work is concerned only with controls that PowerCRUD or a template pack specifies. Existing compatibility must not be broken accidentally, but custom-form widget policy is not a deliverable.

The first architectural phase also does not introduce new rich text editors, JSON editors, colour pickers, drag-and-drop uploads, date-range pickers, or a mutable application-wide widget registry.

## Ownership Boundary

PowerCRUD and Django continue to own form semantics:

1. Field values and initial values.
2. Choices and related-object querysets.
3. Required, disabled, and validation behaviour.
4. Single-value and multi-value submission semantics.
5. Field dependency resolution.
6. HTMX request, replacement, and preservation lifecycle.
7. Accessible error association and server-side error truth.

The selected template pack owns the default presentation policy for PowerCRUD-generated controls:

1. The appropriate widget or compatible widget variant for the semantic category and surface.
2. Framework classes and presentation attributes.
3. Semantic enhancement requests emitted into the rendered control.
4. Pack-owned browser-adapter behaviour and styling for enhanced controls.
5. Any pack-owned templates needed to render the control.

The generic layer may identify semantic facts such as `date`, `boolean`, `select`, `multiselect`, or `inline`, but it must not make DaisyUI-, Bootstrap-, or vendor-specific presentation choices.

## Current Pack Contract Change

This project changes the current template-pack contract cleanly. It does not
support both the old adapter shape and the new widget-policy shape.

The existing contract and server-adapter compatibility markers will be
incremented so an independently maintained old pack fails clearly, but those
numbers are implementation bookkeeping, not separate PowerCRUD products. At
any point, PowerCRUD accepts one current pack contract.

This break is limited to pack authors. Existing applications using the shipped
DaisyUI or Bootstrap packs retain their selector, templates, assets, form
semantics, browser lifecycle, and Phase 1–4 frontend behaviour. The generated
starter, validator, fixtures, first-party packs, and stable authoring guidance
change together, so no compatibility shim is needed.

## Current State

Widget ownership is currently split across several places:

1. `FormMixin.get_form_class()` explicitly creates date, datetime, and time widgets and currently includes a `form-control` class in generic code.
2. Django's generated `ModelForm` supplies the remaining ordinary form widgets.
3. `FilteringMixin` constructs text, number, date, time, select, and multiselect filter widgets while obtaining some presentation attributes from the selected pack.
4. Inline editing reuses generated form widgets and applies inline-specific adjustments, including number-input handling.
5. DaisyUI and Bootstrap bulk templates already own their bulk-control markup.
6. Bootstrap has a pack-specific bound-field renderer; DaisyUI uses its native or Crispy templates.
7. The shared browser runtime discovers semantic searchable-select markers, while the selected pack's browser adapter supplies the presentation-library implementation.

The widgets are not defined in `src/powercrud/templatetags/powercrud.py`. The relevant decisions are distributed across the form, filtering, inline, and bulk mixins; the pack templates and server adapters; Bootstrap's pack-specific template tags; and the two browser adapters.

## What Is Different at the End of Phase 1 Through Phase 4

Before this project, widget presentation decisions are partly generic, partly pack-owned, and partly embedded directly in individual templates. There is no single context-aware contract governing all PowerCRUD-generated widget surfaces.

After Phase 1 through Phase 4:

1. PowerCRUD has one explicit semantic route for resolving generated controls across normal forms, inline editing, filters, and bulk editing.
2. DaisyUI owns all DaisyUI presentation decisions for those controls.
3. Bootstrap owns all Bootstrap presentation decisions for those controls.
4. Generic PowerCRUD code no longer contains pack- or vendor-specific widget display choices.
5. Independent template packs have a documented, neutral contract for supplying the same policy.
6. Current server behaviour, rendered presentation, accessibility, and browser lifecycle remain equivalent under both first-party packs.

The selected pack must provide the policy. A pack may explicitly choose a
neutral presentation that leaves Django's compatible default widget in place,
but that is a pack policy decision rather than a generic old-contract fallback.

There is no intended frontend change in this part of the project. Any visible difference is treated as a regression unless it is an unavoidable correction explicitly reviewed and approved.

## What Is Different After Phase 5

Phase 5 makes the first intentional user-visible change.

Inline ManyToMany fields currently use a tall native multi-select that can increase table-row height. The new architecture will be used to let each pack provide an appropriate compact control without adding an M2M special case to generic PowerCRUD code.

At the end of Phase 5:

1. Inline ManyToMany editing remains within a compact row-oriented control instead of displaying the current tall native multi-select.
2. DaisyUI and Bootstrap provide the appropriate presentation through the same shared widget-policy contract.
3. The underlying Django multi-value field, queryset, validation, and POST behaviour remain intact.
4. The M2M implementation demonstrates that a future pack-specific widget improvement can be added without changing generic CRUD semantics.

## Precedence and Fallback

For the in-scope generated-control path, the intended resolution is:

1. Generic PowerCRUD identifies semantic facts and creates the underlying
   Django field/filter semantics.
2. The selected pack's required policy supplies a compatible widget override,
   attributes, and any semantic enhancement request.
3. Where that policy explicitly leaves the widget class unchanged, Django's
   normal default widget remains in use.

Application-supplied custom forms and view-level widget customization do not enter this resolution path.

## Plan Phases

### Phase 1: Lock the Current Contract and Baseline

Inventory the current generated-control surfaces and characterize existing DaisyUI and Bootstrap output before moving ownership. This baseline is the evidence that the architectural migration has not changed the frontend.

### Phase 2: Introduce the Pack Widget-Policy Architecture

Create the context-aware contract and resolver. The core supplies semantic
facts; every pack adapter supplies presentation policy. Replace the old
contract rather than supporting a parallel compatibility path. No pack-specific
library or class belongs in the generic layer.

### Phase 3: Migrate DaisyUI and Bootstrap Without Frontend Change

Move all current PowerCRUD-generated widget presentation choices into the two first-party packs. Preserve native, Crispy, searchable-select, dependency, validation, accessibility, and HTMX behaviour.

### Phase 4: Ratify the Behaviour-Preserving Architecture

Use shared server, browser, contract, and packaging acceptance evidence to prove that both packs retain the current frontend while the ownership boundary has changed.

### Phase 5: Prove the Policy With an Improved Inline M2M Control

Use the new policy to introduce the first deliberate visible improvement: a compact inline ManyToMany control implemented by both first-party packs without adding a generic special case.

## Implementation Evidence

The completed implementation replaces the old `filter_widget_attrs` adapter
field with a required widget-policy method. The first-party adapters now own
filter presentation and the old generic temporal form class is selected by the
pack. Ordinary generated form controls retain Django widgets when the pack
explicitly returns neutral presentation. Existing bulk controls remain literal
pack templates and therefore were not given a new generic metadata field.

The deliberate visible change is limited to generated inline ManyToMany fields:
the selected pack requests the existing Tom Select multi-value enhancement and
adds compact inline control/dropdown styling. Application-owned custom forms do
not enter that route.

Focused validation passed in separate successful gates:

1. 178 default-pack form, filter, inline, bulk, validation, and adapter tests.
2. 96 Bootstrap-pack server and shared-matrix tests.
3. 321 affected default-pack regression tests after preserving the existing
   bulk metadata contract.
4. The compact generated inline M2M browser proof under DaisyUI and Bootstrap.
5. Fresh `uv build` wheel and sdist validation through the isolated installed
   template-pack artifact harness.

Two attempted broad runs overlapped on the shared test database; they are not
used as evidence. An explicit all-tests Bootstrap invocation is also not a
supported gate because many legacy tests intentionally assert DaisyUI output.
