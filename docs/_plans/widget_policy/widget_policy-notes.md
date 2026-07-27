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

Phase 9 completed the original ownership goal without introducing a mutable
widget registry. The public pack entry point is
`get_widget_presentation(context)`.

The completed resolution path is:

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

### Gaps Closed in Phase 9

Before Phase 9, bulk value controls bypassed `get_widget_presentation()`,
generic form code requested searchable multiselect presentation only for
inline fields, and the first-party packs repeated that inline-only condition.
Phase 9 closed those gaps by routing visible bulk value controls through the
same resolver and moving standard-versus-compact defaults into each pack.

The resulting architecture is intended to reduce complexity: one semantic
resolver, one required pack method, explicit neutral fallback, and small surface
variants instead of presentation decisions distributed across generic form,
filter, inline, and bulk code.

### Phase 9 Implementation Outcome

Phase 9 is complete. `WidgetPolicyContext` now carries an explicit
`default`, `enabled`, or `disabled` enhancement intent, rather than a generic
default-on boolean. `BaseServerAdapter` resolves a pack's semantic base default
and then an optional `(surface, kind)` override. `WidgetPresentation` carries a
small `standard` or `compact` variant marker where a pack needs it.

DaisyUI and Bootstrap each declare all semantic categories. Neutral entries
mean Django keeps its compatible native widget; date, time, datetime, select,
and multiselect entries express the first-party pack defaults. The two packs
use standard searchable multiselects on normal forms, filters, and bulk forms,
and a compact variant inline.

Bulk editing now builds a real disabled Django `BoundField`, applies the same
resolver, and lets the existing pack template provide only layout and the
generic M2M operation radios. Field selection, values, choices, validation,
and add/remove/replace behaviour remain generic. Eligible silent model-backed
custom-ModelForm fields follow the same normal or inline route; application
widgets remain authoritative.

The deliberate pack-extension break is part of the unreleased template-pack
contract and server-adapter API version 2. The markers remain early validation
guards for an independently installed old pack; they are not user-facing
product versions or a second widget-policy system.

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

Phase 10 improved the shared Tom Select multiselect after Phase 9 established
the final resolution route. Both first-party packs import and register Tom
Select's standard `checkbox_options` plugin. Multiselects keep selected options
visible in the dropdown, show their checked state, and let an option click add
or remove that value while the dropdown remains open.

The standard multiselect interaction is shared across applicable surfaces.
Pack adapters remain responsible for DaisyUI or Bootstrap styling. Roomier
surfaces retain ordinary selected-item presentation; the inline variant shows
a compact selected count rather than clipped partial chips. The existing
non-editing overflow tooltip remains unchanged, and no additional inline-edit
tooltip is required.

Before Phase 10, the adapters registered only Tom Select's `remove_button`
plugin. With `hideSelected` false, selected options remained listed without a
clear selected indicator, and clicking an already-selected option did not
toggle it off. The checkbox plugin now supplies the intended standard toggle
behaviour, covered together with adding unselected options in browser tests.

Successful inline save previously destroyed Tom Select during HTMX teardown
and briefly restored the underlying native Django multi-select before the old
row was removed. Outgoing-fragment teardown now keeps that native control
hidden until replacement while preserving normal native restoration for
explicit or non-swap destruction.

### Phase 10 Implementation Outcome

The first Phase 10 implementation registered Tom Select's
`checkbox_options` plugin alongside `remove_button`. Selected menu options now
show checked checkboxes and selected styling; clicking one removes it while the
menu remains open. The regular standard variant retains normal removable chips.

The follow-up correction keeps compact inline chips hidden whether the menu is
closed or open, so `N selected` remains the stable row-level summary while the
checkbox menu supplies the detailed selection state. It also adds Tom Select's
`clear_button` plugin, restores Bootstrap modal initialisation after its modal
becomes visible, and ensures compact controls and their detached menus inherit
the containing table cell's computed font size. `table_classes` remains the
downstream typography hook; no new widget-policy setting is introduced.

The same table-typography rule now applies to row-action controls under both
packs: Bootstrap's buttons no longer retain Bootstrap's default button font
size. The default DaisyUI body-scrolling modal now receives a viewport-height
shell, matching Bootstrap's usable form height and leaving room for a normal
form multiselect menu near the lower fields. A modal configured with
`scroll="modal"` retains its content-sized shell.

During `htmx:beforeSwap`, the outgoing Tom Select control is destroyed without
restoring the already-hidden native select, removing the save flash before the
row replacement. The existing non-editing overflow tooltip remains unchanged.

Phase 10 completion evidence covers the resolver, silent custom form,
filters, bulk controls, Bootstrap native and Crispy modal rendering, checked
state, click-to-deselect, compact count while open, clear-all semantics,
table and row-action typography inheritance, submitted M2M values, placement,
full-height DaisyUI modal presentation, and successful save under both DaisyUI
and Bootstrap. Phase 11 records the resulting stable documentation.

Acceptance evidence covers DaisyUI and Bootstrap initial checked state,
mouse and keyboard add/remove behaviour, selected-count updates, Django POST
values, upward and downward viewport placement, HTMX reinitialisation, and the
absence of a native-control flash during save.

