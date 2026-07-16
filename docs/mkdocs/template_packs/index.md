# Template Packs

Template packs let PowerCRUD use a presentation system while keeping the CRUD behaviour, view configuration, and application ownership rules consistent.

DaisyUI is the built-in compatible default. Bootstrap 5 is an optional supported pack. Select a pack in Django settings before the process starts; it is not a per-request, per-view, or runtime switch.

!!! warning "One complete pack per Django project/process"

    A Django project normally selects one complete pack in its settings for all of its running processes. It can give individual models or view classes different template overrides, but it cannot select different complete packs, browser adapters, or pack assets for different views, tenants, or requests. Choose the complete pack once at Django startup.

## What a pack provides

A pack supplies the templates and presentation details for PowerCRUD's standard screens. That includes list, form, detail, delete, filtering, modal, bulk, async, inline-editing, and favourites surfaces.

Your application still owns its base template. It decides the surrounding site layout and authentication chrome, and chooses the frontend route: PowerCRUD's packaged Vite entry, package-owned manual-static tags, or an application-owned entry. For the manual-static route, PowerCRUD can emit the selected pack's correctly ordered tags; it does not supply a complete HTML page shell or take over an application's frontend build.

## Maintained packs

| Pack | Status | Forms | Asset entry |
| --- | --- | --- | --- |
| DaisyUI | Built-in default | Native Django forms; Crispy `tailwind` | The usual `config/static/js/main.js` PowerCRUD entry |
| Bootstrap 5 | Optional maintained pack | Native Django forms; Crispy `bootstrap5` | `config/static/js/bootstrap5.js`, or the documented manual assets |

Native Django form rendering is available with both packs. If you enable Crispy Forms, configure the Crispy template pack that matches the selected PowerCRUD pack; PowerCRUD does not choose it for you.

| Selected PowerCRUD pack | Native forms | If the project uses Crispy Forms |
| --- | --- | --- |
| DaisyUI | Available | Configure Crispy's `tailwind` pack and its integration app. |
| Bootstrap 5 | Available | Configure Crispy's `bootstrap5` pack and its integration app. |
| Independently published pack | Available when the pack supports it | Follow that pack's documentation for its compatible Crispy integration, if any. |

## Choose a route before changing anything

| Your goal | Start here | What you own |
| --- | --- | --- |
| Use the built-in DaisyUI presentation | Leave the setting unset, then use the packaged DaisyUI entry. | Only your base template and normal application markup. |
| Use maintained Bootstrap 5 | Select Bootstrap and load its documented entry. | Your base template and Bootstrap's documented dependencies. |
| Change one screen or component in one project | Use a model or view override. | Only the copied templates. |
| Share copied templates across selected views | Use a project override with `template_override_path`. | The copied root templates; use `--all` only for complete template ownership. |
| Change a maintained pack's PowerCRUD CSS or JavaScript locally | Add `--assets` to an app-level copy. | A complete manual-static asset snapshot in that app. |
| Support a new CSS framework for multiple projects | Create and publish an independent pack. | The package's templates, adapters, assets, and release tests. |

The first two rows choose a process-wide pack. The middle rows are local overrides of that selected pack. The last row creates another selectable pack. This distinction is the quickest way to avoid copying more than you need.

## Choose the right guide

- [Selecting and configuring](selecting-and-configuring.md) covers the default, Bootstrap setup, assets, and form rendering.
- [Customising](customising.md) explains focused template overrides and ownership boundaries.
- [Authoring and publishing](authoring-and-publishing.md) shows how to create, test, publish, install, and select an independent pack for another CSS framework.
- [Testing and acceptance](testing-and-acceptance.md) explains what makes a supported pack release-ready.

## What does not change with a pack

Packs change presentation, not the core Django and PowerCRUD contracts. Your views, URLs, models, permissions, query behaviour, and application base template remain yours. Settings that accept CSS class strings are framework-specific inputs: write DaisyUI/Tailwind classes for DaisyUI or Bootstrap classes for Bootstrap. PowerCRUD does not translate class names between frameworks.

For the complete setting reference, see [Configuration options](../reference/config_options.md). For the sample application's default, focused-override, and Bootstrap configurations, see [Sample application](../reference/sample_app.md).
