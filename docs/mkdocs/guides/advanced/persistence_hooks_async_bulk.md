# Async Bulk Persistence Without Surprises

This guide is about one practical goal:

> Sync bulk update and async bulk update should not behave differently by accident.

If your app uses extra write logic for bulk updates, you usually want that same logic to run whether the update happens in the request or in a background worker.

For the exact backend contract, see the [Hooks reference](../../reference/hooks.md) and the [configuration reference](../../reference/config_options.md). This guide focuses on the reasoning and the wiring.

---

## 1. The real problem

The sync hook `persist_bulk_update()` is useful, but it lives on the CRUD view.

That is fine for a normal request. It is not enough for async bulk update, because the background worker is not running with your live view instance.

So if your app needs one shared bulk-update write path for both sync and async execution, async needs a different extension point.

---

## 2. Why a view hook is not enough for worker code

The background worker cannot safely depend on your live request-time view object.

That means the async worker needs something else:

- importable
- worker-safe
- not tied to a request
- explicit about what it receives

That is why async bulk update uses a `BulkUpdatePersistenceBackend`.

---

## 3. Reuse the same bulk service

The nicest shape is usually:

- one service that owns the bulk write logic
- one sync hook that calls it
- one async backend that also calls it

The sample app's tutorial service stays the same:

```python
from sample.services import BookBulkUpdateService
```

So you do not need one implementation for sync and another for async. You only need different entry points.

---

## 4. Add a `BulkUpdatePersistenceBackend`

Here is the sample backend:

```python
from powercrud.bulk_persistence import BulkUpdatePersistenceBackend
from sample.services import BookBulkUpdateService


class BookBulkUpdateBackend(BulkUpdatePersistenceBackend):
    """Worker-safe backend used by the async bulk tutorial."""

    def persist_bulk_update(
        self,
        *,
        queryset,
        bulk_fields,
        fields_to_update,
        field_data,
        context,
        progress_callback=None,
    ):
        return BookBulkUpdateService().apply(
            queryset=queryset,
            bulk_fields=bulk_fields,
            fields_to_update=fields_to_update,
            field_data=field_data,
            context=context,
            progress_callback=progress_callback,
        )
```

This backend is for **bulk update only**.

It is not a general save hook, and it does not cover delete behavior.

---

## 5. Point the CRUD view at it

Once the backend exists, the view just names it:

```python
class BookCRUDView(SampleCRUDMixin):
    bulk_async = True
    bulk_update_persistence_backend_path = "sample.backends.BookBulkUpdateBackend"
```

Now PowerCRUD can resolve that backend in the async worker.

In the sample app, `BookCRUDView` also keeps a `persist_bulk_update(...)` override for the sync path, and both entry points call `BookBulkUpdateService`. That is intentional: the sample shows how to keep one bulk rule in one service while still using the right PowerCRUD seam for each execution mode.

Important:

- async bulk update uses this backend
- if you leave the sync hook alone, the default sync bulk path also uses this same backend when the path is configured
- that gives sync and async one shared bulk-update persistence contract

If that shared service returns `success=False`, the async task is marked failed. In the current release, that failure surfaces through task progress and async dashboard state rather than the sync modal-style field error UI.

---

## 6. What the context values are for

The backend gets plain execution context so it can make sensible decisions without depending on a live view.

The most useful values are:

- `context.mode` so your service can tell whether it is running in `"sync"` or `"async"`
- `context.task_name` so logs or audit rows can refer to the async task
- `context.user_id` so app services can associate the write with the initiating user
- `progress_callback` so long-running operations can report progress back through the existing async infrastructure

Most projects will not need every field. The point is that the backend receives enough plain data to do useful work safely.

---

## 7. When you do not need a backend

You do **not** need to configure a backend if:

- you are only using sync bulk update
- the built-in async bulk update behavior is fine
- you do not need special app-level orchestration around bulk updates

The backend exists for the cases where sync and async should share one deliberate write path.

---

## 8. Recap

- `persist_bulk_update()` is the sync bulk-update hook on the view.
- `BulkUpdatePersistenceBackend` is the worker-safe async bulk-update hook.
- When the backend path is configured, the default sync bulk path also uses it.
- Async bulk delete is still separate in the current release.

If you want the full contracts, return shapes, and related hook list, go back to the [Hooks reference](../../reference/hooks.md).