## Release-note draft

### Pack-owned widget presentation

PowerCRUD now lets the selected template pack own visible widget presentation
across normal forms, inline editing, generated filters, and bulk-edit value
controls. Applications get controls that fit the selected framework and
surface while PowerCRUD continues to own values, querysets, validation,
submission, dependencies, and HTMX lifecycle.

Generated `DateTimeField` controls now use true `datetime-local` inputs with
seconds preserved, and silent model-backed defaults in a custom `ModelForm` can
receive the selected pack's presentation without overriding declarative fields,
`Meta.widgets`, runtime replacements, non-model fields, or hidden controls.
Searchable multiselects now share checked options, click-to-toggle, and
clear-all behaviour across both first-party packs: normal forms, filters, and
bulk editing use the standard variant, while inline editing uses the compact
`N selected` variant.

The release also adds opt-in semantic list-column widths and material
cross-pack polish for headers, table sizing, modal controls, dropdown placement,
typography, palettes, and flash-free inline saves. Independently maintained
template packs must upgrade to the server-adapter version 2 widget-policy
contract; the browser-adapter API remains version 1. This version-neutral prose
should move into `CHANGELOG.md` unchanged when release work creates the version
and date heading.

## Branch Change Record

This is the consolidated implementation record for the branch. Use it as the
source checklist for Phase 11 stable documentation and release-note drafting;
it records outcomes rather than reproducing commit messages.

### Planning and Contract

1. Created this widget-policy plan, notes, inventory, ownership matrix,
   behaviour baseline, and contract record.
2. Replaced the previous pack widget hook with the current template-pack and
   server-adapter contract version 2. There is no old-adapter compatibility
   shim: an independently maintained old pack now fails early with a clear
   compatibility error.
3. Made `get_widget_presentation(context)` the one pack decision point for
   widget presentation. The context identifies a semantic widget kind,
   surface, render mode, field facts, and `default`, `enabled`, or `disabled`
   enhancement intent without naming a frontend framework.
4. Added `WidgetPresentation`, including a compatible widget override,
   attributes, enhancement marker, and `standard` or `compact` variant. The
   reusable `BaseServerAdapter` resolves a semantic base default followed by
   an optional `(surface, kind)` override.

### Pack-owned Widget Defaults

1. Moved presentation decisions for text, textarea, number, date, datetime,
   time, boolean, select, multiselect, and file controls into DaisyUI and
   Bootstrap policies.
2. Both first-party packs now define normal-form defaults and filter, inline,
   and bulk variants. A neutral pack decision leaves Django's compatible
   widget in place.
3. Generated forms, inline forms, generated filters, and bulk value controls
   all resolve through that same pack policy. Bulk field selection and M2M
   add/remove/replace semantics remain generic PowerCRUD behaviour.
4. The selected pack applies to a custom `ModelForm` only when a model-backed,
   non-hidden field still has Django's silent default widget. Application
   field declarations, `Meta.widgets`, runtime widget replacement, non-model
   fields, and hidden fields remain authoritative.
5. The sample `BookForm` proves that distinction: its silent `genres` field
   receives the policy, while its explicit `published_date` widget is kept.

### Datetime and Multiselect Behaviour

1. Generated `DateTimeField` create, update, inline, and filter controls now
   use real browser datetime-local presentation with seconds preserved. This
   is separate from the earlier list-value date/time formatting feature.
2. Normal forms, filters, and bulk forms use the standard searchable
   multiselect; inline editing uses the compact variant.
3. Both pack entries register Tom Select's `checkbox_options`,
   `remove_button`, and `clear_button` plugins. Selected options remain in
   the menu with checked state; clicking an option adds or removes it while
   the menu stays open; clear-all works without changing Django submission.
4. Compact inline multiselects show a stable `N selected` summary rather than
   clipped chips, including while the menu is open. Normal, filter, and bulk
   controls retain removable chips where there is room.
5. Inline dropdowns choose upward placement when the viewport has insufficient
   room below and do not recenter the edited row. Successful inline save no
   longer flashes the native Django multi-select before the HTMX row swap.
6. Bootstrap modal controls are enhanced after the modal is visible. The
   ordinary DaisyUI body-scrolling modal now uses the available viewport
   height; a modal explicitly configured with `scroll="modal"` remains
   content-sized.
7. Detached inline menus inherit the table-cell typography and the
   `inline_edit_highlight_accent` palette. The configured accent now drives
   the inline multiselect focus border and checkbox, while selected and active
   menu options use the related pale inline widget and hover tints rather than
   a generic blue.
8. Bulk M2M editing visibly preselects `Replace with selected`, matching the
   generic server-side default when the operation is omitted.
9. Put bulk M2M operation choices above their value control in both packs, so
   an open option menu cannot obscure the operation that will be submitted.
10. Removed DaisyUI's bulk-only `min-h-[150px]` from the enhanced control. Tom
    Select had copied it to its wrapper, causing in-modal dropdowns to open
    far below the visible selector. Both first-party packs now open bulk M2M
    menus directly below their controls.

### Table and Inline-list Presentation

