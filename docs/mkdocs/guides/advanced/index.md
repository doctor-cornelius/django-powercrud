# Advanced Guides

These guides are for the point where you understand a PowerCRUD feature exists, but you need help structuring a real implementation around it.

They focus on patterns, tradeoffs, and the practical "why" behind an extension point. In other words, they sit between the quick setup guides and the formal reference pages.

Use this section when:

- the basic guide tells you how to turn a feature on, but not how to organise your app code around it
- the hooks reference tells you what a method does, but not when it is worth using
- you want a worked example that feels closer to a real project decision

Current advanced guides:

- [PowerCRUD Recipes](recipes.md) shows Base Configuration API patterns for common surfaces, queryset annotation columns, actions, selection flows, bulk persistence, and linked cells.
- [Queryset Annotation Fields](queryset_annotation_fields.md) explains how to expose queryset-backed calculated values as first-class list, sort, and generated-filter columns.
- [Saved Favourites](filter_favourites.md) explains the optional contrib app for per-user saved list states, including installation, enablement, and guard behavior when the app is absent.
- [Lazy Evaluation](lazy_evaluation.md) explains when to defer expensive row-action state and list-cell tooltip callbacks until the user interacts with that row or cell.
- [Permission-Aware Affordances](permission_aware_affordances.md) explains how to keep operation permission separate from row state and backend enforcement.
- [Persistence Hooks](persistence_hooks_sync.md) explains how to keep PowerCRUD in charge of validation and UI flow while moving the actual write into app services.
- [Async Bulk Persistence](persistence_hooks_async_bulk.md) explains how to keep sync and async bulk update behavior aligned without relying on a live view instance in the worker.

For the exact contracts and signatures, use the [Hooks reference](../../reference/hooks.md).
