"""Public declarations and dynamic discovery for PowerCRUD template packs."""

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import PurePosixPath
from typing import Any, Literal, Mapping, Protocol

from django.core.exceptions import ImproperlyConfigured

from powercrud.conf import get_powercrud_setting


TEMPLATE_PACK_CONTRACT_VERSION = 1
SERVER_ADAPTER_API_VERSION = 1
BROWSER_ADAPTER_API_VERSION = 1
_BUILTIN_TEMPLATE_PACKS = {"daisyui": "powercrud.packs.daisyui:template_pack"}
_UNCONFIGURED_SELECTOR = object()
_FRAMEWORK_STYLE_KEYS = {"daisyui": "daisyUI"}

# These options promise a presentation outcome across every first-party pack.
# Framework-specific class strings remain deliberately portable only within the
# framework they name; packs declare any values they cannot honour so runtime
# configuration never becomes a silent no-op.
PORTABLE_PRESENTATION_OPTIONS = frozenset(
    {
        "table_pixel_height_other_page_elements",
        "table_max_height",
        "table_max_col_width",
        "table_header_min_wrap_width",
        "column_alignments",
        "extra_button_classes",
        "inline_edit_highlight_accent",
        "view_help.summary",
        "view_help.details",
        "view_help.default_open",
        "view_help.color",
        "view_help.min_width",
        "view_help_default_color",
        "view_help_min_width",
        "modal_presentation",
        "bulk_modal_presentation",
    }
)
FRAMEWORK_SPECIFIC_PRESENTATION_OPTIONS = frozenset(
    {
        "table_classes",
        "action_button_classes",
        "modal_classes",
        "modal_box_classes",
        "modal_body_classes",
        "bulk_modal_box_classes",
    }
)
DECLARABLE_PRESENTATION_OPTIONS = (
    PORTABLE_PRESENTATION_OPTIONS | FRAMEWORK_SPECIFIC_PRESENTATION_OPTIONS
)


class TemplatePackCompatibilityWarning(UserWarning):
    """Report an explicit presentation setting a selected pack cannot honour."""


@dataclass(frozen=True, slots=True)
class PackageResource:
    """Identify one safe resource inside an importable Python package."""

    package: str
    path: str

    def __post_init__(self):
        """Validate package-resource metadata without importing the package."""
        _require_dotted_identifier(self.package, "package")
        _require_resource_root(self.path)


@dataclass(frozen=True, slots=True)
class VendorRequirement:
    """Describe a frontend dependency supplied by the consuming application."""

    name: str
    purpose: str
    global_name: str | None = None
    vite_import: str | None = None
    manual_static_note: str = ""

    def __post_init__(self):
        """Validate human-facing dependency guidance."""
        _require_string(self.name, "name")
        _require_string(self.purpose, "purpose")
        _require_optional_string(self.global_name, "global_name")
        _require_optional_string(self.vite_import, "vite_import")
        if not isinstance(self.manual_static_note, str):
            raise ValueError("manual_static_note must be a string.")


@dataclass(frozen=True, slots=True)
class BrowserAdapterSpec:
    """Describe an optional pack-owned browser adapter module."""

    api_version: int
    static_path: str
    source: PackageResource

    def __post_init__(self):
        """Validate one browser-adapter declaration."""
        _require_positive_integer(self.api_version, "api_version")
        _require_static_path(self.static_path, "static_path")
        if not isinstance(self.source, PackageResource):
            raise ValueError("source must be a PackageResource.")


@dataclass(frozen=True, slots=True)
class PackAssets:
    """Describe pack-owned assets without installing third-party vendors."""

    stylesheets: tuple[str, ...] = ()
    copy_roots: tuple[PackageResource, ...] = ()
    browser_adapter: BrowserAdapterSpec | None = None
    vendor_requirements: tuple[VendorRequirement, ...] = ()

    def __post_init__(self):
        """Validate immutable asset metadata."""
        _require_tuple_of_static_paths(self.stylesheets, "stylesheets")
        if not isinstance(self.copy_roots, tuple) or not all(
            isinstance(item, PackageResource) for item in self.copy_roots
        ):
            raise ValueError("copy_roots must be a tuple of PackageResource values.")
        if self.browser_adapter is not None and not isinstance(
            self.browser_adapter, BrowserAdapterSpec
        ):
            raise ValueError("browser_adapter must be a BrowserAdapterSpec or None.")
        if not isinstance(self.vendor_requirements, tuple) or not all(
            isinstance(item, VendorRequirement) for item in self.vendor_requirements
        ):
            raise ValueError(
                "vendor_requirements must be a tuple of VendorRequirement values."
            )


