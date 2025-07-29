# System Architecture

## Core Architecture Pattern

Django PowerCRUD uses a modular **mixin-based architecture** that extends Django's class-based views through the `neapolitan` package. The system is built around a single primary mixin (`PowerCRUDMixin`) that combines multiple specialized mixins.

## Source Code Structure

### Primary Package: `/powercrud/`

#### Core Components
- **`__init__.py`** - Package initialization (empty)
- **`models.py`** - BulkTask model for async operation tracking
- **`admin.py`** - Django admin configuration
- **`apps.py`** - Django app configuration
- **`validators.py`** - Pydantic validators for configuration validation

#### Mixin Architecture: `/powercrud/mixins/`
The system uses a modular mixin approach:

1. **`core_mixin.py`** - `CoreMixin`
   - Fundamental setup and initialization
   - Field/property resolution logic
   - Queryset handling and sorting
   - Configuration validation with Pydantic

2. **`htmx_mixin.py`** - `HtmxMixin`
   - HTMX integration and response handling
   - Modal functionality
   - Framework-specific styling
   - Template rendering logic

3. **`filtering_mixin.py`** - `FilteringMixin`
   - Dynamic FilterSet generation
   - HTMX filter form attributes
   - M2M filter logic (AND/OR)
   - Custom filter queryset handling

4. **`bulk_mixin.py`** - `BulkMixin`
   - Bulk edit/delete operations
   - Atomic transaction handling
   - Field metadata processing
   - Selection persistence

5. **`form_mixin.py`** - Form handling and crispy forms integration
6. **`paginate_mixin.py`** - Pagination with HTMX support
7. **`table_mixin.py`** - Table styling and column management
8. **`url_mixin.py`** - URL generation and namespace handling
9. **`async_mixin.py`** - Async processing for bulk operations

#### Template System: `/powercrud/templates/`
Framework-specific template organization:
```
templates/powercrud/
├── bootstrap5/           # Bootstrap 5 templates
│   ├── base.html
│   ├── object_list.html
│   ├── object_detail.html
│   ├── object_form.html
│   ├── object_confirm_delete.html
│   ├── crispy_partials.html
│   └── partial/
│       ├── list.html
│       └── detail.html
└── daisyUI/             # DaisyUI/Tailwind templates
    ├── base.html
    ├── object_list.html
    ├── object_detail.html
    ├── object_form.html
    ├── object_confirm_delete.html
    ├── crispy_partials.html
    └── partial/
        ├── list.html
        ├── detail.html
        └── bulk_edit_form.html
```

#### Template Tags: `/powercrud/templatetags/`
- **`powercrud.py`** - Custom template tags for rendering
  - `action_links()` - Generate CRUD action buttons
  - `object_detail()` - Render object detail views
  - `object_list()` - Render object list tables
  - `extra_buttons()` - Generate additional action buttons
  - `get_proper_elided_page_range()` - Pagination helper

#### Management Commands: `/powercrud/management/commands/`
- **`pcrud_mktemplate.py`** - Bootstrap CRUD templates
- **`pcrud_extract_tailwind_classes.py`** - Extract Tailwind classes for safelist
- **`pcrud_help.py`** - Display README documentation

#### Asset Management: `/powercrud/assets/`
- **`manifest.json`** - Asset manifest for Vite integration
- **`django_assets/`** - Compiled CSS/JS assets

### Sample Application: `/sample/`
Comprehensive example implementation:
- **`models.py`** - Author, Book, Genre, Profile models with relationships
- **`views.py`** - Example CRUD views demonstrating all features
- **`forms.py`** - Custom form examples
- **`filters.py`** - Custom filter examples
- **Management commands for sample data**

### Django Project: `/config/`
Development/demo Django project (renamed from `django_powercrud/`):
- **`settings.py`** - Configuration for development with PostgreSQL and async support
- **`urls.py`** - URL routing
- **`wsgi.py`** - WSGI application
- **`asgi.py`** - ASGI application for async support
- **`static/`** - Static assets for demo

### Additional Infrastructure
- **`docker/`** - Docker configuration for development
  - **`docker-compose.yml`** - Multi-service development setup
  - **`dockerfile_django`** - Django application container
  - **`postgresql.conf`** - PostgreSQL configuration
