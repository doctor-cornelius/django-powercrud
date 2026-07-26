# Phase 1.1: Current Widget Inventory

## 1. Status

Complete as a read-only source and test inventory. This page records the controls
that the built-in PowerCRUD path and the DaisyUI and Bootstrap packs currently
create or explicitly render. It does not define the future widget-policy contract
and does not change code, tests, or the governing plan.

## 2. Scope and Method

The review covered:

- generated create and update `ModelForm` paths;
- generated inline-edit forms and inline dependency replacement;
- automatically generated filters (`filterset_fields`);
- DaisyUI and Bootstrap bulk-edit field templates;
- native and selected-pack Crispy field-rendering branches; and
- text, textarea, number, date, datetime, time, boolean/checkbox, select,
  multiselect, and file semantic categories.

The review used read-only `rg`, `sed`, `find`, and `git` inspection of the
PowerCRUD mixins, first-party pack templates/styles/adapters, browser adapters,
and focused tests. Application `form_class` and `filterset_class` design is out
of scope, as are hidden/submission plumbing, favourites, page-size/list-column
controls, and action controls. Static source is evidence of a declared path, not
proof of a particular browser DOM result; those distinctions are called out below.

## 3. Executive Findings

1. Normal generated forms are Django `ModelForm` forms. PowerCRUD explicitly
   replaces only date, datetime, and time model widgets and adds the generic
   `form-control` class to those three widgets (`form_mixin.py:681-704`). The
   remaining categories use Django's generated widgets (including
   `Textarea`, `NumberInput`, `CheckboxInput`, `Select`, `SelectMultiple`, and
   `ClearableFileInput`).
2. Inline forms reuse the same generated form class and finalization. Inline
   number controls are cloned and changed from `input type=number` to text with
   `inputmode=numeric` and `data-inline-number=true`
   (`inline_editing_mixin.py:1114-1132`).
3. Auto-generated filters explicitly construct text, select, multiselect, date,
   number, boolean-select, relation-select, and time widgets. Their classes and
   baseline attributes come from the selected server adapter's `filter_attrs`
   (`filtering_mixin.py:527-565, 702-809`).
4. The DaisyUI filter mapping uses `input`/`select` classes and a five-row tall
   multiselect; Bootstrap uses `form-control`/`form-select` and the same `size=5`
   multiselect (`daisyui/styles.py:30-61`, `bootstrap5/styles.py:41-64`).
5. Bulk-edit controls are pack-owned literal markup. Both packs render boolean
   select, date, datetime-local, relation/choice select, M2M multiselect plus
   add/remove/replace radios, number, and text branches. Neither bulk template
   has a time or file branch; those categories fall through to the text branch
   in the current source (`daisyui/partial/bulk_fields.html:18-95`,
   `bootstrap5/partial/bulk_fields.html:10-29`).
6. Searchable-select semantics are emitted by generic PowerCRUD markers, while
   Tom Select presentation is pack-browser-owned. Single selects are marked
   `data-powercrud-searchable-select`; filter multiselects are marked
   `data-powercrud-searchable-multiselect`; boolean and M2M bulk selects remain
   native (`form_mixin.py:148-184`, `filtering_mixin.py:185-215`,
   `metadata_mixin.py:102-133`).
7. DaisyUI's normal native form branch emits `{{ form }}`; its explicit Crispy
   inline layout adds DaisyUI classes to checkboxes and non-checkbox controls.
   Bootstrap's native branch calls `bootstrap5_field`, which classifies checkbox,
   select/multiselect, file, and all other widgets and adds accessible error
   classes/attributes (`daisyui/partial/form_fields.html:1-4`,
   `daisyui/layout/inline_field.html:1-25`,
   `bootstrap5/partial/form_fields.html:1-43`,
   `powercrud_bootstrap5.py:20-52`).
8. `src/powercrud/templatetags/powercrud.py` does not own widget selection. Its
   relevant form helper only fetches an already-built bound field
   (`templatetags/powercrud.py:261-272`); widget construction is distributed
   across `FormMixin`, `FilteringMixin`, inline preparation, bulk metadata, and
   pack templates.

