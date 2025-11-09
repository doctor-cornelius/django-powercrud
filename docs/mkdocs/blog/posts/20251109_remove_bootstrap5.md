---
date: 2025-11-09
categories:
  - templates
  - css
---
# Removing `bootstrap5` Templates

The `bootstrap5` templates are very out of date because all of the development has gone into `daisyUI` templates. The continuing presence of the `bootstrap5` templates creates confusion. I have in mind a future simplification and modularisation of the template system (something along the lines of template packs like `crispy-forms` does) but that won't be for a while. So in the meantime, it's better to just remove `bootstrap5` completely. This is the plan to do that.
<!-- more -->

## Task List

1. [x] Remove the entire app template pack at `src/powercrud/templates/powercrud/bootstrap5/` plus every file underneath it.
2. [x] Drop the sample project equivalents inside `src/sample/templates/sample/bootstrap5/`.
3. [x] Delete all `bootstrap5`-specific crispy helper code in `src/powercrud/mixins/htmx_mixin.py`.
4. [x] Remove the template pack handling in `src/powercrud/management/commands/pcrud_mktemplate.py`.
5. [x] Update `src/sample/filters.py` so crispy helpers no longer reference `bootstrap5/layout/inline_field.html`.
6. [x] Strip `bootstrap5` from `src/tests/settings.py` (allowed packs, installed apps) and from `src/config/settings.py`.
7. [x] Remove the dependency on `crispy-bootstrap5` from `pyproject.toml`, `uv.lock`, and any other dependency manifests.
8. [ ] Documentation cleanup:
    1. [x] Update `README.md` so it no longer mentions `bootstrap5`.
    2. [x] Update `docs/mkdocs/index.md` to remove any `bootstrap5` references.
    3. [x] Update `docs/mkdocs/guides/styling_tailwind.md` to reflect the removal.
    4. [x] Update `docs/mkdocs/reference/mgmt_commands.md` so it no longer references `bootstrap5`.
    5. [x] Update `docs/mkdocs/guides/getting_started.md` to remove `bootstrap5` references.
    6. [x] Update `docs/mkdocs/reference/config_options.md` to mention only current frameworks.
9. [x] Scan the repository for `bootstrap5` references after the above work to ensure no lingering docs or comments remain.
