# Testing and Accepting a Template Pack

A supported pack needs evidence that it preserves PowerCRUD's behaviour as well as its own presentation and assets. Equivalent behaviour matters; identical HTML, CSS classes, or pixels do not.

## Start with declaration validation

The declaration must have a valid identity, contract version, template package and resource root, adapter information, capability set, form support, and asset metadata. Validation should fail clearly when a declaration is malformed or claims an unsupported presentation exception.

Run the public helper from the pack's own test project after adding the pack app to `INSTALLED_APPS`:

```python
from powercrud.template_pack_testing import assert_template_pack_conforms


def test_pack_contract():
    assert_template_pack_conforms(
        "my_powercrud_pack.template_pack:template_pack"
    )
```

It validates shipped templates, declared static resources, adapter imports, claimed capabilities, and optional Crispy dependencies without relying on PowerCRUD's internal first-party fixtures.

## Cover shared behaviour and pack-specific details

Every supported pack is expected to pass the shared server behaviour matrix for the standard CRUD surfaces. Add pack-specific server checks for translated presentation settings, declared resources, and any pack-owned templates or assets.

Portable presentation options must keep their promised meaning across the maintained packs. Framework-specific class settings may differ by framework, but they should not become silent no-ops.

## Check the installed distribution

Test the built wheel and source distribution, not only the source checkout. Confirm that template resources and declared assets are present after installation and that the selected pack resolves successfully in that environment.

For an independent pack, put the clean-install check in that package repository: install its built artifact alongside the intended PowerCRUD release, configure a minimal Django project, and run the same conformance helper. This must cover both wheel and source distribution. PowerCRUD does not need to know the package name in advance.

## Use browser tests for browser risks

Use focused Playwright coverage where a server test cannot see the problem: HTMX reinitialisation, modal or dropdown ownership, focus, responsive overflow, and asset loading are typical examples.

Run the broad project suite for release preparation and use focused test selections while developing a bounded pack change. The full commands and environment notes are in [Testing PowerCRUD](../reference/testing.md).

## Acceptance checklist

- The declaration resolves and reports accurate capabilities, form support, and assets.
- Shared server behaviour passes for every supported surface.
- Pack-specific presentation and resource checks pass.
- Installed wheel and source-distribution resources are present and usable.
- Browser-only risks have focused Playwright evidence where relevant.
- Documentation tells users how to select the pack, load its assets, align Crispy Forms, and meet any vendor requirements.