## 4. Inventory Matrix

The ownership labels in this table mean: **PowerCRUD-created** (generic Python
or generic template creates/changes the control), **Django-default** (the
generated model form supplies the widget), **pack-rendered/styled** (the selected
pack template or server style mapping supplies markup/classes), and
**pack-browser-enhanced** (a pack adapter changes the browser presentation after
semantic markers are discovered).

| Surface / category | Current control and ownership | DaisyUI handling | Bootstrap handling | Browser markers / adapters | Evidence |
| --- | --- | --- | --- | --- | --- |
| Create/update: text | Django `TextInput` for ordinary `CharField`-like fields; PowerCRUD does not replace it. | Native path is `{{ form }}`; Crispy is delegated to `{% crispy form %}` (exact integration styling is not declared here). | Native path renders through `bootstrap5_field`: `form-control` (or `form-control-sm` when small); Crispy is delegated to selected Crispy integration. | No searchable marker. Normal HTMX form lifecycle remains generic. | [`form_mixin.py:681-733`](../../../src/powercrud/mixins/form_mixin.py#L681-L733), [`daisyui/partial/form_fields.html:1-4`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/form_fields.html#L1-L4), [`bootstrap5/partial/form_fields.html:14-40`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/form_fields.html#L14-L40), [`powercrud_bootstrap5.py:27-38`](../../../src/powercrud/contrib/bootstrap5/templatetags/powercrud_bootstrap5.py#L27-L38) |
| Create/update: textarea | Django `Textarea` for model `TextField`; no generic replacement. | Native Django output; Crispy output delegated. | `bootstrap5_field` treats it as a non-checkbox/select/file control and applies `form-control`. | No marker. | [`form_mixin.py:681-733`](../../../src/powercrud/mixins/form_mixin.py#L681-L733), [`powercrud_bootstrap5.py:30-38`](../../../src/powercrud/contrib/bootstrap5/templatetags/powercrud_bootstrap5.py#L30-L38) |
| Create/update: number | Django `NumberInput` for integer/decimal/float model fields. | Native output; Crispy output delegated. | `bootstrap5_field` applies `form-control`. | No marker. | [`powercrud_bootstrap5.py:30-38`](../../../src/powercrud/contrib/bootstrap5/templatetags/powercrud_bootstrap5.py#L30-L38) |
| Create/update: date | PowerCRUD-created `DateInput(attrs={type: date, class: form-control})`. | Native form retains the generic `form-control` class; no DaisyUI-specific field class in native path. | Native `bootstrap5_field` adds `form-control`; the generic widget still carries `type=date` and `form-control`. | No marker. | [`form_mixin.py:688-691`](../../../src/powercrud/mixins/form_mixin.py#L688-L691), [`bootstrap5/partial/form_fields.html:28-40`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/form_fields.html#L28-L40) |
| Create/update: datetime | PowerCRUD-created `DateTimeInput(attrs={type: datetime-local, class: form-control})`. | Same native/Crispy split as above. | `bootstrap5_field` applies `form-control`, retaining `datetime-local`. | No marker. | [`form_mixin.py:692-695`](../../../src/powercrud/mixins/form_mixin.py#L692-L695), [`powercrud_bootstrap5.py:35-38`](../../../src/powercrud/contrib/bootstrap5/templatetags/powercrud_bootstrap5.py#L35-L38) |
| Create/update: time | PowerCRUD-created `TimeInput(attrs={type: time, class: form-control})`. | Same native/Crispy split as above. | `bootstrap5_field` applies `form-control`, retaining `type=time`. | No marker. | [`form_mixin.py:696-699`](../../../src/powercrud/mixins/form_mixin.py#L696-L699), [`bootstrap5/styles.py:50-53`](../../../src/powercrud/contrib/bootstrap5/styles.py#L50-L53) |
| Create/update: boolean/checkbox | Django `CheckboxInput` for model booleans. | Native Django output; Crispy inline layout explicitly uses `checkbox checkbox-sm` (normal Crispy form remains delegated). | Native `form_fields.html` identifies checkbox fields; `bootstrap5_field` applies `form-check-input` and accessible feedback. | No searchable marker; checkbox behavior is generic browser/PowerCRUD runtime. | [`daisyui/layout/inline_field.html:6-12`](../../../src/powercrud/templates/powercrud/packs/daisyui/layout/inline_field.html#L6-L12), [`bootstrap5/partial/form_fields.html:14-27`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/form_fields.html#L14-L27), [`powercrud_bootstrap5.py:29-32`](../../../src/powercrud/contrib/bootstrap5/templatetags/powercrud_bootstrap5.py#L29-L32) |
| Create/update: select | Django `Select` for fixed choices, FK, and one-to-one fields. Generic finalization marks eligible single selects searchable. | Native output; Crispy delegated. | `bootstrap5_field` applies `form-select`. | `data-powercrud-searchable-select=true` except boolean-like selects; shared runtime discovers it and selected pack's Tom Select adapter enhances it. | [`form_mixin.py:148-184`](../../../src/powercrud/mixins/form_mixin.py#L148-L184), [`searchable-selects.js:16-22`](../../../src/powercrud/static/powercrud/js/runtime/searchable-selects.js#L16-L22), [`daisyui-searchable-select-adapter.js:126-214`](../../../src/powercrud/static/powercrud/js/runtime/daisyui-searchable-select-adapter.js#L126-L214), [`bootstrap5-searchable-select-adapter.js:101-156`](../../../src/powercrud/contrib/bootstrap5/static/powercrud/contrib/bootstrap5/js/runtime/bootstrap5-searchable-select-adapter.js#L101-L156) |
| Create/update: multiselect | Django `SelectMultiple` for M2M fields; no generic replacement. | Native output; Crispy delegated. | `bootstrap5_field` applies `form-select` (including `multiple`). | Normal form finalization excludes multiple selects from the single-select marker; no generated form multiselect marker is added by `FormMixin`. | [`form_mixin.py:157-162`](../../../src/powercrud/mixins/form_mixin.py#L157-L162), [`powercrud_bootstrap5.py:32-37`](../../../src/powercrud/contrib/bootstrap5/templatetags/powercrud_bootstrap5.py#L32-L37) |
| Create/update: file | Django `ClearableFileInput` for `FileField`; no generic replacement. | Native output or delegated Crispy output; exact class depends on the selected Crispy integration. | `bootstrap5_field` explicitly recognizes `FileInput` and applies `form-control`/`form-control-sm`. | No searchable marker; multipart is enabled by the form shell when `form.is_multipart`. | [`form_shell.html:20-24`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/form_shell.html#L20-L24), [`powercrud_bootstrap5.py:32-38`](../../../src/powercrud/contrib/bootstrap5/templatetags/powercrud_bootstrap5.py#L32-L38) |
| Inline: all editable categories | Reuses `get_form_class()` and `_finalize_form(..., inline=True)`; therefore the normal generated widget matrix applies. | Native inline row prints `{{ inline_field }}`; explicit DaisyUI Crispy inline layout uses checkbox classes or `input input-bordered input-sm w-full` for non-checkbox fields. | Inline row calls `bootstrap5_field(..., small=True)`, yielding compact Bootstrap classes and invalid state. | Inline wrappers carry `data-inline-field`; dependent fields carry `data-inline-dependent`, `data-inline-depends-on`, and `data-inline-endpoint`. Searchable selects use the same marker/runtime and get inline dropdown sizing in both adapters. | [`form_mixin.py:753-763`](../../../src/powercrud/mixins/form_mixin.py#L753-L763), [`daisyui/partial/inline_row_form.html:21-43`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/inline_row_form.html#L21-L43), [`bootstrap5/partial/inline_row_form.html:6-11`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/inline_row_form.html#L6-L11), [`daisyui/layout/inline_field.html:1-15`](../../../src/powercrud/templates/powercrud/packs/daisyui/layout/inline_field.html#L1-L15) |
| Inline: number-specific adjustment | PowerCRUD clones number widgets, changes `input_type` to text, sets `inputmode=numeric`, and adds `data-inline-number=true`. | Native field is then printed as-is; Crispy inline layout supplies DaisyUI input class. | `bootstrap5_field(small=True)` supplies `form-control-sm` while preserving the inline number attributes. | `data-inline-number` is a browser hint/marker; no separate adapter was found in the reviewed runtime. | [`inline_editing_mixin.py:1114-1132`](../../../src/powercrud/mixins/inline_editing_mixin.py#L1114-L1132) |
| Auto filter: text/textarea-like | PowerCRUD creates `CharFilter` with `TextInput` (including fallback fields); `Textarea` is only recognized for custom filterset styling. | Server style mapping uses `input input-bordered input-sm ...`. | Server style mapping uses `form-control form-control-sm`. | HTMX trigger is keyup/change delay for `TextInput`; no searchable marker. | [`filtering_mixin.py:273-310`](../../../src/powercrud/mixins/filtering_mixin.py#L273-L310), [`filtering_mixin.py:746-751`](../../../src/powercrud/mixins/filtering_mixin.py#L746-L751), [`filtering_mixin.py:117-140`](../../../src/powercrud/mixins/filtering_mixin.py#L117-L140) |
| Auto filter: number | PowerCRUD creates `NumberFilter` + `NumberInput`, adds `step=any` unless supplied. | DaisyUI number filter attrs use `input input-bordered ...`; Bootstrap uses `form-control ...`. | Same pack style mapping; HTMX uses keyup/change delay. | No enhancement marker. | [`filtering_mixin.py:759-768`](../../../src/powercrud/mixins/filtering_mixin.py#L759-L768), [`daisyui/styles.py:47-54`](../../../src/powercrud/packs/daisyui/styles.py#L47-L54), [`bootstrap5/styles.py:47-53`](../../../src/powercrud/contrib/bootstrap5/styles.py#L47-L53) |
| Auto filter: date | PowerCRUD creates `DateFilter` + `DateInput`, adds `type=date` unless supplied. | DaisyUI input classes; Bootstrap form-control classes. | Date widget receives `change` HTMX trigger via `DateInput`. | No enhancement marker. | [`filtering_mixin.py:752-758`](../../../src/powercrud/mixins/filtering_mixin.py#L752-L758), [`filtering_mixin.py:122-126`](../../../src/powercrud/mixins/filtering_mixin.py#L122-L126) |
| Auto filter: datetime | There is no dedicated datetime branch. Because `DateTimeField` is a `DateField` subclass, static construction routes it through the date branch; this is an ambiguity requiring runtime confirmation. | If that branch is taken, DaisyUI date attrs apply. | If that branch is taken, Bootstrap date attrs apply. | No marker. | [`filtering_mixin.py:746-803`](../../../src/powercrud/mixins/filtering_mixin.py#L746-L803) |
| Auto filter: time | PowerCRUD creates `TimeFilter` + `TimeInput`, adds `type=time` unless supplied. | DaisyUI time attrs use `input input-bordered ...`. | Bootstrap time attrs use `form-control ...`. | Date/time-like controls use `change` HTMX trigger. | [`filtering_mixin.py:797-803`](../../../src/powercrud/mixins/filtering_mixin.py#L797-L803), [`daisyui/styles.py:55-58`](../../../src/powercrud/packs/daisyui/styles.py#L55-L58), [`bootstrap5/styles.py:50-53`](../../../src/powercrud/contrib/bootstrap5/styles.py#L50-L53) |
| Auto filter: boolean | PowerCRUD creates a `BooleanFilter` rendered as a three-choice native `Select` (blank/true/false); nullable scalar companions use the same select shape. | DaisyUI select classes. | Bootstrap form-select classes. | Boolean-like selects are deliberately excluded from searchable enhancement. | [`filtering_mixin.py:640-659`](../../../src/powercrud/mixins/filtering_mixin.py#L640-L659), [`filtering_mixin.py:769-780`](../../../src/powercrud/mixins/filtering_mixin.py#L769-L780), [`filtering_mixin.py:161-168`](../../../src/powercrud/mixins/filtering_mixin.py#L161-L168) |
| Auto filter: select/relation | PowerCRUD creates `ChoiceFilter`, `ModelChoiceFilter`, or nullable relation variant with `Select`; relation querysets are built/sorted by generic code. | DaisyUI select attrs. | Bootstrap form-select attrs. | Eligible single selects receive `data-powercrud-searchable-select=true`; runtime delegates to pack Tom Select adapter. | [`filtering_mixin.py:728-745`](../../../src/powercrud/mixins/filtering_mixin.py#L728-L745), [`filtering_mixin.py:781-796`](../../../src/powercrud/mixins/filtering_mixin.py#L781-L796), [`filtering_mixin.py:185-215`](../../../src/powercrud/mixins/filtering_mixin.py#L185-L215) |
| Auto filter: multiselect | PowerCRUD creates `ModelMultipleChoiceFilter` (or all-values variant) + `SelectMultiple`. | DaisyUI multiselect attrs include `size=5` and a minimum/max height style. | Bootstrap multiselect attrs include `size=5`. | Eligible multiselects receive `data-powercrud-searchable-multiselect=true`; shared runtime invokes pack adapter `enhanceMultiple`. | [`filtering_mixin.py:728-739`](../../../src/powercrud/mixins/filtering_mixin.py#L728-L739), [`daisyui/styles.py:42-46`](../../../src/powercrud/packs/daisyui/styles.py#L42-L46), [`bootstrap5/styles.py:47-50`](../../../src/powercrud/contrib/bootstrap5/styles.py#L47-L50), [`searchable-selects.js:24-30`](../../../src/powercrud/static/powercrud/js/runtime/searchable-selects.js#L24-L30) |
| Auto filter: file | No dedicated file-filter branch exists; static fallback is a `CharFilter` + `TextInput` for an unrecognised model field type. Exact django-filter model-field generation is unverified here. | If fallback is used, DaisyUI text filter attrs apply. | If fallback is used, Bootstrap text filter attrs apply. | No marker. | [`filtering_mixin.py:746-751`](../../../src/powercrud/mixins/filtering_mixin.py#L746-L751), [`filtering_mixin.py:804-809`](../../../src/powercrud/mixins/filtering_mixin.py#L804-L809) |
| Bulk: boolean | Pack template creates a native `select` with `-- No change --`, Yes, No. | `select select-bordered w-full`. | `form-select`. | No searchable marker; pack script only toggles disabled state. | [`daisyui/partial/bulk_fields.html:18-24`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/bulk_fields.html#L18-L24), [`bootstrap5/partial/bulk_fields.html:10-12`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/bulk_fields.html#L10-L12) |
| Bulk: date/datetime | Pack templates create `input type=date` and `input type=datetime-local`. | DaisyUI `input input-bordered w-full`. | Bootstrap `form-control`. | Enabled/disabled by pack bulk script; no searchable marker. | [`daisyui/partial/bulk_fields.html:26-33`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/bulk_fields.html#L26-L33), [`bootstrap5/partial/bulk_fields.html:12-15`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/bulk_fields.html#L12-L15) |
| Bulk: select/relation | Pack template creates a single `select` with no-change/null/blank choices. Generic metadata marks FK/one-to-one and fixed choices as searchable where eligible. | `select select-bordered w-full`; marker is consumed by DaisyUI Tom Select when enabled. | `form-select`; marker is consumed by Bootstrap Tom Select when enabled. | `data-powercrud-searchable-select=true` is emitted for eligible relation/choice metadata; boolean is excluded. | [`metadata_mixin.py:102-133`](../../../src/powercrud/mixins/bulk_mixin/metadata_mixin.py#L102-L133), [`daisyui/partial/bulk_fields.html:35-47,73-85`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/bulk_fields.html#L35-L47), [`bootstrap5/partial/bulk_fields.html:16-24`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/bulk_fields.html#L16-L24) |
| Bulk: multiselect | Pack template creates a native multiple select; three native radios choose add/remove/replace semantics. | Tall `select ... min-h-[150px] h-auto`; `radio radio-xs` controls. No searchable marker. | `form-select` multiple; Bootstrap radio controls. No searchable marker. | Pack bulk script initializes/enables only single searchable selects; M2M remains native. | [`daisyui/partial/bulk_fields.html:48-71`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/bulk_fields.html#L48-L71), [`bootstrap5/partial/bulk_fields.html:20-22`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/bulk_fields.html#L20-L22), [`metadata_mixin.py:111-113`](../../../src/powercrud/mixins/bulk_mixin/metadata_mixin.py#L111-L113) |
| Bulk: number/text fallback | Pack template creates `input type=number` with integer step `1` or decimal step `any`; all other unhandled types use `input type=text`. | `input input-bordered w-full`. | `form-control`. | No marker; pack script toggles disabled state when field-selection checkbox changes. | [`daisyui/partial/bulk_fields.html:87-95`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/bulk_fields.html#L87-L95), [`bootstrap5/partial/bulk_fields.html:25-29`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/bulk_fields.html#L25-L29) |
| Bulk: time/file | No explicit branches. Static source therefore identifies the text fallback as the current specified output, but whether each model field reaches this template is not tested in the reviewed focused suite. | DaisyUI text fallback if reached. | Bootstrap text fallback if reached. | None. | [`daisyui/partial/bulk_fields.html:87-95`](../../../src/powercrud/templates/powercrud/packs/daisyui/partial/bulk_fields.html#L87-L95), [`bootstrap5/partial/bulk_fields.html:25-29`](../../../src/powercrud/contrib/bootstrap5/templates/powercrud/packs/bootstrap5/partial/bulk_fields.html#L25-L29) |

## 5. Surface Summaries

### Generated create/update forms

`FormMixin.get_form_class()` uses an explicit application `form_class` when one
is configured; that path is excluded from this inventory. Otherwise it calls
`modelform_factory` with configured `form_fields`. Only model date, datetime, and
time fields receive explicit widgets; all other generated widgets are Django's
normal model-form mappings. Crispy enablement adds a `FormHelper` with
`form_tag=False` and `disable_csrf=True`, but does not replace the widgets
(`form_mixin.py:592-627, 673-733`).

### Inline editing

Inline construction calls `get_form_class()`, instantiates it, and runs the same
dependency and searchable-marker finalization with `inline=True`. Rendering is
pack-owned: DaisyUI's native branch prints the bound field, while Bootstrap's
inline row invokes the Bootstrap field tag. Inline dependency responses render
the selected pack's `partial/inline_field.html` and carry dependency markers
(`inline_editing_mixin.py:220-233`; pack inline partials cited in the matrix).

### Automatically generated filters

`FilteringMixin` obtains `filter_attrs` from the selected server adapter and
constructs a filter class/widget pair for each model field. Text, date, number,
boolean, relation, multiselect, and time branches are explicit. Searchable
markers are applied after construction, and HTMX trigger attributes are attached
by `HTMXFilterSetMixin`. Custom filtersets are intentionally not characterized
as a design target here, even though a compatibility styling pass exists.

### Bulk editing

Bulk metadata is generic (`type`, relation/M2M flags, choices, and
`searchable_select` eligibility), but the visible field controls are literal
pack templates. Each field is gated by a separate “fields to update” checkbox;
the pack script shows/enables the corresponding value input. The M2M control is
currently a tall native multiple select with add/remove/replace radios in both
packs.

### Native and Crispy paths

The selected pack's `partial/form_fields.html` preserves both paths. DaisyUI's
native path is a direct `{{ form }}` include and its Crispy path delegates to
`{% crispy form %}`. Bootstrap's native path explicitly renders every visible
field with `bootstrap5_field`; its Crispy path also delegates to `{% crispy
form %}`. Pack-specific inline layouts are explicit, but the normal Crispy
integration's exact output remains owned by the configured Crispy pack.

## 6. Current Ownership Findings

- **Django:** default model-form widget classes and values/choices/querysets,
  validation, required/disabled state, multipart semantics, and native
  single/multi-value submission.
- **Generic PowerCRUD:** temporal widget overrides in normal generated forms;
  generated filter widget construction and filter attributes supplied by the
  selected server adapter; inline number conversion and semantic inline markers;
  searchable-select semantic markers; bulk metadata and field eligibility.
- **DaisyUI pack:** filter class/style mapping; native/Crispy form fragments;
  inline Crispy layout; all bulk field markup and browser toggling; DaisyUI
  Tom Select presentation adapter.
- **Bootstrap pack:** filter class/style mapping; native `bootstrap5_field`
  renderer; inline field renderer and Crispy layout; all bulk field markup and
  browser toggling; Bootstrap Tom Select presentation adapter.
- **`templatetags/powercrud.py`:** no widget selection. The relevant
  `get_form_field` filter only looks up a bound field for a template
  (`templatetags/powercrud.py:261-272`).

## 7. Existing Test Evidence

The following focused tests confirm declared behavior without requiring this
inventory to run them:

- Generated date widget and Crispy helper: [`test_form_mixin_extended.py:137-160`](../../../src/tests/test_form_mixin_extended.py#L137-L160).
- Generated form searchable marker, boolean-like exclusion, global toggle, and
  per-field opt-out: [`test_form_mixin_extended.py:749-810`](../../../src/tests/test_form_mixin_extended.py#L749-L810).
- Auto-filter select/multiselect markers and per-field opt-out:
  [`test_form_filter_template_mixins.py:90-184`](../../../src/tests/test_form_filter_template_mixins.py#L90-L184).
- Bulk metadata searchable eligibility and focused DaisyUI bulk markup:
  [`test_bulk_view_mixin.py:579-678`](../../../src/tests/test_bulk_view_mixin.py#L579-L678).
- Shared native/Crispy selected-pack form matrix:
  [`test_template_pack_behaviour_matrix.py:178-223`](../../../src/tests/test_template_pack_behaviour_matrix.py#L178-L223).
- Bootstrap native/Crispy validation, Bootstrap classes, and accessible
  described-by/error output: [`test_bootstrap_template_pack.py:392-440`](../../../src/tests/test_bootstrap_template_pack.py#L392-L440).
- Bootstrap field-tag classification for checkbox, select, and file controls:
  [`test_template_packs.py:440-454`](../../../src/tests/test_template_packs.py#L440-L454).
- Inline component and dependency template resolution:
  [`test_inline_editing_mixin.py:1167-1198`](../../../src/tests/test_inline_editing_mixin.py#L1167-L1198).

These tests are evidence of the repository's contracts and assertions. No tests,
builds, containers, or browser checks were run for this inventory task.

## 8. Unverified or Ambiguous Behaviour

1. The exact Django HTML emitted for the native DaisyUI `{{ form }}` path varies
   with Django's installed version and model field configuration; source confirms
   ownership but not a complete rendered DOM snapshot.
2. Normal-form Crispy output is delegated to the application's configured
   integration. The first-party inline layouts are explicit, but the exact
   normal-form Crispy classes are not defined in PowerCRUD's pack fragments.
3. Auto-generated datetime filters have no dedicated branch. The current order
   (`DateField` before `TimeField`) appears to route `DateTimeField` through the
   date branch, but this should be confirmed with a runtime fixture before a
   future policy treats it as contractual.
4. No explicit auto-filter or bulk-file widget path is present. Bulk time and
   file fields also have no branch and therefore appear to use the text fallback;
   reaching those branches for every supported model field is not covered by the
   focused tests inspected.
5. This inventory did not run a browser. Tom Select enhancement, native-select
   hiding/restoration, dropdown sizing, and HTMX replacement behavior are
   established by adapter source and marker tests, but their current visual
   browser output remains a later Phase 1 baseline activity.
6. Application custom `form_class` and `filterset_class` behavior is deliberately
   excluded, so this document makes no policy claim about their widget choices.

## 9. Completion

Phase 1.1 inventory is complete. The document records current control ownership,
pack handling, markers/adapters, and available source/test evidence. Future
widget-policy design and the later inline M2M improvement remain separate work.
