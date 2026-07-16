"""Development and CI validation for declared PowerCRUD template packs."""

from importlib import import_module
from importlib.resources import files
from importlib.util import find_spec
from pathlib import PurePosixPath

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles import finders
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template

from powercrud.template_packs import (
    BROWSER_ADAPTER_API_VERSION,
    SERVER_ADAPTER_API_VERSION,
    TEMPLATE_PACK_CONTRACT_VERSION,
    TemplatePack,
)


BASELINE_CAPABILITIES = frozenset({"list", "form", "detail", "delete"})
OPTIONAL_CAPABILITIES = frozenset(
    {"filters", "modal", "bulk", "async", "inline", "favourites"}
)
CAPABILITY_DEPENDENCIES = {
    "async": frozenset({"bulk"}),
    "bulk": frozenset({"list"}),
    "favourites": frozenset({"list"}),
    "filters": frozenset({"list"}),
    "inline": frozenset({"list"}),
}
CAPABILITY_TEMPLATE_PATHS = {
    "list": frozenset(
        {
            "object_list.html",
            "partial/extra_buttons.html",
            "partial/list.html",
            "partial/list_actions.html",
            "partial/list_columns.html",
            "partial/page_size_selector.html",
            "partial/pagination.html",
            "partial/row_actions.html",
            "partial/table_header.html",
            "partial/table_row.html",
            "partial/table_shell.html",
        }
    ),
    "form": frozenset(
        {
            "object_form.html",
            "partial/form_actions.html",
            "partial/form_conflict.html",
            "partial/form_fields.html",
            "partial/form_shell.html",
        }
    ),
    "detail": frozenset(
        {
            "object_detail.html",
            "partial/detail.html",
            "partial/detail_content.html",
            "partial/detail_shell.html",
        }
    ),
    "delete": frozenset(
        {
            "object_confirm_delete.html",
            "partial/delete_actions.html",
            "partial/delete_conflict.html",
            "partial/delete_content.html",
            "partial/delete_shell.html",
        }
    ),
    "filters": frozenset(
        {
            "partial/filter_form.html",
            "partial/filter_panel_actions.html",
            "partial/filter_trigger.html",
        }
    ),
    "modal": frozenset(
        {
            "partial/modal.html",
            "partial/modal_content.html",
            "partial/modal_shell.html",
        }
    ),
    "bulk": frozenset(
        {
            "bulk_edit_form.html",
            "partial/bulk_edit_errors.html",
            "partial/bulk_fields.html",
            "partial/bulk_form.html",
            "partial/bulk_outcomes.html",
            "partial/bulk_selection_controls.html",
            "partial/bulk_selection_status.html",
        }
    ),
    "async": frozenset(),
    "inline": frozenset(
        {
            "layout/inline_field.html",
            "partial/inline_field.html",
            "partial/inline_row_display.html",
            "partial/inline_row_form.html",
            "partial/list.html",
        }
    ),
    # Favourites are a shared contrib component rather than a pack-owned
    # template surface, so they have no selected-pack resource requirement.
    "favourites": frozenset(),
}
CAPABILITY_FRAGMENT_PATHS = {
    "list": frozenset(
        {
            "object_list.html#filtered_results",
            "object_list.html#pagination",
            "object_list.html#pcrud_content",
        }
    ),
    "form": frozenset(
        {
            "object_form.html#normal_content",
            "object_form.html#pcrud_content",
        }
    ),
    "detail": frozenset({"object_detail.html#pcrud_content"}),
    "delete": frozenset(
        {
            "object_confirm_delete.html#normal_content",
            "object_confirm_delete.html#pcrud_content",
        }
    ),
    "filters": frozenset(),
    "modal": frozenset(),
    "bulk": frozenset(
        {
            "bulk_edit_form.html#full_form",
            "object_list.html#bulk_selection_status",
            "partial/bulk_edit_errors.html#bulk_edit_conflict",
            "partial/bulk_edit_errors.html#bulk_edit_error",
        }
    ),
    "async": frozenset(
        {
            "bulk_edit_form.html#async_queue_success",
            "object_confirm_delete.html#conflict_detected",
            "object_form.html#conflict_detected",
        }
    ),
    "inline": frozenset(
        {
            "partial/list.html#inline_row_display",
            "partial/list.html#inline_row_form",
        }
    ),
    "favourites": frozenset(),
}
CRISPY_TEMPLATE_PATHS = frozenset({"crispy_partials.html", "partial/form_fields.html"})
CRISPY_FRAGMENT_PATHS = frozenset(
    {"crispy_partials.html#crispy_form", "crispy_partials.html#load_tags"}
)
class TemplatePackValidationError(ImproperlyConfigured):
    """Report all deterministic contract failures for one template-pack declaration."""

    def __init__(self, template_pack: TemplatePack, issues: list[str]):
        """Build an actionable error message for the invalid declaration."""
        self.issues = tuple(issues)
        message = "\n".join(
            [
                f"PowerCRUD template pack {template_pack.identity!r} failed validation:",
                *[f"- {issue}" for issue in self.issues],
            ]
        )
        super().__init__(message)


