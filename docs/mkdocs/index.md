# Home

**Advanced CRUD for perfectionists with deadlines. An opinionated extension of [`Neapolitan`](https://github.com/carltongibson/neapolitan).**

PowerCRUD respects Neapolitan’s foundations while supplying the practical UX and async tooling that most projects end up building themselves.

!!! info "Project status"
    PowerCRUD is still evolving, but now ships with a full pytest suite (including Playwright smoke tests). Expect breaking changes while APIs settle, and pin the package if you rely on current behaviour.

## Where to start

1. **First view online**

    - [Getting Started](guides/getting_started.md) for installation and base template requirements.  
    - [Setup & Core CRUD basics](guides/setup_core_crud.md) for filters, pagination, and modals.

2. **Improve day-to-day editing**  

    - [Inline editing](guides/inline_editing.md) to adjust rows in place.  
    - [Bulk editing (synchronous)](guides/bulk_edit_sync.md) for multi-record updates with validation controls.

3. **Handle long-running work**  

    - [Async Manager](guides/async_manager.md) explains locks, progress storage, and reusable helpers.  
    - [Bulk editing (async)](guides/bulk_edit_async.md) queues jobs through django-q2.  
    - [Async dashboard add-on](guides/async_dashboard.md) persists lifecycle data.

4. **Tune styling and behaviour**  

    - [Styling & Tailwind](guides/styling_tailwind.md) covers framework options and safelists.  
    - [Customisation tips](guides/customisation_tips.md) shows template overrides, extra actions, and mixin hooks.

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

- Configuration reference: [config_options.md](reference/config_options.md)  
- Complete class example: [complete_example.md](reference/complete_example.md)  
- Tooling: [dockerised_dev.md](reference/dockerised_dev.md), [mgmt_commands.md](reference/mgmt_commands.md), [testing.md](reference/testing.md)  
- Sample app overview: [sample_app.md](reference/sample_app.md)  
- Planned enhancements: [enhancements.md](reference/enhancements.md)

PowerCRUD is still moving; pin releases if you rely on specific behaviour and check these guides when upgrading.
