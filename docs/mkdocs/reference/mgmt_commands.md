# Management Commands

powercrud provides several management commands to help with setup, template customization, and Tailwind CSS integration.

## `pcrud_mktemplate` - Bootstrap CRUD Templates

Copy powercrud templates to your project for customization.

### Usage

```bash
# Copy all templates for an app
python manage.py pcrud_mktemplate myapp --all

# Copy all CRUD templates for a specific model
python manage.py pcrud_mktemplate myapp.Project --all

# Copy specific templates for a model
python manage.py pcrud_mktemplate myapp.Project --list
python manage.py pcrud_mktemplate myapp.Project --detail  
python manage.py pcrud_mktemplate myapp.Project --form
python manage.py pcrud_mktemplate myapp.Project --delete
```

### Arguments

- `target` - App name (e.g., `myapp`) or app.Model (e.g., `myapp.Project`)
- `model` - Model name (optional, can be specified as part of target)

### Options

- `--all` - Copy all templates (entire structure for app, or all CRUD templates for model)
- `--list` (`-l`) - Copy list template only
- `--detail` (`-d`) - Copy detail template only  
- `--create` (`-c`) - Copy create template only
- `--update` (`-u`) - Copy update template only
- `--form` (`-f`) - Copy form template only
- `--delete` - Copy delete template only

### Examples

```bash
# Copy entire template structure to myapp
python manage.py pcrud_mktemplate myapp --all

# Copy all CRUD templates for Book model
python manage.py pcrud_mktemplate library.Book --all

# Copy just the list template for Book model
python manage.py pcrud_mktemplate library.Book --list
```

### Template Locations

Templates are copied to your app's template directory following Django conventions:

- **Source**: `powercrud/templates/powercrud/{framework}/`
- **Target**: `{app}/templates/{app}/{template_name}`

Where `{framework}` is determined by your `POWERCRUD_CSS_FRAMEWORK` setting.

---

## `pcrud_extract_tailwind_classes` - Extract Tailwind CSS Classes

Copy compiled CSS files and generate Tailwind safelist for your build process.

### Usage

```bash
# Basic usage (requires TAILWIND_SAFELIST_JSON_LOC setting)
python manage.py pcrud_extract_tailwind_classes

# Specify output location
python manage.py pcrud_extract_tailwind_classes --output ./config/

# Specify exact filename
python manage.py pcrud_extract_tailwind_classes --output ./config/safelist.json
```

### Options

- `--output PATH` - Specify output path (directory or file path)
- `--legacy` - Use legacy method of extracting classes (currently unused)

### Configuration

Set the output location in your Django settings:

```python
# settings.py
POWERCRUD_SETTINGS = {
    'TAILWIND_SAFELIST_JSON_LOC': 'config'  # Creates BASE_DIR/config/powercrud_tailwind_safelist.json
    'TAILWIND_SAFELIST_JSON_LOC': 'config/safelist.json'  # Uses exact filename
    # ... other settings
}
```

### Examples

```bash
# Using settings configuration
python manage.py pcrud_extract_tailwind_classes

# Override with command line
python manage.py pcrud_extract_tailwind_classes --output ./static/css/

# Specify exact output file
python manage.py pcrud_extract_tailwind_classes --output ./tailwind/safelist.json
```

### Integration with Tailwind

Use the generated file in your `tailwind.config.js`:

```javascript
module.exports = {
  content: [
    // your content paths
  ],
  safelist: require('./config/powercrud_tailwind_safelist.json')
}
```

See [Section 06](../guides/06_styling_tailwind.md) for more details.

---

## `pcrud_cleanup_async` - Cleanup Async Artifacts

Remove stale locks, progress keys, and dashboard rows left behind by completed or abandoned async tasks.

### Usage

```bash
# Human-readable summary
python manage.py pcrud_cleanup_async

# Structured output for scripts/monitoring
python manage.py pcrud_cleanup_async --json
```

### Behaviour

- Skips execution when `POWERCRUD_SETTINGS["ASYNC_ENABLED"]` is `False`.
- Inspects the cache of active tasks, checking `django_q.Task` for completion.
- Removes conflict locks and progress entries when safe, then calls the configured async manager’s `cleanup_dashboard_data`.
- Returns a summary dictionary (or JSON) detailing cleaned and skipped tasks.

### Example summary

```
PowerCRUD Async Cleanup Summary
Active tasks inspected: 3

Cleaned 2 task(s):
  - 9f2b... (completed successfully) [locks=5, progress=1, dashboard=1]
  - 174c... (completed with failure) [locks=3, progress=1, dashboard=1]

Skipped 1 active task(s):
  - 2cd0...: task still running
```

Use the JSON mode to feed the data into logging or alerting pipelines.

---

## `pcrud_help` - Open Documentation

Opens the powercrud documentation in your default browser.

### Usage

```bash
python manage.py pcrud_help
```

### Behavior

Opens your default web browser to the powercrud documentation at:
`https://your-docs-url.github.io/django-powercrud/` *(placeholder URL)*

!!! note "Documentation URL"
    The actual documentation URL will be updated when the docs are published.

---

## Common Use Cases

### Initial Setup

```bash
# 1. Copy templates for customization
python manage.py pcrud_mktemplate myapp --all

# 2. Generate Tailwind safelist (if using Tailwind)
python manage.py pcrud_extract_tailwind_classes --output ./config/
```

### Template Customization Workflow

```bash
# Copy specific templates you want to modify
python manage.py pcrud_mktemplate myapp.Book --list
python manage.py pcrud_mktemplate myapp.Book --form

# Templates are now in myapp/templates/myapp/ for customization
```

### Tailwind CSS Workflow

```bash
# Generate safelist for Tailwind build
python manage.py pcrud_extract_tailwind_classes

# Add to your tailwind.config.js safelist
# Rebuild your CSS

# Optional: clear stale async state
python manage.py pcrud_cleanup_async --json
```
