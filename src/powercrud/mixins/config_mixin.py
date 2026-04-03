from types import SimpleNamespace
import warnings

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.reverse_related import ManyToOneRel
from typing import Any, Callable

from ..validators import PowerCRUDMixinValidator

from powercrud.conf import get_powercrud_setting
from powercrud.logging import get_logger

log = get_logger(__name__)


class ConfigMixin:
    """
    Centralized configuration mixin responsible for declaring and validating
    PowerCRUD options. Downstream behavioural mixins should read resolved
    configuration via `self.config()` (or the `resolve_config()` helper),
    which returns a namespace containing validated field lists, derived flags,
    and rule-evaluated defaults.
    """

    # namespace if appropriate
    namespace: str | None = None

    # template parameters
    templates_path: str = (
        f"powercrud/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}"
    )
    # base_template_path must always be provided by the project; there is no
    # built-in HTML shell. It should point at the app’s real base template.
    base_template_path: str | None = None
    view_title: str | None = None
    view_instructions: str | None = None
    column_help_text: dict[str, str] | None = None

    # forms
    use_crispy: bool | None = None
    searchable_selects: bool | None = True

    # field and property inclusion scope
    exclude: list[str] = []
    properties: list[str] = []
    properties_exclude: list[str] = []

    # for the detail view
    detail_fields: list[str] = []
    detail_exclude: list[str] = []
    detail_properties: list[str] = []
    detail_properties_exclude: list[str] = []

    # form fields (if no form_class is specified)
    form_class = None
    form_fields: list[str] = []
    form_fields_exclude: list[str] = []
    form_display_fields: list[str] = []
    form_disabled_fields: list[str] = []

    # bulk edit parameters
    bulk_fields: list[str] = []
    bulk_delete: bool = False
    bulk_full_clean: bool = (
        True  # If True, run full_clean() on each object during bulk edit
    )

    # async processing parameters
    bulk_async: bool = False
    bulk_async_conflict_checking = True  # Default enabled
    bulk_min_async_records: int = 20
    bulk_async_backend: str = "q2"
    bulk_async_notification: str = "status_page"
    bulk_async_allow_anonymous = True
    bulk_update_persistence_backend_path: str | None = None
    bulk_update_persistence_backend_config: dict | None = None

    # htmx
    use_htmx: bool | None = None
    default_htmx_target: str = "#content"
    hx_trigger: str | dict[str, str] | None = None

    # inline editing
    inline_edit_fields: list[str] | str | None = None
    field_queryset_dependencies: dict[str, dict[str, Any]] | None = None
    inline_edit_requires_perm: str | None = None
    inline_edit_allowed: Callable[[Any, Any], bool] | None = None
    inline_preserve_required_fields: bool = True
    inline_edit_always_visible: bool = True
    inline_edit_highlight_accent: str = "#14b8a6"

    # modals (if htmx is active)
    use_modal: bool | None = None
    modal_id: str | None = None
    modal_target: str | None = None

    # table display parameters
    table_pixel_height_other_page_elements: int | float = 0
    table_max_height: int = 70

    table_max_col_width: int | None = None
    table_header_min_wrap_width: int | None = None

    table_classes: str = ""
    action_button_classes: str = ""
    extra_button_classes: str = ""
    extra_actions_mode: str = "buttons"
    show_record_count: bool = False
    show_bulk_selection_meta: bool = True

    # filtering options
    m2m_filter_and_logic = False
    dropdown_sort_options: dict = {}
    filter_null_fields_exclude: list[str] = []

    # async manager configuration
    async_manager_class = None
    async_manager_class_path: str | None = None
    async_manager_config: dict | None = None

    # pagination defaults
    paginate_by: int | None = None

    EXTRA_CONFIG_FIELDS = {
        "form_class",
        "bulk_fields",
        "bulk_delete",
        "bulk_full_clean",
        "bulk_async",
        "bulk_async_conflict_checking",
        "bulk_min_async_records",
        "bulk_async_backend",
        "bulk_async_notification",
        "bulk_async_allow_anonymous",
        "bulk_update_persistence_backend_path",
        "bulk_update_persistence_backend_config",
        "field_queryset_dependencies",
        "dropdown_sort_options",
        "filter_null_fields_exclude",
        "table_classes",
        "action_button_classes",
        "extra_button_classes",
        "extra_actions_mode",
        "show_record_count",
        "show_bulk_selection_meta",
        "m2m_filter_and_logic",
        "inline_preserve_required_fields",
        "async_manager_class",
        "async_manager_class_path",
        "async_manager_config",
        "paginate_by",
    }

    DEDUPED_STRING_LIST_FIELDS = {
        "fields",
        "properties",
        "exclude",
        "properties_exclude",
        "detail_fields",
        "detail_exclude",
        "detail_properties",
        "detail_properties_exclude",
        "form_fields",
        "form_fields_exclude",
        "form_display_fields",
        "form_disabled_fields",
        "bulk_fields",
        "inline_edit_fields",
        "filter_null_fields_exclude",
        "filterset_fields",
    }

    # ------------------------------------------------------------------
    # Sync-safe async defaults
    # ------------------------------------------------------------------
    # PowerCRUDMixin (sync stack) intentionally does not inherit AsyncMixin.
    # These defaults let sync views call shared form/bulk code paths without
    # requiring downstream projects to define async/conflict hooks.
    def get_bulk_async_enabled(self) -> bool:
        return False

    def get_bulk_min_async_records(self) -> int:
        return int(getattr(self, "bulk_min_async_records", 20))

    def get_bulk_async_backend(self) -> str:
        return str(getattr(self, "bulk_async_backend", "q2"))

    def get_bulk_async_notification(self) -> str:
        return str(getattr(self, "bulk_async_notification", "status_page"))

    def get_bulk_update_persistence_backend_path(self) -> str | None:
        """Return the configured bulk update persistence backend import path."""
        return getattr(self, "bulk_update_persistence_backend_path", None)

    def get_bulk_update_persistence_backend_config(self) -> dict | None:
        """Return the configured bulk update persistence backend config."""
        return getattr(self, "bulk_update_persistence_backend_config", None)

    def should_process_async(self, record_count: int) -> bool:
        return False

    def get_conflict_checking_enabled(self) -> bool:
        return False

    def _check_for_conflicts(self, selected_ids=None) -> bool:
        return False

    def _check_single_record_conflict(self, pk) -> bool:
        return False

    def __init__(self, *args, **kwargs):  # pragma: no cover
        super().__init__(*args, **kwargs)
        self._validated_config = None
        self._legacy_inline_edit_enabled_present = hasattr(self, "inline_edit_enabled")
        self._legacy_inline_edit_enabled_value = bool(
            getattr(self, "inline_edit_enabled", False)
        )

        if self._legacy_inline_edit_enabled_present:
            self._warn_inline_edit_enabled_legacy(
                getattr(self, "inline_edit_fields", None)
            )

        config_dict = {}
        for attr in PowerCRUDMixinValidator.model_fields.keys():
            if hasattr(self, attr):
                config_dict[attr] = getattr(self, attr)

        try:
            validated_settings = PowerCRUDMixinValidator(**config_dict)
            for field_name, value in validated_settings.model_dump().items():
                setattr(self, field_name, value)
            self._validated_config = validated_settings
        except ValueError as e:
            class_name = self.__class__.__name__
            raise ImproperlyConfigured(
                f"Invalid configuration in class '{class_name}': {str(e)}"
            )

        self._normalize_declared_string_lists()
        self._configure_fields()
        self._configure_properties()
        self._configure_detail_fields()
        self._configure_detail_properties()
        self._configure_bulk_fields()
        self._configure_inline_edit_fields()
        self._configure_form_fields()
        self._configure_form_display_fields()

        if self.bulk_async and not self.get_bulk_async_enabled():
            log.warning(
                "bulk_async is enabled but backend '%s' is not available",
                self.get_bulk_async_backend(),
            )

    def config(self):
        """
        Return the validated configuration namespace for this instance.

        Each call rebuilds the namespace to capture any attribute overrides that
        may have happened after `__init__` (for example, in lightweight test
        harnesses that mutate attributes directly). Behavioural mixins should
        treat the returned object as read-only and rely on helpers such as
        `resolve_config(self)` when they need a configuration view.
        """
        return self._build_config_namespace()

    @staticmethod
    def _dedupe_preserving_first(values: list[str] | None) -> list[str]:
        """
        Return the input list with duplicates removed, keeping first occurrence.
        """
        if not values:
            return []
        return list(dict.fromkeys(values))

    def _normalize_declared_string_lists(self) -> None:
        """
        Quietly collapse duplicate configured list entries before resolution.
        """
        for attr_name in self.DEDUPED_STRING_LIST_FIELDS:
            value = getattr(self, attr_name, None)
            if isinstance(value, list):
                setattr(self, attr_name, self._dedupe_preserving_first(value))

    def _configure_fields(self):
        if not self.fields or self.fields == "__all__":
            self.fields = self._get_all_fields()
        elif isinstance(self.fields, list):
            all_fields = self._get_all_fields()
            for field in self.fields:
                if field not in all_fields:
                    raise ValueError(
                        f"Field {field} not defined in {self.model.__name__}"
                    )
        elif not isinstance(self.fields, list):
            raise TypeError("fields must be a list")
        else:
            raise ValueError(
                "fields must be '__all__', a list of valid fields or not defined"
            )

        if isinstance(self.exclude, list):
            self.fields = [field for field in self.fields if field not in self.exclude]
        else:
            raise TypeError("exclude must be a list")

    def _configure_properties(self):
        if self.properties:
            if self.properties == "__all__":
                self.properties = self._get_all_properties()
            elif isinstance(self.properties, list):
                all_properties = self._get_all_properties()
                for prop in self.properties:
                    if prop not in all_properties:
                        raise ValueError(
                            f"Property {prop} not defined in {self.model.__name__}"
                        )
            elif not isinstance(self.properties, list):
                raise TypeError("properties must be a list or '__all__'")

        if isinstance(self.properties_exclude, list):
            self.properties = [
                prop for prop in self.properties if prop not in self.properties_exclude
            ]
        else:
            raise TypeError("properties_exclude must be a list")

    def _configure_detail_fields(self):
        if self.detail_fields == "__all__":
            self.detail_fields = self._get_all_fields()
        elif not self.detail_fields or self.detail_fields == "__fields__":
            self.detail_fields = self.fields
        elif isinstance(self.detail_fields, list):
            all_fields = self._get_all_fields()
            for field in self.detail_fields:
                if field not in all_fields:
                    raise ValueError(
                        f"detail_field {field} not defined in {self.model.__name__}"
                    )
        elif not isinstance(self.detail_fields, list):
            raise TypeError(
                "detail_fields must be a list or '__all__' or '__fields__' or a list of fields"
            )

        if isinstance(self.detail_exclude, list):
            self.detail_fields = [
                field
                for field in self.detail_fields
                if field not in self.detail_exclude
            ]
        else:
            raise TypeError("detail_fields_exclude must be a list")

    def _configure_detail_properties(self):
        if self.detail_properties:
            if self.detail_properties == "__all__":
                self.detail_properties = self._get_all_properties()
            elif self.detail_properties == "__properties__":
                self.detail_properties = self.properties
            elif isinstance(self.detail_properties, list):
                all_properties = self._get_all_properties()
                for prop in self.detail_properties:
                    if prop not in all_properties:
                        raise ValueError(
                            f"Property {prop} not defined in {self.model.__name__}"
                        )
            elif not isinstance(self.detail_properties, list):
                raise TypeError(
                    "detail_properties must be a list or '__all__' or '__properties__'"
                )

        if isinstance(self.detail_properties_exclude, list):
            self.detail_properties = [
                prop
                for prop in self.detail_properties
                if prop not in self.detail_properties_exclude
            ]
        else:
            raise TypeError("detail_properties_exclude must be a list")

    def _validate_declared_model_fields(
        self,
        field_names: list[str],
        *,
        config_name: str,
        editable_only: bool = False,
    ) -> None:
        """
        Validate configured model-field names against the current model.

        Args:
            field_names: Declared field names to validate.
            config_name: Public config attribute being validated.
            editable_only: When True, require the referenced model fields to be
                editable as well as present on the model.
        """
        all_fields = set(self._get_all_fields())
        invalid_fields = [field for field in field_names if field not in all_fields]
        if invalid_fields:
            raise ValueError(
                f"The following {config_name} are not model fields in {self.model.__name__}: "
                f"{', '.join(invalid_fields)}"
            )

        if not editable_only:
            return

        editable_fields = set(self._get_all_editable_fields())
        non_editable_fields = [
            field for field in field_names if field not in editable_fields
        ]
        if non_editable_fields:
            raise ValueError(
                f"The following {config_name} are not editable fields in {self.model.__name__}: "
                f"{', '.join(non_editable_fields)}"
            )

    def _configure_bulk_fields(self):
        if self.bulk_fields:
            if isinstance(self.bulk_fields, list):
                for field_name in self.bulk_fields:
                    if not isinstance(field_name, str):
                        raise ValueError(
                            f"Invalid bulk field configuration: {field_name}. Must be a string."
                        )
                self._validate_declared_model_fields(
                    self.bulk_fields,
                    config_name="bulk_fields",
                    editable_only=True,
                )

    def _configure_inline_edit_fields(self):
        """
        Validate explicitly declared inline-edit fields.

        Inline sentinel values are resolved later by InlineEditingMixin, but any
        explicit list must reference editable model fields up front so
        misconfiguration fails loudly instead of disappearing silently.
        """
        if isinstance(self.inline_edit_fields, list):
            self._validate_declared_model_fields(
                self.inline_edit_fields,
                config_name="inline_edit_fields",
                editable_only=True,
            )

    def _configure_form_fields(self):
        """
        Resolve editable auto-generated form fields.

        When a custom ``form_class`` is configured, PowerCRUD no longer treats
        ``form_fields`` / ``form_fields_exclude`` as meaningful form-shaping
        configuration. The custom form class becomes the sole source of truth
        for editable inputs.
        """
        if self.form_class is not None:
            self.form_fields = []
            return

        all_editable = self._get_all_editable_fields()

        if not self.form_fields:
            self.form_fields = [f for f in self.detail_fields if f in all_editable]
        elif self.form_fields == "__all__":
            self.form_fields = all_editable
        elif self.form_fields == "__fields__":
            self.form_fields = [f for f in self.fields if f in all_editable]
        else:
            self._validate_declared_model_fields(
                self.form_fields,
                config_name="form_fields",
                editable_only=True,
            )

        if self.form_fields_exclude:
            self.form_fields = [
                f for f in self.form_fields if f not in self.form_fields_exclude
            ]

    def _configure_form_display_fields(self):
        """Validate configured display-only form fields against model fields."""
        if not self.form_display_fields:
            self.form_display_fields = []
            return

        all_fields = self._get_all_fields()
        invalid_fields = [f for f in self.form_display_fields if f not in all_fields]
        if invalid_fields:
            raise ValueError(
                f"The following form_display_fields are not model fields in {self.model.__name__}: "
                f"{', '.join(invalid_fields)}"
            )

    def _get_all_fields(self):
        return [
            field.name
            for field in self.model._meta.get_fields()
            if not isinstance(field, ManyToOneRel)
        ]

    def _get_all_editable_fields(self):
        return [
            field.name
            for field in self.model._meta.get_fields()
            if hasattr(field, "editable") and field.editable
        ]

    def _get_all_properties(self):
        return [
            name
            for name in dir(self.model)
            if isinstance(getattr(self.model, name), property) and name != "pk"
        ]

    def _build_config_namespace(self) -> SimpleNamespace:
        config: dict[str, Any] = {}
        field_names = (
            set(PowerCRUDMixinValidator.model_fields.keys()) | self.EXTRA_CONFIG_FIELDS
        )
        for attr in field_names:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if isinstance(value, list):
                    value = value.copy()
                elif isinstance(value, dict):
                    value = value.copy()
                config[attr] = value

        # Ensure resolved field lists are captured post-configuration
        config["fields"] = list(getattr(self, "fields", []))
        config["properties"] = list(getattr(self, "properties", []))
        config["detail_fields"] = list(getattr(self, "detail_fields", []))
        config["detail_properties"] = list(getattr(self, "detail_properties", []))
        config["form_fields"] = list(getattr(self, "form_fields", []))
        config["form_display_fields"] = list(
            getattr(self, "form_display_fields", [])
        )
        config["form_disabled_fields"] = list(
            getattr(self, "form_disabled_fields", [])
        )

        # Derived booleans
        use_htmx_enabled = config.get("use_htmx") is True
        config["use_htmx_enabled"] = use_htmx_enabled
        config["use_modal_enabled"] = bool(config.get("use_modal") and use_htmx_enabled)
        config["inline_editing_active"] = bool(
            self._is_inline_editing_declared(config.get("inline_edit_fields"))
            and use_htmx_enabled
        )
        config["bulk_edit_enabled"] = bool(
            (config.get("bulk_fields") or config.get("bulk_delete"))
            and config["use_modal_enabled"]
        )
        config["bulk_delete_enabled"] = bool(
            config.get("bulk_delete") and config["bulk_edit_enabled"]
        )
        config["use_crispy_enabled"] = self._resolve_use_crispy_setting(
            config.get("use_crispy")
        )
        config["searchable_selects_enabled"] = config.get("searchable_selects") is not False

        # HTMX/modal defaults
        config["modal_id_resolved"] = config.get("modal_id") or "powercrudBaseModal"
        config["modal_target_resolved"] = (
            config.get("modal_target") or "powercrudModalContent"
        )

        # Table presentation helpers
        config["table_pixel_height_px"] = (
            f"{config.get('table_pixel_height_other_page_elements') or 0}px"
        )
        config["table_max_col_width_css"] = self._resolve_table_max_col_width(
            config.get("table_max_col_width")
        )
        config["table_header_min_wrap_width_css"] = (
            self._resolve_table_header_min_width(
                config.get("table_header_min_wrap_width"),
                config["table_max_col_width_css"],
            )
        )

        return SimpleNamespace(**config)

    def _resolve_table_max_col_width(self, value: int | None) -> str:
        if not value:
            return "25ch"
        return f"{int(value)}ch"

    def _resolve_table_header_min_width(self, value: int | None, fallback: str) -> str:
        if value is None:
            return fallback
        try:
            value_int = int(value)
            max_int = int(fallback.rstrip("ch") or 0)
            clamped = min(value_int, max_int) if max_int else value_int
        except (TypeError, ValueError):
            return fallback
        return f"{clamped}ch"

    def _resolve_use_crispy_setting(self, desired: bool | None) -> bool:
        crispy_installed = "crispy_forms" in settings.INSTALLED_APPS
        if desired is None:
            return crispy_installed
        if desired and not crispy_installed:
            log.warning(
                "use_crispy is set to True, but crispy_forms is not installed. Forcing to False."
            )
            return False
        return desired

    @staticmethod
    def _inline_edit_fields_configured(value: Any) -> bool:
        """Return True when inline-edit configuration is explicitly enabled."""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set, dict)):
            return bool(value)
        return bool(value)

    def _warn_inline_edit_enabled_legacy(self, inline_edit_fields: Any) -> None:
        """
        Warn when a view still declares the removed inline_edit_enabled flag.
        """
        if self._legacy_inline_edit_enabled_value and not self._inline_edit_fields_configured(
            inline_edit_fields
        ):
            message = (
                "inline_edit_enabled=True without inline_edit_fields is deprecated "
                "compatibility-only behavior. PowerCRUD is temporarily falling back "
                "to resolved form_fields. Configure inline_edit_fields explicitly."
            )
        else:
            message = (
                "inline_edit_enabled is deprecated compatibility-only behavior. "
                "Configure inline_edit_fields instead. Legacy views still work for "
                "now, including the old fallback to form fields when "
                "inline_edit_enabled=True and inline_edit_fields is unset."
            )

        warnings.warn(message, FutureWarning, stacklevel=2)

    def _has_legacy_inline_edit_enabled(self) -> bool:
        """
        Return True when the view still declares the legacy inline flag.
        """
        return bool(getattr(self, "_legacy_inline_edit_enabled_present", False))

    def _legacy_inline_editing_enabled(self) -> bool:
        """
        Return the truthy value of the legacy inline flag when declared.
        """
        return bool(getattr(self, "_legacy_inline_edit_enabled_value", False))

    def _legacy_inline_edit_uses_form_fields(self, value: Any) -> bool:
        """
        Return True when legacy inline mode should fall back to form fields.
        """
        return (
            self._has_legacy_inline_edit_enabled()
            and self._legacy_inline_editing_enabled()
            and not self._inline_edit_fields_configured(value)
        )

    def _is_inline_editing_declared(self, value: Any) -> bool:
        """
        Resolve whether inline editing should be treated as configured.
        """
        if self._has_legacy_inline_edit_enabled():
            if not self._legacy_inline_editing_enabled():
                return False
            if self._legacy_inline_edit_uses_form_fields(value):
                return True
        return self._inline_edit_fields_configured(value)