- **`tasks.py`** - Async task functions for django-q2 and Celery backends

## Key Technical Decisions

### 1. Mixin-Based Design
**Decision**: Use multiple specialized mixins combined into one primary mixin
**Rationale**: 
- Separation of concerns
- Easier testing and maintenance
- Allows selective feature usage
- Follows Django's class-based view patterns

### 2. Pydantic Validation
**Decision**: Use Pydantic for configuration validation in `CoreMixin.__init__()`
**Rationale**:
- Type safety for configuration
- Clear error messages for misconfigurations
- Automatic validation of complex configuration options

### 3. Template Framework Abstraction
**Decision**: Support multiple CSS frameworks through template path switching
**Rationale**:
- Flexibility for different project requirements
- Easy framework switching without code changes
- Extensible to additional frameworks

### 4. HTMX-First Approach
**Decision**: Build reactive features around HTMX rather than custom JavaScript
**Rationale**:
- Minimal JavaScript complexity
- Server-side rendering maintained
- Progressive enhancement approach
- Easier debugging and maintenance

## Component Relationships

### Primary Flow
```
PowerCRUDMixin
├── CoreMixin (base functionality)
├── HtmxMixin (HTMX/modal support)
├── FilteringMixin (dynamic filters)
├── BulkMixin (bulk operations)
├── FormMixin (form handling)
├── PaginateMixin (pagination)
├── TableMixin (table styling)
├── UrlMixin (URL generation)
└── AsyncMixin (async processing)
```

### Data Flow
1. **Request** → CoreMixin (queryset, field resolution)
2. **Filtering** → FilteringMixin (dynamic filterset creation)
3. **Rendering** → HtmxMixin (template selection, modal handling)
4. **Response** → Template system (framework-specific rendering)

### Configuration Flow
1. **Class Definition** → Pydantic validation in `CoreMixin.__init__()`
2. **Field Resolution** → `_get_all_fields()`, `_get_all_properties()`
3. **Template Selection** → Framework-specific template paths
4. **Style Application** → `get_framework_styles()` method

## Critical Implementation Paths

### 1. CRUD Operations
- **List**: `CoreMixin.list()` → filtering → pagination → template rendering
- **Detail**: Standard neapolitan flow with enhanced template context
- **Create/Update**: Form handling → validation → modal response
- **Delete**: Confirmation → atomic deletion → response

### 2. Bulk Operations
- **Selection**: JavaScript-based selection with session persistence
- **Processing**: `BulkMixin.bulk_edit()` → atomic transactions → response
- **Error Handling**: Validation errors → modal redisplay with errors

### 3. Filtering
- **Dynamic Generation**: `FilteringMixin.get_filterset()` → field analysis → widget creation
- **HTMX Integration**: `HTMXFilterSetMixin.setup_htmx_attrs()` → reactive form fields
- **Query Processing**: Filter application → queryset modification

### 4. Template Resolution
- **Framework Detection**: Settings-based framework selection
- **Template Paths**: `templates_path` → framework-specific directories
- **Override System**: App-specific templates → fallback to package templates

## Design Patterns Used

### 1. **Mixin Pattern**
Multiple inheritance for feature composition

### 2. **Template Method Pattern**
Base methods with customizable hooks (e.g., `get_bulk_choices_for_field()`)

### 3. **Strategy Pattern**
Framework-specific styling through `get_framework_styles()`

### 4. **Factory Pattern**
Dynamic FilterSet creation in `FilteringMixin`

### 5. **Observer Pattern**
HTMX triggers for reactive updates

## Performance Considerations

### 1. **Queryset Optimization**
- Selective field loading based on configuration
- Related field optimization for display
- Stable sorting with secondary keys

### 2. **Template Caching**
- Framework-specific template resolution
- Template existence checking with fallbacks

### 3. **Session Management**
- Bulk selection persistence
- Filter state maintenance
- Pagination preferences

### 4. **Asset Management**
- Vite-based asset compilation
- Framework-specific CSS loading
- Tailwind class extraction for optimization