# Home

**Advanced CRUD for perfectionists with deadlines. An opinionated Django package for shipping production-grade CRUD screens with filtering, bulk operations, inline editing, and async workflows.**

PowerCRUD extends [`Neapolitan`](https://github.com/carltongibson/neapolitan)’s view layer with the practical infrastructure needed for real operational interfaces.

!!! info "Project status"
    PowerCRUD is still evolving, but now ships with a full pytest suite. CI blocks on a curated Playwright smoke subset, while the full browser suite remains part of the local and release-preparation workflow. Expect breaking changes while APIs settle, and pin the package if you rely on current behaviour.

## Where to start

1. **First view online**

    - [Getting Started](guides/getting_started.md) for installation and base template requirements.  
    - [Setup & Core CRUD basics](guides/setup_core_crud.md) for the first full view configuration.
    - [Filtering](guides/filtering.md) for default vs optional filters, sorting, null helpers, and custom filterset behavior.

2. **Improve day-to-day editing**  

    - [Inline editing](guides/inline_editing.md) to adjust rows in place.  
    - [Forms](guides/forms.md) for generated vs custom forms, contextual display fields, disabled inputs, and parent/child dropdown queryset scoping.
    - [Bulk editing (synchronous)](guides/bulk_edit_sync.md) for multi-record updates with validation controls.
    - [Persistence Hooks](guides/advanced/persistence_hooks_sync.md) for moving validated writes into app services without scattering save logic.

3. **Handle long-running work**  

    - [Async Manager](guides/async_manager.md) explains locks, progress storage, and reusable helpers.  
    - [Bulk editing (async)](guides/bulk_edit_async.md) queues jobs through django-q2.  
    - [Async Bulk Persistence](guides/advanced/persistence_hooks_async_bulk.md) shows how to keep sync and async bulk update behavior aligned.
    - [Async dashboard add-on](guides/async_dashboard.md) persists lifecycle data.

4. **Tune styling and behaviour**  

    - [Styling & Tailwind](guides/styling_tailwind.md) covers framework options and safelists.  
    - [Customisation tips](guides/customisation_tips.md) shows template overrides, extra actions, and mixin hooks.
    - [PowerCRUD Concepts](guides/concepts.md) puts the setup guides in perspective and explains the mental model behind surfaces, field intent, actions, presentation, selection, bulk work, and async work.
    - [Structured API](guides/structured_api/index.md) explains when to use `PowerField`, `PowerAction`, and `PowerButton` for repeated field and action config.
    - [Advanced Guides](guides/advanced/index.md) collects deeper implementation walkthroughs for trickier extension patterns, including the optional saved favourites add-on.
    - [PowerCRUD Recipes](guides/advanced/recipes.md) shows Base Configuration API patterns you can adapt.

!!! tip "Two API styles"
    PowerCRUD's Base Configuration API uses class attributes, hooks, lists, and dictionaries directly. The Structured Declaration API uses `PowerField`, `PowerAction`, and `PowerButton` to group repeated intent into reusable declaration objects. Both styles use the same runtime behavior.

## What ships in the box

- Enhanced CRUD views with property support, field exclusions, and customizable display options
- Modal-based create, edit, and delete forms with HTMX integration
- Inline row editing with HTMX-powered reactive updates and conflict detection
- Sortable tables with pagination and responsive column controls
- Reactive filtering and search with M2M logic and custom queryset handling
- Bulk edit and delete operations with atomic transactions and async processing
- Async task management with progress tracking, conflict locks, and lifecycle monitoring
- daisyUI/Tailwind styling with template flexibility and framework extension points
- Crispy forms integration and HTML5 widgets
- Management commands for template bootstrapping and asset utilities
- Comprehensive sample app and Docker development setup

## Async in brief

1. View reserves locks and enqueues a worker.  
2. Worker runs via django-q2, updates progress, and returns results.  
3. Completion hook clears locks, emits lifecycle events, and optionally records dashboard rows.  
4. Cleanup command or schedule reconciles anything stuck.

See [Async architecture](reference/async.md) for details.

## Reference map

- Base Configuration API reference: [config_options.md](reference/config_options.md)
- Concepts guide: [concepts.md](guides/concepts.md)
- Structured API guide: [Choosing an API Style](guides/structured_api/index.md)
- PowerField guide/reference: [guide](guides/structured_api/powerfields.md), [reference](reference/powerfields.md)
- PowerAction and PowerButton guide/reference: [guide](guides/structured_api/poweractions.md), [reference](reference/poweractions.md)
- Hooks reference: [hooks.md](reference/hooks.md)  
- Complete class example: [complete_example.md](reference/complete_example.md)  
- Tooling: [dockerised_dev.md](reference/dockerised_dev.md), [mgmt_commands.md](reference/mgmt_commands.md), [testing.md](reference/testing.md)  
- Sample app overview: [sample_app.md](reference/sample_app.md)  
- Planned enhancements: [enhancements.md](reference/enhancements.md)

PowerCRUD is still moving; pin releases if you rely on specific behaviour and check these guides when upgrading.