@dataclass(frozen=True, slots=True)
class CrispyIntegration:
    """Describe one optional Crispy Forms integration owned by a pack."""

    template_pack: str
    dependency: str | None = None

    def __post_init__(self):
        """Validate one Crispy integration declaration."""
        _require_string(self.template_pack, "template_pack")
        _require_optional_string(self.dependency, "dependency")


FilterWidgetKind = Literal["text", "select", "multiselect", "date", "number", "time", "default"]
ActionRole = Literal["view", "edit", "delete", "extra"]


@dataclass(frozen=True, slots=True)
class ServerAdapterContext:
    """Stable semantic context supplied to a server adapter for one view."""

    modal_id: str
    modal_target_id: str
    use_htmx: bool
    use_modal: bool


@dataclass(frozen=True, slots=True)
class ActionPresentation:
    """Framework presentation for links and action controls."""

    base_classes: str = ""
    role_classes: Mapping[ActionRole, str] = field(default_factory=dict)
    group_item_classes: str = ""
    extra_default_classes: str = ""
    list_cell_link_classes: str = ""


@dataclass(frozen=True, slots=True)
class ServerPresentation:
    """Complete framework presentation returned for one view."""

    filter_widget_attrs: Mapping[FilterWidgetKind, Mapping[str, str]] = field(
        default_factory=dict
    )
    actions: ActionPresentation = field(default_factory=ActionPresentation)


class PowerCRUDServerAdapter(Protocol):
    """Public server-adapter interface for selectable packs."""

    api_version: int

    def get_presentation(self, context: ServerAdapterContext) -> ServerPresentation:
        """Return framework presentation for one configured view."""

    def get_view_help_variables(self, color: str) -> Mapping[str, str]:
        """Return the documented PowerCRUD view-help CSS variables."""


class BaseServerAdapter:
    """Provide neutral server presentation defaults for simple template packs."""

    api_version = SERVER_ADAPTER_API_VERSION

    def get_presentation(self, context: ServerAdapterContext) -> ServerPresentation:
        """Return presentation with no framework classes or widget attributes."""
        del context
        return ServerPresentation()

    def get_view_help_variables(self, color: str) -> Mapping[str, str]:
        """Return neutral CSS variables while preserving the requested colour."""
        return {
            "--pc-view-help-color": color,
            "--pc-view-help-border-color": color,
            "--pc-view-help-background-color": "transparent",
            "--pc-view-help-text-color": "inherit",
            "--pc-view-help-accent-color": color,
        }


@dataclass(frozen=True, slots=True)
class TemplatePack:
    """Describe one selectable pack and its public adapter resources."""

    identity: str
    contract_version: int
    template_namespace: str
    template_package: str
    template_resource_root: str
    server_adapter: str
    capabilities: frozenset[str]
    supports_native_forms: bool
    django_app: str | None
    assets: PackAssets = field(default_factory=PackAssets)
    crispy_integrations: tuple[CrispyIntegration, ...] = ()
    unsupported_presentation_options: frozenset[str] = frozenset()
    legacy_copy_destination: str | None = None

    def __post_init__(self):
        """Validate the declaration shape without probing its environment."""
        _require_safe_identity(self.identity)
        _require_positive_integer(self.contract_version, "contract_version")
        _require_string(self.template_namespace, "template_namespace")
        _require_string(self.template_package, "template_package")
        _require_resource_root(self.template_resource_root)
        _require_selector_path(self.server_adapter, "server_adapter")
        _require_frozenset_of_strings(self.capabilities, "capabilities")
        if not isinstance(self.supports_native_forms, bool):
            raise ValueError("supports_native_forms must be a bool.")
        _require_optional_string(self.django_app, "django_app")
        if not isinstance(self.assets, PackAssets):
            raise ValueError("assets must be a PackAssets value.")
        if not isinstance(self.crispy_integrations, tuple) or not all(
            isinstance(item, CrispyIntegration) for item in self.crispy_integrations
        ):
            raise ValueError(
                "crispy_integrations must be a tuple of CrispyIntegration values."
            )
        _require_legacy_copy_destination(self.legacy_copy_destination)
        _require_frozenset_of_strings(
            self.unsupported_presentation_options,
            "unsupported_presentation_options",
        )
        unknown_presentation_options = (
            self.unsupported_presentation_options - DECLARABLE_PRESENTATION_OPTIONS
        )
        if unknown_presentation_options:
            unknown_values = ", ".join(sorted(unknown_presentation_options))
            raise ValueError(
                "unsupported_presentation_options contains unknown presentation "
                f"options: {unknown_values}."
            )
        portable_exclusions = (
            self.unsupported_presentation_options & PORTABLE_PRESENTATION_OPTIONS
        )
        if portable_exclusions:
            excluded_values = ", ".join(sorted(portable_exclusions))
            raise ValueError(
                "unsupported_presentation_options cannot exclude portable presentation "
                f"options: {excluded_values}."
            )


