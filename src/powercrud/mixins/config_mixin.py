from types import SimpleNamespace

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
    templates_path: str = f"powercrud/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}"
    # base_template_path must always be provided by the project; there is no
    # built-in HTML shell. It should point at the app’s real base template.
    base_template_path: str | None = None

    # forms
    use_crispy: bool | None = None

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

    # bulk edit parameters
    bulk_fields: list[str] = []
    bulk_delete: bool = False
    bulk_full_clean: bool = True  # If True, run full_clean() on each object during bulk edit

    # async processing parameters
    bulk_async: bool = False
    bulk_async_conflict_checking = True  # Default enabled
    bulk_min_async_records: int = 20
    bulk_async_backend: str = 'q2'
    bulk_async_notification: str = 'status_page'
    bulk_async_allow_anonymous = True

    # htmx
    use_htmx: bool | None = None
    default_htmx_target: str = '#content'
    hx_trigger: str | dict[str, str] | None = None

    # inline editing
    inline_edit_enabled: bool | None = None
    inline_edit_fields: list[str] | str | None = None
    inline_field_dependencies: dict[str, dict[str, Any]] | None = None
    inline_edit_requires_perm: str | None = None
    inline_edit_allowed: Callable[[Any, Any], bool] | None = None
    inline_preserve_required_fields: bool = True

    # modals (if htmx is active)
    use_modal: bool | None = None
    modal_id: str | None = None
    modal_target: str | None = None

    # table display parameters
    table_pixel_height_other_page_elements: int | float = 0
    table_max_height: int = 70

    table_max_col_width: int | None = None
    table_header_min_wrap_width: int | None = None

    table_classes: str = ''
    action_button_classes: str = ''
    extra_button_classes: str = ''

    # filtering options
    m2m_filter_and_logic = False
    dropdown_sort_options: dict = {}

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
        "dropdown_sort_options",
        "table_classes",
        "action_button_classes",
        "extra_button_classes",
        "m2m_filter_and_logic",
        "inline_preserve_required_fields",
        "async_manager_class",
        "async_manager_class_path",
        "async_manager_config",
        "paginate_by",
    }

    def __init__(self, *args, **kwargs):  # pragma: no cover
        super().__init__(*args, **kwargs)
        self._validated_config = None

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

        self._configure_fields()
        self._configure_properties()
        self._configure_detail_fields()
        self._configure_detail_properties()
        self._configure_bulk_fields()
        self._configure_form_fields()

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

    def _configure_fields(self):
        if not self.fields or self.fields == '__all__':
            self.fields = self._get_all_fields()
        elif type(self.fields) == list:
            all_fields = self._get_all_fields()
            for field in self.fields:
                if field not in all_fields:
                    raise ValueError(f"Field {field} not defined in {self.model.__name__}")
        elif type(self.fields) != list:
            raise TypeError("fields must be a list")
        else:
            raise ValueError("fields must be '__all__', a list of valid fields or not defined")

        if isinstance(self.exclude, list):
            self.fields = [field for field in self.fields if field not in self.exclude]
        else:
            raise TypeError("exclude must be a list")

    def _configure_properties(self):
        if self.properties:
            if self.properties == '__all__':
                self.properties = self._get_all_properties()
            elif type(self.properties) == list:
                all_properties = self._get_all_properties()
                for prop in self.properties:
                    if prop not in all_properties:
                        raise ValueError(f"Property {prop} not defined in {self.model.__name__}")
            elif type(self.properties) != list:
                raise TypeError("properties must be a list or '__all__'")

        if type(self.properties_exclude) == list:
            self.properties = [prop for prop in self.properties if prop not in self.properties_exclude]
        else:
            raise TypeError("properties_exclude must be a list")

    def _configure_detail_fields(self):
        if self.detail_fields == '__all__':
            self.detail_fields = self._get_all_fields()
        elif not self.detail_fields or self.detail_fields == '__fields__':
            self.detail_fields = self.fields
        elif type(self.detail_fields) == list:
            all_fields = self._get_all_fields()
            for field in self.detail_fields:
                if field not in all_fields:
                    raise ValueError(f"detail_field {field} not defined in {self.model.__name__}")
        elif type(self.detail_fields) != list:
            raise TypeError("detail_fields must be a list or '__all__' or '__fields__' or a list of fields")

        if type(self.detail_exclude) == list:
            self.detail_fields = [field for field in self.detail_fields if field not in self.detail_exclude]
        else:
            raise TypeError("detail_fields_exclude must be a list")

    def _configure_detail_properties(self):
        if self.detail_properties:
            if self.detail_properties == '__all__':
                self.detail_properties = self._get_all_properties()
            elif self.detail_properties == '__properties__':
                self.detail_properties = self.properties
            elif type(self.detail_properties) == list:
                all_properties = self._get_all_properties()
                for prop in self.detail_properties:
                    if prop not in all_properties:
                        raise ValueError(f"Property {prop} not defined in {self.model.__name__}")
            elif type(self.detail_properties) != list:
                raise TypeError("detail_properties must be a list or '__all__' or '__properties__'")

        if type(self.detail_properties_exclude) == list:
            self.detail_properties = [
                prop for prop in self.detail_properties if prop not in self.detail_properties_exclude
            ]
        else:
            raise TypeError("detail_properties_exclude must be a list")

    def _configure_bulk_fields(self):
        if self.bulk_fields:
            if isinstance(self.bulk_fields, list):
                all_fields = self._get_all_fields()
                for field_name in self.bulk_fields:
                    if not isinstance(field_name, str):
                        raise ValueError(
                            f"Invalid bulk field configuration: {field_name}. Must be a string."
                        )

                    if field_name not in all_fields:
                        raise ValueError(
                            f"Bulk field '{field_name}' not defined in {self.model.__name__}"
                        )

    def _configure_form_fields(self):
        all_editable = self._get_all_editable_fields()

        if not self.form_fields:
            self.form_fields = [
                f for f in self.detail_fields
                if f in all_editable
            ]
        elif self.form_fields == '__all__':
            self.form_fields = all_editable
        elif self.form_fields == '__fields__':
            self.form_fields = [
                f for f in self.fields
                if f in all_editable
            ]
        else:
            invalid_fields = [f for f in self.form_fields if f not in all_editable]
            if invalid_fields:
                raise ValueError(
                    f"The following form_fields are not editable fields in {self.model.__name__}: "
                    f"{', '.join(invalid_fields)}"
                )

        if self.form_fields_exclude:
            self.form_fields = [
                f for f in self.form_fields
                if f not in self.form_fields_exclude
            ]

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
            if hasattr(field, 'editable') and field.editable
        ]

    def _get_all_properties(self):
        return [
            name
            for name in dir(self.model)
            if isinstance(getattr(self.model, name), property) and name != 'pk'
        ]

    def _build_config_namespace(self) -> SimpleNamespace:
        config: dict[str, Any] = {}
        field_names = set(PowerCRUDMixinValidator.model_fields.keys()) | self.EXTRA_CONFIG_FIELDS
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

        # Derived booleans
        use_htmx_enabled = config.get("use_htmx") is True
        config["use_htmx_enabled"] = use_htmx_enabled
        config["use_modal_enabled"] = bool(config.get("use_modal") and use_htmx_enabled)
        config["inline_editing_active"] = bool(config.get("inline_edit_enabled") and use_htmx_enabled)
        config["bulk_edit_enabled"] = bool(
            (config.get("bulk_fields") or config.get("bulk_delete")) and config["use_modal_enabled"]
        )
        config["bulk_delete_enabled"] = bool(config.get("bulk_delete") and config["bulk_edit_enabled"])
        config["use_crispy_enabled"] = self._resolve_use_crispy_setting(config.get("use_crispy"))

        # HTMX/modal defaults
        config["modal_id_resolved"] = config.get("modal_id") or "powercrudBaseModal"
        config["modal_target_resolved"] = config.get("modal_target") or "powercrudModalContent"

        # Table presentation helpers
        config["table_pixel_height_px"] = f"{config.get('table_pixel_height_other_page_elements') or 0}px"
        config["table_max_col_width_css"] = self._resolve_table_max_col_width(config.get("table_max_col_width"))
        config["table_header_min_wrap_width_css"] = self._resolve_table_header_min_width(
            config.get("table_header_min_wrap_width"),
            config["table_max_col_width_css"],
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
            return bool(self._raw("inline_edit_enabled") and self.__getattr__("use_htmx_enabled"))
        if name == "bulk_edit_enabled":
            bulk_fields = self._raw("bulk_fields") or []
            bulk_delete = self._raw("bulk_delete") or False
            return bool((bulk_fields or bulk_delete) and self.__getattr__("use_modal_enabled"))
        if name == "bulk_delete_enabled":
            return bool(self._raw("bulk_delete") and self.__getattr__("bulk_edit_enabled"))
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
            return self._raw("templates_path") or f"powercrud/{get_powercrud_setting('POWERCRUD_CSS_FRAMEWORK')}"
        if name == "base_template_path":
            # Do not invent a default; projects must set this explicitly.
            return self._raw("base_template_path")
        if name in {"bulk_fields", "form_fields", "fields", "detail_fields", "detail_properties"}:
            return self._raw(name, []) or []
        if name in {"dropdown_sort_options", "inline_field_dependencies"}:
            return self._raw(name, {}) or {}
        return self._raw(name)


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
