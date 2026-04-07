# Persistence Hooks for Real Write Logic

This guide is for the moment when normal CRUD behavior stops being enough.

Maybe saving a row should also:

- write an audit entry
- recalculate some summary data
- trigger a workflow check
- go through an app service that already owns the business rules

PowerCRUD can still handle validation, forms, modal responses, and HTMX flow. Your app can take over the actual write.

For the exact hook signatures, see the [Hooks reference](../../reference/hooks.md). This guide focuses on when these hooks are useful and how to structure them in a simple way.

---

## 1. The problem in everyday terms

Without persistence hooks, it is easy for write logic to end up scattered:

- one override for the normal form save
- another for inline save
- another for bulk update

That works for a while, but it is harder to maintain and easier to miss a save path later.

The sync persistence hooks solve that problem by giving you two clear places to take over writes:

- `persist_single_object()` for one validated object at a time
- `persist_bulk_update()` for sync bulk updates

---

## 2. What PowerCRUD still does for you

These hooks do not mean you are opting out of PowerCRUD.

PowerCRUD still handles:

- building and validating the form
- normalizing bulk-edit payloads
- modal and HTMX response handling
- list refresh behavior and success messages

Your app code only needs to answer one question:

> Now that the input is valid, how should this write actually happen?

---

## 3. When to use `persist_single_object()`

Use `persist_single_object()` when you want one service to own the actual save for a single row.

That hook covers:

- normal create forms
- normal update forms
- inline row updates

So if you want one place for single-row write orchestration, this is the hook.

---

## 4. A small write-service example

Here is a deliberately small service from the sample app:

```python
from sample.services import BookWriteService


class BookWriteService:
    """Small write service used by the persistence hook tutorials."""

    def save_book(self, *, form, mode):
        book = form.save(commit=False)
        book.save()
        form.save_m2m()
        return book
```

This is intentionally simple. The point is not the business logic itself. The point is that there is now one obvious place to put it.

In a real project, this service might also:

- write audit records
- call a domain service
- trigger downstream recalculation
- decide whether some extra side effect should happen for this model

---

## 5. Wiring the service into `BookCRUDView`

Then the CRUD view becomes very thin:

```python
from sample.services import BookWriteService


class BookCRUDView(SampleCRUDMixin):
    def persist_single_object(self, *, form, mode, instance=None):
        return BookWriteService().save_book(form=form, mode=mode)
```

That is the core idea:

- PowerCRUD validates the form
- your service owns the write
- the view just joins those two pieces together

---

## 6. `save_m2m()` in plain terms

This is the part that often confuses people at first.

If you call `form.save()` directly, Django handles the normal `ModelForm` save flow for you.

If you do **not** call `form.save()` directly, and instead do `form.save(commit=False)` so your service can control the write, then any many-to-many form values still need to be saved afterwards. That is what `form.save_m2m()` is for.

So the simple rule is:

- if your override just returns `form.save()`, you do not need to think about this
- if your override bypasses `form.save()`, you own any needed `form.save_m2m()`

---

## 7. When to use `persist_bulk_update()`

Use `persist_bulk_update()` when sync bulk edit should go through your own app service instead of going straight through the built-in row update path.

This is useful when a bulk update should still trigger app-level rules, such as:

- audit logging
- selective recalculation
- workflow checks
- one project-specific orchestration layer for multi-row changes

This hook is for **sync bulk update**. Bulk delete is separate, and async bulk update is covered in the next guide.

---

## 8. A small sync bulk-service example

The sample app includes a tutorial-oriented bulk service:

```python
from powercrud.bulk_persistence import (
    BulkUpdateExecutionContext,
    DefaultBulkUpdatePersistenceBackend,
)


class BookBulkUpdateService:
    """Small example service used by the sync bulk tutorial."""

    def apply(
        self,
        *,
        queryset,
        bulk_fields,
        fields_to_update,
        field_data,
        context,
        progress_callback=None,
    ):
        return DefaultBulkUpdatePersistenceBackend().persist_bulk_update(
            queryset=queryset,
            bulk_fields=bulk_fields,
            fields_to_update=fields_to_update,
            field_data=field_data,
            context=context,
            progress_callback=progress_callback,
        )
```

This example still uses PowerCRUD's built-in bulk update behavior. The point is that your app now has one clear bulk-write hook where extra orchestration can live.

---

## 9. Wiring sync bulk into `BookCRUDView`

```python
from sample.services import BookBulkUpdateService


class BookCRUDView(SampleCRUDMixin):
    def persist_bulk_update(
        self,
        *,
        queryset,
        fields_to_update,
        field_data,
        progress_callback=None,
    ):
        return BookBulkUpdateService().apply(
            queryset=queryset,
            bulk_fields=list(self.bulk_fields),
            fields_to_update=fields_to_update,
            field_data=field_data,
            context=self._build_bulk_update_execution_context(
                queryset=queryset,
                mode="sync",
            ),
            progress_callback=progress_callback,
        )
```

This keeps the view logic simple while giving your app one bulk-update service to grow later.

---

## 10. Which hook should I use?

- Use `persist_single_object()` when one validated object is being created or updated.
- Use `persist_bulk_update()` when a sync bulk edit should go through your own write orchestration.
- Use both when your project wants the same app-level service pattern for single-row and multi-row writes.

---

## 11. Next step

If sync bulk update might also run in the background in your project, continue with [Async Bulk Persistence Without Surprises](persistence_hooks_async_bulk.md).