def get_selected_template_pack() -> TemplatePack:
    """Resolve the current selector without caching settings or declarations."""
    selector = get_powercrud_setting(
        "POWERCRUD_TEMPLATE_PACK", default=_UNCONFIGURED_SELECTOR
    )
    return resolve_template_pack("daisyui" if selector is _UNCONFIGURED_SELECTOR else selector)


def get_configured_template_pack() -> TemplatePack | None:
    """Resolve canonical DaisyUI selection while retaining custom legacy fallback."""
    selector = get_powercrud_setting(
        "POWERCRUD_TEMPLATE_PACK", default=_UNCONFIGURED_SELECTOR
    )
    if selector is _UNCONFIGURED_SELECTOR:
        if get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK") == "daisyUI":
            return resolve_template_pack("daisyui")
        return None
    return resolve_template_pack(selector)


def get_template_pack_template_namespace() -> str:
    """Return the explicit pack namespace or the compatible legacy namespace."""
    template_pack = get_configured_template_pack()
    if template_pack is not None:
        return template_pack.template_namespace
    return f"powercrud/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}"


def get_template_pack_style_key() -> str:
    """Return the selected pack identity or the compatible legacy style key."""
    template_pack = get_configured_template_pack()
    if template_pack is not None:
        return template_pack.identity
    return get_powercrud_setting("POWERCRUD_CSS_FRAMEWORK")


def get_template_pack_styles(styles: Mapping[str, Any]) -> Any:
    """Select styles while retaining the established DaisyUI override key."""
    style_key = get_template_pack_style_key()
    if style_key in styles:
        return styles[style_key]
    legacy_key = _FRAMEWORK_STYLE_KEYS.get(style_key)
    if legacy_key is not None and legacy_key in styles:
        return styles[legacy_key]
    raise ImproperlyConfigured(
        f"PowerCRUD could not find styles for template-pack framework adapter {style_key!r}."
    )


def get_template_pack_copy_destination() -> str:
    """Return the whole-tree destination for the active pack."""
    template_pack = get_configured_template_pack()
    if template_pack is None:
        return PurePosixPath(get_template_pack_template_namespace()).name
    return template_pack.legacy_copy_destination or template_pack.identity


def get_template_pack_server_adapter() -> PowerCRUDServerAdapter:
    """Resolve and validate the selected pack's public server adapter."""
    template_pack = get_selected_template_pack()
    adapter = _load_template_pack(template_pack.server_adapter, template_pack.identity)
    api_version = getattr(adapter, "api_version", None)
    get_presentation = getattr(adapter, "get_presentation", None)
    if api_version != SERVER_ADAPTER_API_VERSION or not callable(get_presentation):
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {template_pack.identity!r} server_adapter "
            f"{template_pack.server_adapter!r} must expose api_version "
            f"{SERVER_ADAPTER_API_VERSION} and callable get_presentation()."
        )
    return adapter


def resolve_template_pack(selector: str) -> TemplatePack:
    """Resolve a built-in identity or ``module.path:attribute`` declaration."""
    declared_selector = _validate_selector(selector)
    declaration_path = _BUILTIN_TEMPLATE_PACKS.get(declared_selector, declared_selector)
    template_pack = _load_template_pack(declaration_path, selector)
    _validate_resolved_template_pack(template_pack, selector)
    return template_pack


def _require_string(value: object, field_name: str) -> None:
    """Require a non-empty string without leading or trailing whitespace."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty, unpadded string.")


def _require_dotted_identifier(value: object, field_name: str) -> None:
    """Require a dotted Python identifier suitable for an importable package."""
    _require_string(value, field_name)
    if not _is_dotted_identifier(str(value)):
        raise ValueError(f"{field_name} must be a dotted Python identifier.")


def _require_safe_identity(value: object) -> None:
    """Require an identity safe for diagnostics and project copy destinations."""
    _require_string(value, "identity")
    path = PurePosixPath(str(value))
    if (
        path.is_absolute()
        or len(path.parts) != 1
        or path.parts[0] in {".", ".."}
        or "\\" in str(value)
    ):
        raise ValueError("identity must be one safe relative POSIX path segment.")


def _require_selector_path(value: object, field_name: str) -> None:
    """Require a module-path declaration reference without importing it."""
    _require_string(value, field_name)
    module_name, separator, attribute_name = str(value).partition(":")
    if not separator or ":" in attribute_name or not _is_dotted_identifier(module_name) or not attribute_name.isidentifier():
        raise ValueError(f"{field_name} must use 'module.path:attribute' syntax.")


def _require_optional_string(value: object, field_name: str) -> None:
    """Require an optional string using the declaration string rules."""
    if value is not None:
        _require_string(value, field_name)


def _require_legacy_copy_destination(value: object) -> None:
    """Require the optional legacy-copy target to be one safe path segment."""
    if value is None:
        return
    _require_string(value, "legacy_copy_destination")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or len(path.parts) != 1
        or path.parts[0] in {".", ".."}
        or "\\" in value
    ):
        raise ValueError(
            "legacy_copy_destination must be one safe relative POSIX path segment."
        )


def _require_positive_integer(value: object, field_name: str) -> None:
    """Require a positive integer while excluding bool values."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")


