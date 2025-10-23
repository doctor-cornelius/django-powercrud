# Technology Stack & Technical Details

## Core Technologies

### Backend Framework
- **Django 5.1+** - Primary web framework
- **Python 3.12** - Programming language
- **neapolitan 24.8+** - Base CRUD view package that powercrud extends

### Frontend Technologies
- **HTMX** - Reactive web interactions without complex JavaScript
- **Alpine.js** - Minimal JavaScript framework for modal interactions
- **Popper.js** - Tooltip and popover positioning for table column truncation

### CSS Frameworks (Supported)
- **Bootstrap 5** - Default CSS framework with comprehensive component library
- **daisyUI** - Tailwind CSS component library (v5 with Tailwind v4)
- **Tailwind CSS** - Utility-first CSS framework (underlying daisyUI)

### Form Handling
- **Django Crispy Forms** - Enhanced form rendering
- **crispy-bootstrap5** - Bootstrap 5 integration for crispy forms
- **crispy-tailwind** - Tailwind CSS integration for crispy forms
- **crispy-daisyui** - DaisyUI integration for crispy forms

### Data Validation
- **Pydantic 2.10.6+** - Configuration validation and type checking

### Template System
- **django-template-partials 24.4+** - Partial template rendering support

### Asset Management
- **Vite** - Modern build tool for CSS/JS assets
- **django-vite 3.1.0+** - Django integration for Vite

### Async Processing
- **django-q2 1.8.0+** - Async task processing for bulk operations
- **Celery 5.4.0+** - Alternative async task processing backend
- **django-celery-beat 2.7.0+** - Periodic task scheduling for Celery

### Database Systems
- **PostgreSQL** - Primary database for development and production
- **psycopg 3.2.1+** - PostgreSQL adapter for Python
- **psycopg-binary 3.2.1+** - Binary distribution of psycopg

### Caching & Session Storage
- **Redis 5.2.0+** - In-memory data structure store for caching
- **django-redis 5.4.0+** - Redis cache backend for Django

## Development Setup

### Package Management
- **Poetry** - Dependency management and packaging
- **pyproject.toml** - Project configuration and dependencies

### Build Tools
- **Vite (vite.config.mjs)** - Asset compilation and development server
- **npm/package.json** - Frontend dependency management
- **Tailwind CSS** - Utility-first CSS compilation

### Development Dependencies
- **commitizen** - Conventional commit formatting
- **pytest** - Testing framework (tests not yet implemented)
- **coverage** - Code coverage analysis
- **ipykernel** - Jupyter notebook support for development

### Documentation
- **MkDocs** - Documentation site generation
- **mkdocs-material** - Material Design theme for documentation
- **mkdocs-mermaid2-plugin** - Diagram support in documentation

## Technical Constraints

### Django Version Requirements
- **Minimum Django 5.1** - Required for latest features and security
- **Python 3.12+** - Modern Python features and performance improvements

### Database Considerations
- **PostgreSQL** - Primary database for development and production (config project)
- **SQLite** - Alternative for simple development setups
- **Session Storage** - Database-backed sessions for bulk selection persistence
- **Docker Support** - PostgreSQL containerized setup available

### Browser Support
- **Modern Browsers** - HTMX and modern CSS features require recent browser versions
- **JavaScript Required** - HTMX and Alpine.js functionality requires JavaScript enabled

### Performance Limitations
- **Large Datasets** - Bulk operations may need async processing for large record counts
- **Complex Queries** - Advanced filtering can generate complex SQL queries
- **Session Storage** - Bulk selections stored in database sessions

## Configuration Management

### Django Settings Integration
```python
# Required settings
INSTALLED_APPS = [
    "powercrud",
    "neapolitan", 
    "django_htmx",
    "template_partials",
]

# Framework selection
NOMINOPOLITAN_CSS_FRAMEWORK = 'bootstrap5'  # or 'daisyUI'

# Crispy forms configuration
CRISPY_TEMPLATE_PACK = 'bootstrap5'  # or 'tailwind'

# Tailwind safelist location
TAILWIND_SAFELIST_JSON_LOC = 'path/to/safelist/'

# django-q2 settings
Q_CLUSTER = {
    'name': 'powercrud',
    'workers': 1,
    'recycle': 500,
    'timeout': 250,
    'retry': 300,
    'orm': 'default',  # Use database instead of Redis
    'save_limit': 250,
    'queue_limit': 500,
}
```

