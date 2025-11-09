# Possible Enhancements

ideas for possible enhancements:

- **Deal With Bootstrap**: Get rid of deprecated bootstrap templates altogether since they are just so out of date. It's confusing having them there.
- **A Better Way to Override Templates**: Other packages have better, more robust ways to allow template packs to be developed (eg see especially [`crispy-forms`](https://django-crispy-forms.readthedocs.io/en/latest/template_packs.html)). Maybe that would be better here too. And make `daisyUI` the first one?
- **Spreadsheet Model Interface**: beyond the inline row editing we have now. Something more like spreadsheet. Maybe `htmx` based cell by cell edits (although have to watch out for row-level inter-field dependencies), or maybe a datagrid like `tabulator-js` as a base (although maybe that's better as a separate library). 