def _require_resource_root(value: object) -> None:
    """Require a relative POSIX package-resource path without traversal."""
    _require_string(value, "template_resource_root")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) in {".", ""}:
        raise ValueError(
            "template_resource_root must be a relative package-resource path without traversal."
        )


def _require_static_path(value: object, field_name: str) -> None:
    """Require one safe Django staticfiles path."""
    _require_string(value, field_name)
    path = PurePosixPath(str(value))
    if path.is_absolute() or ".." in path.parts or str(path) in {".", ""} or "\\" in str(value):
        raise ValueError(f"{field_name} must be a safe relative static path.")


def _require_frozenset_of_strings(value: object, field_name: str) -> None:
    """Require an immutable set of valid string values."""
    if not isinstance(value, frozenset) or not all(
        isinstance(item, str) and item and item == item.strip() for item in value
    ):
        raise ValueError(f"{field_name} must be a frozenset of non-empty, unpadded strings.")


def _require_tuple_of_strings(value: object, field_name: str) -> None:
    """Require an immutable sequence of valid string asset paths."""
    if not isinstance(value, tuple) or not all(
        isinstance(item, str) and item and item == item.strip() for item in value
    ):
        raise ValueError(f"{field_name} must be a tuple of non-empty, unpadded strings.")


def _require_tuple_of_static_paths(value: object, field_name: str) -> None:
    """Require immutable safe staticfiles paths."""
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple of safe static paths.")
    for item in value:
        _require_static_path(item, field_name)


def _validate_selector(selector: object) -> str:
    """Validate the accepted selector grammar before import attempts."""
    if not isinstance(selector, str) or not selector or selector != selector.strip():
        raise ImproperlyConfigured(
            "POWERCRUD_SETTINGS['POWERCRUD_TEMPLATE_PACK'] must be a non-empty, "
            "unpadded string."
        )
    if selector in _BUILTIN_TEMPLATE_PACKS:
        return selector
    if ":" not in selector:
        raise ImproperlyConfigured(
            f"Unknown PowerCRUD template pack {selector!r}. Use built-in 'daisyui' or "
            "a third-party 'module.path:attribute' declaration."
        )
    module_name, separator, attribute_name = selector.partition(":")
    if (
        not separator
        or ":" in attribute_name
        or not _is_dotted_identifier(module_name)
        or not attribute_name.isidentifier()
    ):
        raise ImproperlyConfigured(
            "POWERCRUD_SETTINGS['POWERCRUD_TEMPLATE_PACK'] third-party selectors must use "
            "'module.path:attribute' syntax."
        )
    return selector


def _is_dotted_identifier(value: str) -> bool:
    """Return whether every segment of a dotted module path is an identifier."""
    return bool(value) and all(part.isidentifier() for part in value.split("."))


def _load_template_pack(declaration_path: str, original_selector: object) -> object:
    """Import and retrieve one declaration while preserving contextual errors."""
    module_name, _, attribute_name = declaration_path.partition(":")
    try:
        module = import_module(module_name)
    except Exception as exc:
        raise ImproperlyConfigured(
            f"Could not import PowerCRUD template pack {original_selector!r} from "
            f"{module_name!r}: {exc}"
        ) from exc
    try:
        return getattr(module, attribute_name)
    except AttributeError as exc:
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {original_selector!r} declares no "
            f"{attribute_name!r} attribute in {module_name!r}."
        ) from exc


def _validate_resolved_template_pack(template_pack: object, selector: object) -> None:
    """Reject malformed public declarations without whitelisting frameworks."""
    if not isinstance(template_pack, TemplatePack):
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {selector!r} must resolve to a TemplatePack declaration."
        )
    if template_pack.contract_version != TEMPLATE_PACK_CONTRACT_VERSION:
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {selector!r} uses contract version "
            f"{template_pack.contract_version}; this PowerCRUD version supports "
            f"{TEMPLATE_PACK_CONTRACT_VERSION}."
        )
    if selector != "daisyui" and template_pack.identity == "daisyui":
        raise ImproperlyConfigured(
            "The 'daisyui' template-pack identity is reserved for PowerCRUD's built-in pack."
        )
    if selector == "daisyui" and template_pack.identity != "daisyui":
        raise ImproperlyConfigured(
            "The built-in 'daisyui' selector must resolve PowerCRUD's DaisyUI declaration."
        )