### Middleware Requirements
```python
MIDDLEWARE = [
    # ... other middleware
    "django_htmx.middleware.HtmxMiddleware",  # Required for HTMX functionality
]
```

### Template Configuration
```python
TEMPLATES = [{
    'OPTIONS': {
        'builtins': [
            'django_htmx.templatetags.django_htmx',
            'template_partials.templatetags.partials',
        ],
    },
}]
```

## Asset Pipeline

### Vite Configuration (vite.config.mjs)
- **Development Server**: Port 5174 for hot reloading
- **Asset Compilation**: CSS/JS bundling and optimization
- **Django Integration**: django-vite for seamless asset serving

### CSS Framework Integration
- **Bootstrap 5**: CDN or local installation
- **Tailwind CSS**: Build process with class extraction
- **Custom Styles**: Framework-specific customizations

### JavaScript Dependencies
- **HTMX**: Core reactive functionality
- **Alpine.js**: Modal and interactive components
- **Popper.js**: Tooltip positioning for table features

## Database Schema

### Core Models
```python
# powercrud/models.py
class BulkTask(models.Model):
    """Tracks bulk operations for progress monitoring"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    model_name = models.CharField(max_length=100)
    operation = models.CharField(choices=OPERATION_CHOICES)
    total_records = models.IntegerField()
    processed_records = models.IntegerField(default=0)
    status = models.CharField(choices=STATUS_CHOICES)
    # ... additional fields for tracking and metadata
```

### Session Data Structure
```python
# Session storage for bulk selections and state
session['powercrud'] = {
    'bulk_selected': [list_of_ids],
    'filter_state': {dict_of_filters},
    'pagination_preferences': {dict_of_settings}
}
```

## Tool Usage Patterns

### Management Commands
```bash
# Template bootstrapping
python manage.py pcrud_mktemplate app.Model --all
python manage.py pcrud_mktemplate app.Model --list

# Tailwind class extraction
python manage.py pcrud_extract_tailwind_classes --pretty

# Documentation display
python manage.py pcrud_help --lines 50
```

### Development Workflow
1. **Asset Development**: `npm run dev` for Vite development server
2. **Asset Building**: `npm run build` for production assets
3. **Testing**: `pytest` (when tests are implemented)
4. **Documentation**: `mkdocs serve` for local documentation

### Deployment Considerations
- **Static Files**: Collect static files including compiled assets
- **Database Migrations**: BulkTask model requires migration
- **Session Backend**: Configure appropriate session storage for production
- **Async Workers**: Set up django-q2 workers for bulk operations

## Integration Points

### Neapolitan Integration
- **Extends CRUDView**: All functionality builds on neapolitan's base
- **URL Patterns**: Compatible with neapolitan's URL generation
- **Template System**: Extends neapolitan's template resolution

### Django Integration
- **Admin Interface**: BulkTask model registered in Django admin
- **Permissions**: Integrates with Django's permission system
- **Forms**: Compatible with Django's form system and crispy forms

### Third-Party Integrations
- **HTMX**: Deep integration for reactive functionality
- **Crispy Forms**: Automatic form styling when available
- **Pydantic**: Configuration validation and type safety

## Security Considerations

### CSRF Protection
- **Form Security**: All forms include CSRF tokens
- **HTMX Requests**: CSRF tokens included in HTMX requests
- **Bulk Operations**: Atomic transactions prevent partial updates

### Permission Handling
- **View-Level**: Standard Django view permissions apply
- **Bulk Operations**: Permissions checked for each operation
- **Session Security**: Bulk selections tied to user sessions

### Input Validation
- **Pydantic Validation**: Configuration parameters validated
- **Form Validation**: Standard Django form validation
- **Bulk Edit Validation**: `full_clean()` called on each object