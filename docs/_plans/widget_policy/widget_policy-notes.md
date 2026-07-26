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

Application-supplied custom forms and their widget choices were outside the
initial Phase 1–5 scope.

If an application provides a custom `form_class`, the initial work does not
attempt to replace, restyle, normalize, or provide new guarantees for its
widgets. Existing compatibility must not be broken accidentally.

The first architectural phase also does not introduce new rich text editors, JSON editors, colour pickers, drag-and-drop uploads, date-range pickers, or a mutable application-wide widget registry.

## Scoped Follow-up: Silent Custom ModelForm Fields

Phase 7 narrows the custom-form boundary without making custom forms generally
pack-owned. Where a custom `ModelForm` leaves a model-backed, non-hidden field
on Django's default widget, PowerCRUD may apply the selected pack's normal
presentation policy. This lets the sample `BookForm` receive the compact inline
ManyToMany treatment for `genres`, even though the form does not explicitly
configure that widget.

An application remains authoritative if it declares a form field, supplies a
`Meta.widgets` entry, replaces Django's default widget class at runtime, or
uses a non-model or hidden control. Those fields stay outside the pack policy.

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

1. PowerCRUD has one explicit semantic policy contract for normal forms, inline editing, and filters; bulk presentation remains pack-owned literal markup until Phase 9 completes the unified resolution route.
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

Phase 7 additionally permits a custom ModelForm's silent default widgets to
enter this path. Explicit application widget choices remain outside it.

## Agreed Completion Architecture

Phase 9 completes the original ownership goal without introducing a mutable
widget registry. The public pack entry point remains
`get_widget_presentation(context)`.

The completed resolution path will be:

1. Django or generic PowerCRUD creates the field semantics, values, choices,
   queryset, validation, and submission behaviour.
2. PowerCRUD identifies the semantic widget category and surface, then calls
   the selected pack once for its presentation decision.
3. The pack starts from its base default for that semantic category and may
   apply a surface-specific variant.
4. PowerCRUD applies the compatible widget class, attributes, enhancement, and
   variant returned by the pack.
5. If the pack returns neutral presentation for a category, Django's compatible
   default widget remains in use.

Every pack may define base defaults for text, textarea, number, date, datetime,
time, boolean, select, multiselect, and file controls. A surface variant refines
that base default rather than creating an unrelated widget system. For example,
a pack may choose searchable multiselect as its base and use a standard variant
on normal forms, filters, and bulk forms while using a compact variant inline.

The four policy surfaces are:

1. Normal create and update forms, whether modal or non-modal.
2. Inline-edit forms.
3. Generated filter forms.
4. Bulk-edit value controls.

Eligible silent model-backed fields in custom `ModelForm` classes follow the
same normal or inline policy. Application-declared fields, `Meta.widgets`,
hidden controls, non-model fields, and other explicit application widget
choices remain authoritative and bypass pack defaults.

Surface context remains necessary for sizing, layout, request behaviour, and
bulk-operation surroundings. It must not be used by generic PowerCRUD to choose
a presentation library or impose an inline-only default. Application intent
should be expressed as default, enabled, or disabled so a pack can choose its
normal default while respecting explicit opt-in or opt-out configuration.

Bulk field-selection semantics and M2M add/remove/replace operations remain
generic PowerCRUD behaviour. Only the visible bulk value widget is resolved
through the pack policy.

### Pack API Shape

The required adapter method remains the complete public decision point:

```python
def get_widget_presentation(self, context):
    ...
```

Simple packs should be able to declare base defaults plus surface overrides;
advanced packs may implement conditional logic directly in the method. The
convenience API may take this shape:

```python
widget_defaults = {
    "multiselect": WidgetPresentation(
        enhancement="searchable-multiselect",
        variant="standard",
    ),
}

widget_surface_overrides = {
    ("inline", "multiselect"): WidgetPresentation(variant="compact"),
}
```

PowerCRUD merges the surface override onto the base default. Pack templates,
CSS, and browser adapters implement the returned decision; they do not create a
second policy authority. Most application developers only select a pack and use
ordinary Django custom-form mechanisms when they need an explicit override.

### Current Gaps Phase 9 Must Close

1. Normal forms, inline forms, and filters call `get_widget_presentation()`, but
   bulk value controls still bypass it and are literal pack-template markup.
2. Generic form code currently requests searchable multiselect presentation
   only for inline fields.
3. The first-party packs repeat the inline-only multiselect condition.
4. Normal/modal and bulk M2M controls therefore remain native even though the
   compact inline control has proven the enhancement path.

The resulting architecture is intended to reduce complexity: one semantic
resolver, one required pack method, explicit neutral fallback, and small surface
variants instead of presentation decisions distributed across generic form,
filter, inline, and bulk code.

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

