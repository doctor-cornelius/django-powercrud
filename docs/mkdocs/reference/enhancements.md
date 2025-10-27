# Possible Enhancements

Planned and possible enhancements are listed below.

- **testing matrix**: using `tox` or if possible just `uv` in a clever way for different versions of python and django, etc.
- **Dependabot or Some Way to Keep Dependencies Updated**: mandatory for a published package. Also needs to work on keeping images updated, eg python versions. Maybe `renovate`.
- **A Better Way to Override Templates**: Other packages have better, more robust ways to allow template packs to be developed (eg see especially [`crispy-forms`](https://django-crispy-forms.readthedocs.io/en/latest/template_packs.html)). Maybe that would be better here too. And make `daisyUI` the first one?
- **Deal With Bootstrap**: Should we get rid of deprecated bootstrap templates altogether since they are just so out of date? Wouldn't it be better just to start fresh?
- **Inline Editing Within List**: Offer configurable inlines editing. See [inline editing](../blog/posts/20250825_inline_table_editing.md) and [child editing](../blog/posts/20250825_child_table_editing.md)
- **Local matrix tooling polish**: Provide `just` recipes (or similar) that install alternate Python interpreters via `uv` so contributors can replay every matrix cell locally without manual setup.