def validate_template_pack(template_pack: TemplatePack) -> None:
    """Validate one resolved declaration without changing runtime pack selection."""
    issues: list[str] = []
    _validate_declaration(template_pack, issues)
    _validate_assets(template_pack, issues)
    template_paths, fragment_paths = _get_required_paths(template_pack)
    resource_root = _get_resource_root(template_pack, issues)
    if resource_root is not None:
        _validate_resource_paths(resource_root, template_paths, issues)
    _validate_django_templates(template_pack, template_paths, fragment_paths, issues)
    if issues:
        raise TemplatePackValidationError(template_pack, issues)


def _validate_declaration(template_pack: TemplatePack, issues: list[str]) -> None:
    """Validate declaration metadata that requires a configured Django environment."""
    if template_pack.contract_version != TEMPLATE_PACK_CONTRACT_VERSION:
        issues.append(
            "contract version "
            f"{template_pack.contract_version} is unsupported; expected "
            f"{TEMPLATE_PACK_CONTRACT_VERSION}."
        )

    unknown_capabilities = sorted(
        template_pack.capabilities - BASELINE_CAPABILITIES - OPTIONAL_CAPABILITIES
    )
    if unknown_capabilities:
        issues.append(f"declares unknown capabilities: {', '.join(unknown_capabilities)}.")

    missing_baseline_capabilities = sorted(BASELINE_CAPABILITIES - template_pack.capabilities)
    if missing_baseline_capabilities:
        issues.append(
            "is missing baseline capabilities: "
            f"{', '.join(missing_baseline_capabilities)}."
        )

    for capability, dependencies in sorted(CAPABILITY_DEPENDENCIES.items()):
        if capability in template_pack.capabilities:
            missing_dependencies = sorted(dependencies - template_pack.capabilities)
            if missing_dependencies:
                issues.append(
                    f"capability {capability!r} requires: "
                    f"{', '.join(missing_dependencies)}."
                )

    _validate_server_adapter(template_pack, issues)
    if not template_pack.supports_native_forms:
        issues.append("must support native Django forms for its baseline form capability.")

    if template_pack.django_app is not None and not apps.is_installed(template_pack.django_app):
        issues.append(f"declares Django app {template_pack.django_app!r}, which is not installed.")

    for crispy_integration in template_pack.crispy_integrations:
        dependency = crispy_integration.dependency
        if dependency is not None and find_spec(dependency) is None:
            issues.append(
                f"declares crispy template pack {crispy_integration.template_pack!r}, but dependency "
                f"{dependency!r} is unavailable."
            )


def _validate_server_adapter(template_pack: TemplatePack, issues: list[str]) -> None:
    """Validate the selected pack's declared public server adapter."""
    module_name, _, attribute_name = template_pack.server_adapter.partition(":")
    try:
        adapter = getattr(import_module(module_name), attribute_name)
    except (AttributeError, ImportError, ValueError) as exc:
        issues.append(
            f"cannot import server_adapter {template_pack.server_adapter!r}: {exc}."
        )
        return
    if getattr(adapter, "api_version", None) != SERVER_ADAPTER_API_VERSION:
        issues.append(
            "server_adapter "
            f"{template_pack.server_adapter!r} has api_version "
            f"{getattr(adapter, 'api_version', None)!r}; expected "
            f"{SERVER_ADAPTER_API_VERSION}."
        )
    if not callable(getattr(adapter, "get_presentation", None)):
        issues.append(
            f"server_adapter {template_pack.server_adapter!r} lacks callable get_presentation()."
        )


