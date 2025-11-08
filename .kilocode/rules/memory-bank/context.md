# Current Context

## Project Status
**Early Alpha Release (v0.2.27)** - Active development with frequent releases and breaking changes expected.

## Current Work Focus

### Recent Development (Last 10 Releases)
1. **Async Processing Implementation** - Added django-q2 and Celery support for bulk operations
2. **Infrastructure Modernization** - Moved Django project from `django_powercrud/` to `config/`
3. **Database Enhancement** - Added PostgreSQL support with Docker configuration
4. **Bulk Operations Enhancement** - Improved bulk edit/delete functionality with better error handling
5. **Dropdown Sorting** - Added `dropdown_sort_options` for related field sorting in filters and forms
6. **Pagination Improvements** - User-selectable page sizes that persist after operations
7. **Template System** - Enhanced template override capabilities and framework switching
8. **HTMX Integration** - Refined modal handling and form error display

### Active Features
- **Bulk Edit/Delete**: Atomic operations with validation and error handling
- **Inline Row Editing**: HTMX-powered inline editing with conflict detection and dependent fields
- **Advanced Filtering**: Dynamic filtersets with M2M logic options
- **Modal CRUD**: HTMX-powered modal forms for all CRUD operations
- **Async Processing**: django-q2 support for bulk operations with progress tracking and conflict management
- **Async Dashboard**: Lifecycle event persistence and monitoring for background tasks
- **Template Flexibility**: Bootstrap5 and daisyUI framework support (NB bootstrap will be deprecated in future release)
- **Management Commands**: Template bootstrapping and Tailwind class extraction

## Recent Changes

### Latest Release (0.2.27)
- Enhanced `BulkTask` model for comprehensive async task tracking.
- Implemented `mark_started`, `mark_completed`, `update_progress` methods in `BulkTask`.
- Added `task_key` and `unique_model_key` to `BulkTask` for duplicate prevention.
- Improved `BulkTask` status tracking with `PENDING`, `STARTED`, `SUCCESS`, `FAILURE` states.
- Added `clear_q2_queue` class method to `BulkTask` for debugging.
- Ensured `BulkTask` deletion also removes associated django-q2 tasks.

### Key Recent Features
- **Inline Row Editing**: HTMX-powered inline editing with conflict detection, dependent fields, and keyboard navigation
- **Async Processing**: Complete async backend implementation for bulk operations with django-q2 and Celery support
- **Async Dashboard**: Model tracking for lifecycle event persistence and monitoring
- **Enhanced Async Task Tracking**: Comprehensive `BulkTask` model for monitoring bulk operations
- **Improved Bulk Operation Reliability**: Better status tracking, error handling, and duplicate prevention for async tasks
- **Dropdown Sort Options**: Control sorting of related objects in dropdowns
- **Bulk Delete**: Separate control for bulk edit vs bulk delete operations
- **User Page Size Selection**: Persistent pagination preferences
- **Enhanced Error Handling**: Better bulk operation error display in modals
- **Filter Parameter Persistence**: Persist filter, pagination & sort params after single & bulk edit operations

## Next Steps

### Planned Features
1. **Async Processing**: Complete async backend implementation for bulk operations
2. **Additional CSS Frameworks**: Expand beyond Bootstrap5 and daisyUI
3. **Advanced Permissions**: Role-based access control for CRUD operations
4. **API Integration**: REST API endpoints for CRUD operations

### Non-Prioritised Enhancements
1. **Testing Framework**: Add comprehensive test suite (currently missing)
2. **Documentation**: Expand documentation beyond README
3. **Stability**: Reduce breaking changes as package matures
4. **Performance**: Optimize queryset handling for large datasets

## Development Environment

### Current Setup
- **Django 5.1+** with Python 3.12
- **Development Tools**: Poetry for dependency management, Vite for asset building
- **CSS Frameworks**: daisyUI/Tailwind CSS (default) Bootstrap5 (will be reconsidered)
- **Frontend**: Javascript, HTMX, Alpine.js, Popper.js for enhanced interactions
- **Database**: PostgreSQL with Docker containerization
- **Async Processing**: django-q2 for bulk operations, Celery support planned
- **Caching**: Redis for session storage and caching

### Sample Application
- Comprehensive sample app with Author, Book, Genre, Profile models
- Demonstrates all major features and configuration options
- Management commands for sample data creation/deletion

## Known Issues & Limitations

### Current Limitations
1. **No Test Suite**: Package lacks automated testing
2. **Breaking Changes**: Frequent API changes in alpha stage
3. **Limited Documentation**: Primarily README-based documentation
4. **Framework Dependencies**: Requires specific versions of Django/neapolitan

### Technical Debt
1. **Error Handling**: Inconsistent error handling patterns across features
2. **Template Complexity**: Some templates have complex logic that could be simplified

## Community & Adoption

### Current State
- **Early Adopters**: Author is the only user at present
- **Feedback Loop**: Active development based on use in a downstream project
- **Contribution**: Open to community contributions and feature requests but not yet publicized

### Goals
- Stabilize API for broader adoption
- Potentially contribute features back to neapolitan core