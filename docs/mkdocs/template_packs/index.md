# Template Packs

Template packs let PowerCRUD use one supported presentation system while keeping the CRUD behaviour, view configuration, and application ownership rules consistent.

DaisyUI is the built-in compatible default. Bootstrap 5 is an optional supported pack. Select a pack in Django settings before the process starts; it is not a per-request, per-view, or runtime switch.

## What a pack provides

A pack supplies the templates and presentation details for PowerCRUD's standard screens. That includes list, form, detail, delete, filtering, modal, bulk, async, inline-editing, and favourites surfaces.

Your application still owns its base template. It decides the surrounding site layout, authentication chrome, and how the pack's frontend assets are loaded. PowerCRUD does not supply a complete HTML page shell.

## Supported packs

| Pack | Status | Forms | Asset entry |
| --- | --- | --- | --- |
| DaisyUI | Built-in default | Native Django forms; Crispy `tailwind` | The usual `config/static/js/main.js` PowerCRUD entry |
| Bootstrap 5 | Optional supported pack | Native Django forms; Crispy `bootstrap5` | `config/static/js/bootstrap5.js`, or the documented manual assets |

Native Django form rendering is available with both packs. If you enable Crispy Forms, configure the Crispy template pack that matches the selected PowerCRUD pack; PowerCRUD does not choose it for you.

## Choose the right guide

- [Selecting and configuring](selecting-and-configuring.md) covers the default, Bootstrap setup, assets, and form rendering.
- [Customising](customising.md) explains focused template overrides and ownership boundaries.
- [Authoring and publishing](authoring-and-publishing.md) records the maintained declaration contract and its current limits.
- [Testing and acceptance](testing-and-acceptance.md) explains what makes a supported pack release-ready.

## What does not change with a pack

Packs change presentation, not the core Django and PowerCRUD contracts. Your views, URLs, models, permissions, query behaviour, and application base template remain yours. Settings that accept CSS class strings are framework-specific inputs: write DaisyUI/Tailwind classes for DaisyUI or Bootstrap classes for Bootstrap. PowerCRUD does not translate class names between frameworks.

For the complete setting reference, see [Configuration options](../reference/config_options.md). For the sample application's default, focused-override, and Bootstrap configurations, see [Sample application](../reference/sample_app.md).
