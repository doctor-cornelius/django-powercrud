# Pagination

Enable pagination with user-selectable page sizes and HTMX integration.

## Basic Setup

```python
class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    base_template_path = "core/base.html"
    fields = ["title", "author", "published_date"]
    
    paginate_by = 25  # Enable pagination with default page size
```

## User Experience

When pagination is enabled:

- Users see a page size dropdown with options: 5, 10, 25, 50, 100, All
- Custom `paginate_by` values are automatically added to the dropdown
- Page size selection persists across navigation and modal operations
- Filter and sort parameters are preserved across pages
- Filters automatically reset to page 1 when applied

## HTMX Integration

With `use_htmx = True`, pagination updates without page reloads:

```python
class BookCRUDView(NominopolitanMixin, CRUDView):
    model = models.Book
    base_template_path = "core/base.html"
    paginate_by = 25
    use_htmx = True
    
    # Works seamlessly with other features
    filterset_fields = ["author", "published_date"]
    bulk_fields = ["status"]
```

## Performance Tips

- Use smaller page sizes (10-15) for complex data
- Use larger page sizes (50-100) for simple lists
- Consider database optimization for large datasets

## Configuration Reference

| Setting       | Type | Default | Purpose                                |
| ------------- | ---- | ------- | -------------------------------------- |
| `paginate_by` | int  | `None`  | Default page size (enables pagination) |
| `use_htmx`    | bool | `False` | Enable reactive pagination             |