1. Removed the sample Author `bio`/memo field from inline editing so a large
   textarea does not make an inline row excessively tall.
2. Made both list shells use their available container width rather than an
   unnecessarily constrained DaisyUI table wrapper.
3. Enlarged Bootstrap bulk-selection checkboxes to match the DaisyUI affordance.
4. Added semantic list-column width modes. `bounded` is the legacy default;
   the opt-in `semantic` policy infers compact primary-key and boolean columns,
   auto-sized temporal and numeric columns, and bounded text, relation,
   annotation, and property columns. Individual columns can override the
   resolved mode.
5. Added `column_width_policy` and `column_width_modes` to the base view API,
   plus `PowerField(..., column={"width": ...})` for structured declarations.
   The sample Author view demonstrates the semantic policy and explicit
   property/boolean overrides.
6. Updated both packs to size tables from their content within a full-width
   scroll container, avoiding equal distribution across every column while
   preserving a horizontal scrollbar when content genuinely cannot fit.
7. Made both packs use horizontally and vertically centred table headers,
   including the Actions heading. Cell alignment remains semantic and
   independently configurable.
8. Made Bootstrap inline widgets, detached menus, and row-action buttons
   inherit the table's configured text size, matching DaisyUI and preserving
   `table_classes` as the downstream typography hook.
9. Switched both Book sample views—the ordinary primitive view and the
   PowerField equivalent—to the opt-in `semantic` column-width policy.
10. Kept Bootstrap view controls above sticky table headers but below the
    Bootstrap modal layer, preventing filter and column controls from painting
    over a bulk-edit modal.

### Sample Shell Presentation

1. Added Bootstrap's light/dark selector to the sample navigation. It uses
   Bootstrap's native `data-bs-theme` support and remembers the local choice.
2. Compacted the Bootstrap sample shell's padding, metadata, navigation
   controls, and spacing so its menu area has a comparable text scale and
   vertical footprint to the DaisyUI sample shell.

### Validation and Packaging

1. Added or updated server, template, configuration, package-contract, and
   browser coverage for the policy, datetime, custom-form, multiselect,
   table-width, header, and palette behaviour under both first-party packs.
2. Verified compact inline M2M behaviour, values, checked options, clear-all,
   placement, typography, palette transfer, and save lifecycle in browser
   tests under DaisyUI and Bootstrap.
3. Rebuilt and committed the manifest-backed DaisyUI and Bootstrap frontend
   assets after each frontend-runtime change.
4. Updated the stable guides and references for the completed widget policy,
   multiselect behaviour, semantic column-width API, and cross-pack ownership
   boundary. Version-neutral release wording is retained in these notes until
   release work creates the `CHANGELOG.md` version and date heading.

### Phase 11: Update Documentation

The stable documentation keeps its existing task-led structure. Template-pack
authors use `template_packs/authoring-and-publishing.md` for the end-to-end
contract and release journey, including the collapsed release checklist, and
`template_packs/testing-and-acceptance.md` for the acceptance matrix.

Application developers use `guides/forms.md` as the main widget-presentation
authority, with the inline, filtering, and bulk guides describing their own
surface behaviour. Setup owns semantic list widths; Getting Started and the
styling guide own consumer asset-loading order; the sample and terse references
link back to those authorities without duplicating the policy.

The Phase 11 handover and inventory audit remain historical planning evidence.
No new stable page or MkDocs navigation entry was added. The release-note draft
above is the approved transfer source for a later release-heading update to
`CHANGELOG.md`.

## Implementation Evidence

The completed implementation replaces the old `filter_widget_attrs` adapter
field with the required server-adapter version 2 widget-policy method. The
first-party adapters own visible presentation across normal forms, inline
forms, generated filters, and bulk value controls. A neutral decision preserves
Django's compatible widget, while `BaseServerAdapter` combines semantic base
defaults, surface overrides, and explicit enhancement intent.

Bulk field selection and M2M add/remove/replace operations remain generic
PowerCRUD behaviour. Pack templates still own their layout, but the visible
bulk value control now resolves through the same widget policy as the other
three surfaces.

The deliberate visible change in Phase 5 was limited to generated inline ManyToMany fields:
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

### Phase 11 Documentation Validation

1. `git diff --check` passed for the completed documentation change set.
2. `.venv/bin/mkdocs build --strict` completed successfully after correcting
   the customisation page's management-command anchor. It reported no missing
   pages, invalid links or anchors, malformed tabs, malformed admonitions, or
   other build errors.
3. MkDocs retained the three pre-existing informational notices for pages that
   sit outside configured navigation: `guides/dependent_form_fields.md`,
   `guides/poweractions.md`, and `guides/powerfields.md`. Phase 11 deliberately
   made no navigation change.
4. The Material for MkDocs runtime printed its upstream MkDocs 2.0 migration
   advisory; the locked MkDocs 1.6 strict build itself passed.
5. Every changed stable Markdown page and its new cross-links were inspected.
   No product test was run because Phase 11 changes documentation only.
6. `CHANGELOG.md` remains unchanged. The version-neutral release prose stays in
   these notes until release work supplies the version and date heading.
