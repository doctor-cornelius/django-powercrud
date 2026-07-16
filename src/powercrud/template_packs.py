"""Public declarations and dynamic discovery for PowerCRUD template packs."""

from dataclasses import dataclass
from importlib import import_module
from pathlib import PurePosixPath
from typing import Any, Mapping

from django.core.exceptions import ImproperlyConfigured

from powercrud.conf import get_powercrud_setting


TEMPLATE_PACK_CONTRACT_VERSION = 1
_BUILTIN_TEMPLATE_PACKS = {"daisyui": "powercrud.packs.daisyui:template_pack"}
_UNCONFIGURED_SELECTOR = object()
_FRAMEWORK_STYLE_KEYS = {"daisyui": "daisyUI"}
_SUPPORTED_FRAMEWORK_ADAPTERS = frozenset({"bootstrap5", "daisyui"})

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
class TemplatePack:
    """Describe one template pack without loading its templates or assets."""

    identity: str
    contract_version: int
    template_namespace: str
    template_package: str
    template_resource_root: str
    legacy_copy_destination: str | None
    framework_adapter: str
    variant_adapter: str | None
    capabilities: frozenset[str]
    supports_native_forms: bool
    crispy_template_packs: frozenset[str]
    django_app: str | None
    manual_assets: tuple[str, ...] = ()
    vite_assets: tuple[str, ...] = ()
    unsupported_presentation_options: frozenset[str] = frozenset()

    def __post_init__(self):
        """Validate the declaration shape without probing its environment."""
        _require_string(self.identity, "identity")
        _require_positive_integer(self.contract_version, "contract_version")
        _require_string(self.template_namespace, "template_namespace")
        _require_string(self.template_package, "template_package")
        _require_resource_root(self.template_resource_root)
        _require_legacy_copy_destination(self.legacy_copy_destination)
        _require_string(self.framework_adapter, "framework_adapter")
        _require_optional_string(self.variant_adapter, "variant_adapter")
        _require_frozenset_of_strings(self.capabilities, "capabilities")
        if not isinstance(self.supports_native_forms, bool):
            raise ValueError("supports_native_forms must be a bool.")
        _require_frozenset_of_strings(self.crispy_template_packs, "crispy_template_packs")
        _require_optional_string(self.django_app, "django_app")
        _require_tuple_of_strings(self.manual_assets, "manual_assets")
        _require_tuple_of_strings(self.vite_assets, "vite_assets")
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
    """Return the canonical pack-adapter key or the legacy style key."""
    template_pack = get_configured_template_pack()
    if template_pack is not None:
        return template_pack.framework_adapter
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
    """Return the legacy whole-tree destination for the active pack."""
    template_pack = get_configured_template_pack()
    if template_pack is None:
        return PurePosixPath(get_template_pack_template_namespace()).name
    if template_pack.legacy_copy_destination is None:
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {template_pack.identity!r} does not declare a "
            "whole-tree copy destination."
        )
    return template_pack.legacy_copy_destination


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
    """Reject declarations unsupported by the Phase 4 runtime contract."""
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
    if template_pack.framework_adapter not in _SUPPORTED_FRAMEWORK_ADAPTERS:
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {selector!r} requires unsupported framework adapter "
            f"{template_pack.framework_adapter!r}; supported adapters are "
            f"{', '.join(sorted(_SUPPORTED_FRAMEWORK_ADAPTERS))}."
        )
    if template_pack.variant_adapter is not None:
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {selector!r} requires unsupported variant adapter "
            f"{template_pack.variant_adapter!r}."
        )
    if (
        template_pack.framework_adapter != "bootstrap5"
        and (template_pack.manual_assets or template_pack.vite_assets)
    ):
        raise ImproperlyConfigured(
            f"PowerCRUD template pack {selector!r} declares additional browser assets, which "
            "are supported only by the Bootstrap 5 adapter."
        )