def _validate_assets(template_pack: TemplatePack, issues: list[str]) -> None:
    """Validate declared package-owned static and source resources."""
    for asset_path in template_pack.assets.stylesheets:
        if finders.find(asset_path) is None:
            issues.append(f"declares missing stylesheet {asset_path!r}.")
    for copy_root in template_pack.assets.copy_roots:
        _validate_package_resource(copy_root, "copy root", issues, require_directory=True)
    browser_adapter = template_pack.assets.browser_adapter
    if browser_adapter is None:
        return
    if browser_adapter.api_version != BROWSER_ADAPTER_API_VERSION:
        issues.append(
            f"declares browser adapter API {browser_adapter.api_version}; expected "
            f"{BROWSER_ADAPTER_API_VERSION}."
        )
    if finders.find(browser_adapter.static_path) is None:
        issues.append(
            f"declares missing browser adapter static path {browser_adapter.static_path!r}."
        )
    _validate_package_resource(browser_adapter.source, "browser adapter source", issues)


def _validate_package_resource(resource, label: str, issues: list[str], *, require_directory: bool = False) -> None:
    """Validate one declared importlib resource without source-checkout assumptions."""
    try:
        candidate = files(resource.package).joinpath(*PurePosixPath(resource.path).parts)
    except ModuleNotFoundError:
        issues.append(f"{label} package {resource.package!r} cannot be imported.")
        return
    if require_directory:
        available = candidate.is_dir()
    else:
        available = candidate.is_file()
    if not available:
        issues.append(
            f"declares missing {label} {resource.path!r} in package {resource.package!r}."
        )


def _get_required_paths(template_pack: TemplatePack) -> tuple[frozenset[str], frozenset[str]]:
    """Return stable template and fragment paths required by the declaration."""
    template_paths: set[str] = set()
    fragment_paths: set[str] = set()
    for capability in template_pack.capabilities & (
        BASELINE_CAPABILITIES | OPTIONAL_CAPABILITIES
    ):
        template_paths.update(CAPABILITY_TEMPLATE_PATHS[capability])
        fragment_paths.update(CAPABILITY_FRAGMENT_PATHS[capability])
    if template_pack.crispy_integrations:
        template_paths.update(CRISPY_TEMPLATE_PATHS)
        fragment_paths.update(CRISPY_FRAGMENT_PATHS)
    return frozenset(template_paths), frozenset(fragment_paths)


def _get_resource_root(template_pack: TemplatePack, issues: list[str]):
    """Resolve the declared package-resource directory without using source paths."""
    try:
        package_root = files(template_pack.template_package)
    except ModuleNotFoundError:
        issues.append(f"template package {template_pack.template_package!r} cannot be imported.")
        return None
    resource_root = package_root.joinpath(
        *PurePosixPath(template_pack.template_resource_root).parts
    )
    if not resource_root.is_dir():
        issues.append(
            "template resource root "
            f"{template_pack.template_resource_root!r} is missing from package "
            f"{template_pack.template_package!r}."
        )
        return None
    return resource_root


def _validate_resource_paths(resource_root, template_paths: frozenset[str], issues: list[str]) -> None:
    """Check declared package resources before relying on Django loader configuration."""
    for template_path in sorted(template_paths):
        resource = resource_root.joinpath(*PurePosixPath(template_path).parts)
        if not resource.is_file():
            issues.append(f"is missing required template resource {template_path!r}.")


def _validate_django_templates(
    template_pack: TemplatePack,
    template_paths: frozenset[str],
    fragment_paths: frozenset[str],
    issues: list[str],
) -> None:
    """Compile declared templates and directly rendered fragments through Django."""
    for template_path in sorted(template_paths):
        _validate_django_template(template_pack, template_path, issues)
    for fragment_path in sorted(fragment_paths):
        _validate_django_template(template_pack, fragment_path, issues)


def _validate_django_template(
    template_pack: TemplatePack, template_path: str, issues: list[str]
) -> None:
    """Record one loader failure while allowing the validator to continue."""
    template_name = f"{template_pack.template_namespace}/{template_path}"
    try:
        get_template(template_name)
    except (TemplateDoesNotExist, TemplateSyntaxError) as exc:
        issues.append(f"Django cannot load {template_name!r}: {exc}.")