### Phase 6: Correct Generated Datetime Controls

Correct the deferred date-only `DateTimeField` form and auto-filter behaviour through the selected pack policy. Keep this separate from the 0.8.6 temporal list-value formatting feature and preserve Django parsing, timezone, validation, and HTMX semantics.

### Phase 7: Apply Policy to Silent Custom ModelForm Widgets

Extend the selected-pack default only to model-backed fields for which a custom
ModelForm has not itself selected a widget. The sample `BookForm` is the proof:
its default `genres` multi-select may receive the inline pack enhancement, but
its explicit `published_date` widget remains untouched.

### Phase 8: Verify the Follow-up Behaviour

Validate both first-party packs across server and browser paths, including
datetime input/filter round-tripping and the custom-form ownership boundary.

### Phase 9: Complete Unified Pack Defaults Across Every Surface

Make the pack policy authoritative for value-control presentation across normal,
inline, filter, and bulk surfaces. Define pack base defaults with surface
variants, retain explicit Django fallback and application overrides, and use the
same rich multiselect family across all four surfaces with a compact inline
variant.

### Phase 10: Complete the Shared Multiselect UX

After Phase 9 establishes the final resolution route, improve the shared Tom
Select multiselect rather than adding another surface-specific widget. Both
first-party packs will import and register Tom Select's standard
`checkbox_options` plugin. Multiselects will keep selected options visible in
the dropdown, show their checked state, and let an option click add or remove
that value while the dropdown remains open.

The standard multiselect interaction will be shared across applicable
surfaces. Pack adapters remain responsible for DaisyUI or Bootstrap styling.
Roomier surfaces may retain ordinary selected-item presentation; the inline
variant will show a compact selected count rather than clipped partial chips.
The existing non-editing overflow tooltip remains unchanged, and no additional
inline-edit tooltip is required.

The current adapters register only Tom Select's `remove_button` plugin. With
`hideSelected` false, selected options therefore remain listed without a clear
selected indicator, and clicking an already-selected option does not toggle it
off. The checkbox plugin supplies the intended standard toggle behaviour. Any
failure to add an unselected option is treated as a separate regression and
must be covered by the same browser proof.

Successful inline save currently destroys Tom Select during HTMX teardown and
briefly restores the underlying native Django multi-select before the old row
is removed. Outgoing-fragment teardown must keep that native control hidden
until replacement while preserving normal native restoration for explicit or
non-swap destruction.

Acceptance evidence must cover DaisyUI and Bootstrap initial checked state,
mouse and keyboard add/remove behaviour, selected-count updates, Django POST
values, upward and downward viewport placement, HTMX reinitialisation, and the
absence of a native-control flash during save.

### Phase 11: Update Documentation

Promote the settled datetime, silent-custom-form, pack-default, surface-variant,
fallback, bulk-integration, and multiselect behaviour into stable documentation,
then reconcile these temporary notes with the final boundary.

## Implementation Evidence

The completed implementation replaces the old `filter_widget_attrs` adapter
field with a required widget-policy method. The first-party adapters now own
filter presentation and the old generic temporal form class is selected by the
pack. Ordinary generated form controls retain Django widgets when the pack
explicitly returns neutral presentation. Existing bulk controls remain literal
pack templates and therefore were not given a new generic metadata field.

Phase 9 will close that deliberate preservation gap and remove the generic
inline-only multiselect presentation decision. Until then, the implemented
contract is not yet the single resolution route for bulk value controls.

The deliberate visible change in Phase 5 is limited to generated inline ManyToMany fields:
the selected pack requests the existing Tom Select multi-value enhancement and
adds compact inline control/dropdown styling. Phase 7 separately extends that
route to silent default widgets in custom ModelForms; application-owned widget
choices still do not enter it.

Focused validation passed in separate successful gates:

1. 178 default-pack form, filter, inline, bulk, validation, and adapter tests.
2. 96 Bootstrap-pack server and shared-matrix tests.
3. 321 affected default-pack regression tests after preserving the existing
   bulk metadata contract.
4. The compact generated inline M2M browser proof under DaisyUI and Bootstrap.
5. Fresh `uv build` wheel and sdist validation through the isolated installed
   template-pack artifact harness.

The completed Phase 6–8 follow-up has separate successful evidence:

1. 115 focused form, filter, and dependency tests under the default DaisyUI
   settings.
2. The datetime and custom-form ownership proofs under Bootstrap settings.
3. The real sample `BookForm` inline M2M browser proof, including save, under
   both DaisyUI and Bootstrap settings.

Two attempted broad runs overlapped on the shared test database; they are not
used as evidence. An explicit all-tests Bootstrap invocation is also not a
supported gate because many legacy tests intentionally assert DaisyUI output.
