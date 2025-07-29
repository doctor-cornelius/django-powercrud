# Management Commands

PowerCRUD provides several management commands to help with setup, template customization, and Tailwind CSS integration.

## `pcrud_mktemplate` - Bootstrap CRUD Templates

Copy PowerCRUD templates to your project for customization.

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

Where `{framework}` is determined by your `NOMINOPOLITAN_CSS_FRAMEWORK` setting.

---

## `pcrud_extract_tailwind_classes` - Extract Tailwind CSS Classes

Copy compiled CSS files and generate Tailwind safelist for your build process.

### Usage

```bash
# Basic usage (requires NM_TAILWIND_SAFELIST_JSON_LOC setting)
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
NM_TAILWIND_SAFELIST_JSON_LOC = 'config'  # Creates BASE_DIR/config/PowerCRUD_tailwind_safelist.json
NM_TAILWIND_SAFELIST_JSON_LOC = 'config/safelist.json'  # Uses exact filename
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
  safelist: require('./config/PowerCRUD_tailwind_safelist.json')
}
```

See [Tailwind CSS Integration](../configuration/styling.md#tailwind-css-integration) for more details.

---

## `pcrud_help` - Open Documentation

Opens the PowerCRUD documentation in your default browser.

### Usage

```bash
python manage.py pcrud_help
```

### Behavior

Opens your default web browser to the PowerCRUD documentation at:
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
```