class _ConfigShim:
    """
    Fallback config namespace for tests or mixins that do not have ConfigMixin
    in their MRO. It proxies attribute access to the original object and computes
    the derived attributes (`use_htmx_enabled`, CSS helpers, etc.) so that code
    calling `resolve_config(self)` sees the same shape whether or not the full
    ConfigMixin pipeline has executed.
    """

    def __init__(self, source):
        self._source = source

    def _raw(self, name, default=None):
        return getattr(self._source, name, default)

    def __getattr__(self, name):
        if name == "use_htmx_enabled":
            return self._raw("use_htmx") is True
        if name == "use_modal_enabled":
            return bool(self._raw("use_modal") and self.__getattr__("use_htmx_enabled"))
        if name == "inline_editing_active":
            return bool(
                self._inline_editing_declared()
                and self.__getattr__("use_htmx_enabled")
            )
        if name == "bulk_edit_enabled":
            bulk_fields = self._raw("bulk_fields") or []
            bulk_delete = self._raw("bulk_delete") or False
            return bool(
                (bulk_fields or bulk_delete) and self.__getattr__("use_modal_enabled")
            )
        if name == "bulk_delete_enabled":
            return bool(
                self._raw("bulk_delete") and self.__getattr__("bulk_edit_enabled")
            )
        if name == "use_crispy_enabled":
            desired = self._raw("use_crispy")
            crispy_installed = "crispy_forms" in settings.INSTALLED_APPS
            if desired is None:
                return crispy_installed
            if desired and not crispy_installed:
                log.warning(
                    "use_crispy is set to True, but crispy_forms is not installed. Forcing to False."
                )
                return False
            return desired
        if name == "searchable_selects_enabled":
            return self._raw("searchable_selects", True) is not False
        if name == "modal_id_resolved":
            return self._raw("modal_id") or "powercrudBaseModal"
        if name == "modal_target_resolved":
            return self._raw("modal_target") or "powercrudModalContent"
        if name == "table_pixel_height_px":
            value = self._raw("table_pixel_height_other_page_elements", 0) or 0
            return f"{value}px"
        if name == "table_max_col_width_css":
            value = self._raw("table_max_col_width")
            if not value:
                return "25ch"
            return f"{int(value)}ch"
        if name == "table_header_min_wrap_width_css":
            fallback = self.__getattr__("table_max_col_width_css")
            value = self._raw("table_header_min_wrap_width")
            if value is None:
                return fallback
            try:
                value_int = int(value)
                max_int = int(fallback.rstrip("ch") or 0)
                clamped = min(value_int, max_int) if max_int else value_int
            except (TypeError, ValueError):
                return fallback
            return f"{clamped}ch"
        if name == "templates_path":
            return (
                self._raw("templates_path")
                or f"powercrud/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}"
            )
        if name == "inline_edit_always_visible":
            value = self._raw("inline_edit_always_visible")
            return True if value is None else bool(value)
        if name == "inline_edit_highlight_accent":
            return self._raw("inline_edit_highlight_accent") or "#14b8a6"
        if name == "base_template_path":
            # Do not invent a default; projects must set this explicitly.
            return self._raw("base_template_path")
        if name in {
            "bulk_fields",
            "form_fields",
            "form_display_fields",
            "form_disabled_fields",
            "fields",
            "detail_fields",
            "detail_properties",
            "filterset_fields",
        }:
            return ConfigMixin._dedupe_preserving_first(self._raw(name, []) or [])
        if name in {
            "properties",
            "exclude",
            "properties_exclude",
            "detail_exclude",
            "detail_properties_exclude",
            "form_fields_exclude",
            "filter_null_fields_exclude",
        }:
            return ConfigMixin._dedupe_preserving_first(self._raw(name, []) or [])
        if name in {
            "dropdown_sort_options",
            "field_queryset_dependencies",
        }:
            return self._raw(name, {}) or {}
        return self._raw(name)

    def _inline_editing_declared(self) -> bool:
        """
        Mirror ConfigMixin inline-edit activation logic for shimmed instances.
        """
        legacy_present = hasattr(self._source, "inline_edit_enabled")
        legacy_enabled = bool(getattr(self._source, "inline_edit_enabled", False))
        inline_edit_fields = self._raw("inline_edit_fields")

        if legacy_present:
            if not legacy_enabled:
                return False
            if not ConfigMixin._inline_edit_fields_configured(inline_edit_fields):
                return True

        return ConfigMixin._inline_edit_fields_configured(inline_edit_fields)


def resolve_config(instance):
    """
    Return a configuration namespace for the provided mixin instance.

    If the instance implements `config()` (i.e. it inherits `ConfigMixin`), we
    delegate to that method; otherwise we fall back to `_ConfigShim`, which
    inspects the instance’s attributes directly. This helper makes it easy for
    behavioural mixins to depend on a single API even when they are used in
    isolation inside tests.
    """
    config_getter = getattr(instance, "config", None)
    if callable(config_getter):
        try:
            return config_getter()
        except AttributeError:
            return _ConfigShim(instance)
    return _ConfigShim(instance)


__all__ = ["ConfigMixin", "resolve_config"]
