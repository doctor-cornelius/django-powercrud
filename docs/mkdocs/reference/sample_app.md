# Sample Application

## Overview

The `sample` app provides a comprehensive demonstration of django-PowerCRUD features using a realistic book/author management system. It serves as both a testing environment during development and a reference implementation for developers learning the package.

## Models

The sample app includes four interconnected models that showcase different relationship types and field configurations:

=== "Author"

    - Basic fields: `name`, `bio`, `birth_date`
    - Properties: `has_bio`, `property_birth_date` 
    - Demonstrates property display in list/detail views

=== "Book"  

    - Core fields: `title`, `author` (ForeignKey), `published_date`, `isbn`, `pages`
    - Many-to-many: `genres` relationship
    - Advanced features: 
    - `isbn_empty` GeneratedField for complex database expressions
    - `uneditable_field` for testing non-editable fields
    - Custom `clean()` and `save()` methods
    - Delayed `delete()` method for async testing
    - Properties with custom display names
    - Unique constraint on `title` + `author`

=== "Genre"

    - Simple model: `name`, `description`, `numeric_string`
    - Custom validation in `clean()` method
    - Used for many-to-many relationships and filtering

=== "Profile"

    - OneToOneField to Author (tests 1:1 relationships)
    - ForeignKey to Genre (tests optional relationships)
    - Demonstrates related field handling in forms/filters

## CRUD Views

Each model has a dedicated CRUD view demonstrating different PowerCRUD features:

### BookCRUDView - Full Feature Demo

```python
class BookCRUDView(PowerCRUDMixin, CRUDView):
    # Comprehensive configuration showing:
    bulk_fields = ['title', 'published_date', 'bestseller', 'pages', 'author', 'genres']
    bulk_delete = True
    bulk_async = True
    
    filterset_fields = ['author', 'title', 'published_date', 'isbn', 'pages', 'genres']
    dropdown_sort_options = {"author": "name"}
    
    extra_buttons = [...]  # Custom action buttons
    extra_actions = [...]  # Additional row actions
```

### Other Views

- **GenreCRUDView**: Minimal configuration example
- **ProfileCRUDView**: OneToOneField and bulk operations
- **AuthorCRUDView**: Properties, filtering, and template debugging

## Management Commands

=== "Creating Test Data"

    ```bash
    # Create default authors (25) and books (50)
    ./manage.py create_sample_data

    # Create 100 authors and 1000 books
    ./manage.py create_sample_data --authors 100 --books 1000

    # Create 500 books with an average of 5 books per author
    ./manage.py create_sample_data --books 500 --books-per-author 5
    ```

    Generates realistic sample data:

    - Random author names and bios
    - Book titles, descriptions, publication dates, and ISBNs
    - Progress feedback during creation
    - Allows control over the distribution of books per author using `--books-per-author`.

=== "Clearing Test Data"

    ```bash
    ./manage.py clear_sample_data --all        # Delete everything
    ./manage.py clear_sample_data --books      # Books only
    ./manage.py clear_sample_data --authors    # Authors only (cascades to books)
    ```

    Safety features:

    - Only works when `DEBUG=True`
    - Handles protected foreign key relationships
    - Provides clear feedback on deletion counts

## Forms & Filters

### Custom Forms

- **BookForm**: Date widgets, field selection, crispy forms integration
- **AuthorForm**: Demonstrates form customization patterns

### Advanced Filtering  

- **BookFilterSet**: HTMX integration, custom widget attributes
- **AuthorFilterSet**: Inherits from `HTMXFilterSetMixin` for reactive filtering
- Shows crispy forms layout integration

## Development Use Cases

### Feature Testing

- **Bulk Operations**: Test edit/delete on multiple books with validation
- **Async Processing**: Book deletion includes artificial delay for async testing  
- **Complex Relationships**: M2M genres, ForeignKey authors, OneToOne profiles
- **Field Types**: Generated fields, boolean displays, date formatting

### UI/UX Testing

- **Modal Interactions**: All CRUD operations in modals
- **HTMX Features**: Reactive filtering, pagination, form updates
- **CSS Frameworks**: Easy switching between daisyUI and Bootstrap
- **Responsive Design**: Table layouts with column width controls

### Configuration Examples

- **Property Display**: Custom property names and formatting
- **Field Exclusions**: Hide sensitive/internal fields  
- **Custom Actions**: Additional buttons and row-level actions
- **Sorting & Filtering**: Advanced queryset manipulation

## Getting Started

1. **Run migrations:**

   ```bash
   ./manage.py migrate
   ```

2. **Create sample data:**

   ```bash
   ./manage.py create_sample_data
   ```

3. **Access the views:**

   - Books: http://localhost:8001/sample/bigbook/
   - Authors: http://localhost:8001/sample/author/
   - Genres: http://localhost:8001/sample/genre/
   - Profiles: http://localhost:8001/sample/profile/

4. **Test features:**

   - Try bulk edit operations on books
   - Use filtering and sorting
   - Test modal create/edit/delete
   - Experiment with different page sizes

## Development Notes

The sample app is designed to be:

- **Comprehensive**: Covers all major PowerCRUD features
- **Realistic**: Uses believable domain models and relationships  
- **Educational**: Clear examples of configuration patterns
- **Extensible**: Easy to add new models or features for testing

When developing new PowerCRUD features, add corresponding examples to the sample app to ensure comprehensive testing coverage.