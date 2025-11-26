# Django PowerCRUD

[![Run Test Matrix](https://github.com/doctor-cornelius/django-powercrud/actions/workflows/pr_tests.yml/badge.svg)](https://github.com/doctor-cornelius/django-powercrud/actions/workflows/pr_tests.yml)
[![codecov](https://codecov.io/github/doctor-cornelius/django-powercrud/branch/main/graph/badge.svg)](https://codecov.io/github/doctor-cornelius/django-powercrud)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](#supported-versions)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.2-0C4B33)](#supported-versions)
[![PyPI](https://img.shields.io/pypi/v/django-powercrud.svg)](https://pypi.org/project/django-powercrud/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen?logo=renovatebot)](https://developer.mend.io/github/doctor-cornelius/django-powercrud)

**Advanced CRUD for perfectionists with deadlines. An opinionated extension of [Neapolitan](https://github.com/carltongibson/neapolitan).**

PowerCRUD builds on Neapolitan’s view layer and adds the practical pieces you would otherwise wire up by hand.

## Why PowerCRUD

- **Production-ready CRUD – faster**  
  HTMX responses, modal forms, inline row editing, and filter sidebars are configured through class attributes rather than custom templates.

- **Bulk operations that scale**  
  Start synchronously with selection persistence and validation controls, then opt into async queueing with conflict locks, progress polling, and an optional dashboard when jobs run longer.

- **One async toolkit everywhere**  
  The async manager, conflict handling, and progress API are reusable from admin actions, management commands, or bespoke launch sites so background work behaves consistently.

- **Batteries included**  
  Sample app, Docker dev stack, management commands, Tailwind safelist tooling, and a maintained pytest/Playwright suite keep the project teachable and testable.

> ℹ️ **Status**
>
> PowerCRUD is still evolving, but now ships with a comprehensive pytest suite (including Playwright UI smoke tests). Expect rough edges while APIs settle, and pin the package if you rely on current behaviour.

See the [full documentation](https://doctor-cornelius.github.io/django-powercrud/).

## Key Features

- HTMX-enabled CRUD views with modal create/edit/delete flows.
- Inline row editing with dependency-aware widgets, lock checks, and permission guards.
- Bulk edit/delete with selection persistence and an optional async path.
- Async infrastructure: conflict locks, progress cache, django-q2 workers, cleanup command, optional dashboard persistence.
- Filtering, sorting, and pagination helpers backed by tuned templates.
- Styling controls (daisyUI/Tailwind) plus template scaffolding and Tailwind safelist extraction.
- Extension hooks for custom actions, buttons, and templates, illustrated in the bundled sample app.
- Tooling support: Dockerised dev environment, management commands, pytest + Playwright coverage.

## Quick Examples

### Core CRUD (synchronous)

```python
from neapolitan.views import CRUDView
from powercrud.mixins import PowerCRUDMixin


class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = Project
    base_template_path = "core/base.html"

    # Core configuration
    fields = ["name", "owner", "status", "created_date"]
    properties = ["is_overdue"]
    filterset_fields = ["owner", "status", "created_date"]
    paginate_by = 25

    # UX helpers
    use_htmx = True
    use_modal = True
    inline_edit_enabled = True
    inline_edit_fields = ["status", "owner"]

    # Bulk operations (synchronous)
    bulk_fields = ["status", "owner"]
    bulk_delete = True
```

This single view serves a filtered list, modal forms, inline edits, and synchronous bulk edits - no async stack required.

### Async bulk (opt-in)

```python
from neapolitan.views import CRUDView
from powercrud.mixins import PowerCRUDAsyncMixin


class ProjectAsyncCRUDView(PowerCRUDAsyncMixin, CRUDView):
    model = Project
    base_template_path = "core/base.html"

    bulk_fields = ["status", "owner"]
    bulk_delete = True
    bulk_async = True
    bulk_min_async_records = 20
    bulk_async_conflict_checking = True

    # Optional async dashboard manager
    async_manager_class_path = "myapp.async_manager.AppAsyncManager"
```

Here async queueing is explicit: you opt in by using `PowerCRUDAsyncMixin`, enabling `bulk_async`, and configuring django-q2 (`django_q` in `INSTALLED_APPS`, `Q_CLUSTER`, and any `POWERCRUD_SETTINGS` overrides you need).

## Getting Started

- Install `django-powercrud` and `neapolitan`, add `powercrud`, `neapolitan`, and `django_htmx`, then follow the [Getting Started](https://doctor-cornelius.github.io/django-powercrud/guides/getting_started/) guide for base template requirements.
- Continue with [Setup & Core CRUD basics](https://doctor-cornelius.github.io/django-powercrud/guides/setup_core_crud/) to enable filters, pagination, and modals.
- Add [Inline editing](https://doctor-cornelius.github.io/django-powercrud/guides/inline_editing/) and [Bulk editing (synchronous)](https://doctor-cornelius.github.io/django-powercrud/guides/bulk_edit_sync/), then move to [Async Manager](https://doctor-cornelius.github.io/django-powercrud/guides/async_manager/) and [Bulk editing (async)](https://doctor-cornelius.github.io/django-powercrud/guides/bulk_edit_async/) when you need background work.
- Use [Styling & Tailwind](https://doctor-cornelius.github.io/django-powercrud/guides/styling_tailwind/) and [Customisation tips](https://doctor-cornelius.github.io/django-powercrud/guides/customisation_tips/) to adapt templates.

## Tooling & References

- **Sample app** – complete walkthrough of every feature.  
- **Docker dev environment** – Django, Postgres, Redis, Vite, django-q2.  
- **Management commands** – template scaffolding, Tailwind safelist extraction, async cleanup.  
- **Testing** – pytest matrix plus Playwright smoke tests.

## Supported Versions

PowerCRUD is tested against the following combinations:

- Python 3.12 with Django 4.2 LTS and Django 5.2
- Python 3.13 with Django 4.2 LTS and Django 5.2
- Python 3.14 with Django 4.2 LTS and Django 5.2

We aim to keep the dependency lock compatible with each pairing; upcoming CI work will exercise this matrix automatically on pushes to `main`.

## Development Setup

PowerCRUD’s development environment is Docker-first. From the project root:

```bash
./runproj up          # build images, start services, enter the Django container
./runtests                # run the full test suite, including Playwright smoke tests
```

Dependencies are managed with [`uv`](https://github.com/astral-sh/uv); the Docker image installs them into the system interpreter so you never need to activate a virtual environment inside the container. See the [Dockerised Development Environment guide](https://doctor-cornelius.github.io/django-powercrud/reference/dockerised_dev/) for full details.
