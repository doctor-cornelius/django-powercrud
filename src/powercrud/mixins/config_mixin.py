from types import SimpleNamespace
import warnings

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.http import HttpResponseForbidden
from django.db.models.fields.reverse_related import ManyToOneRel
from typing import Any, Callable

from ..actions import PowerAction, PowerButton
from ..cell_tooltips import has_lazy_list_cell_tooltip
from ..powerfields import compile_powerfields
from ..row_actions import is_lazy_row_action_state_action
from ..validators import DEFAULT_PAGINATE_BY, PowerCRUDMixinValidator

from powercrud.conf import get_powercrud_setting
from powercrud.logging import get_logger

log = get_logger(__name__)

DEFAULT_MODAL_BOX_CLASSES = "modal-box flex max-h-[calc(100dvh-2rem)] flex-col"
DEFAULT_MODAL_BODY_CLASSES = "min-h-0 flex-1 overflow-y-auto py-4"


def has_selection_aware_extra_buttons(extra_buttons: Any) -> bool:
    """Return True when any extra button declares ``uses_selection=True``."""
    if not extra_buttons:
        return False
    if not isinstance(extra_buttons, (list, tuple)):
        return False

    for button in extra_buttons:
        if isinstance(button, PowerButton) and button.uses_selection:
            return True
        if isinstance(button, dict) and bool(button.get("uses_selection", False)):
            return True
    return False


def has_lazy_row_action_state(extra_actions: Any) -> bool:
    """Return True when any row action declares lazy runtime-state resolution."""
    if not extra_actions:
        return False
    if not isinstance(extra_actions, (list, tuple)):
        return False

    for action in extra_actions:
        if isinstance(action, PowerAction):
            action = action.to_dict()
        if isinstance(action, dict) and is_lazy_row_action_state_action(action):
            return True
    return False


def has_lazy_list_cell_tooltip_state(list_cell_tooltip_fields: Any) -> bool:
    """Return True when any list-cell tooltip declares lazy content resolution."""
    return has_lazy_list_cell_tooltip(list_cell_tooltip_fields)


FIELD_INTENT_CONFIG_FIELDS = {
    "fields",
    "properties",
    "exclude",
    "properties_exclude",
    "default_list_fields",
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
    "inline_edit_enabled",
    "list_cell_tooltip_fields",
    "field_labels",
    "column_help_text",
    "column_alignments",
    "column_value_formats",
    "field_queryset_dependencies",
    "link_fields",
}


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
    view_help: dict[str, Any] | None = None
    view_help_default_color: str = "base"
    view_help_min_width: str = "40rem"
    column_help_text: dict[str, str] | None = None
    field_labels: dict[str, str] | None = None
    column_alignments: dict[str, str] | None = None
    column_value_formats: dict[str, str] | None = None
    default_datetime_value_format: str = "date"
    list_cell_tooltip_fields: list[str] | dict[str, Any] | None = None
    list_cell_link_default_open_in: str = "new"
    link_fields: dict[str, Any] | None = None
    column_sort_fields_override: dict[str, str] | None = None

    # forms
    use_crispy: bool | None = None
    searchable_selects: bool | None = True

    # field and property inclusion scope
    power_fields: list[Any] | None = None
    exclude: list[str] = []
    properties: list[str] = []
    properties_exclude: list[str] = []
    list_options_enabled: bool | None = None
    default_list_fields: list[str] | None = None

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
    inline_save_refresh_policy: str = "reset_if_filtered_out"

    # modals (if htmx is active)
    use_modal: bool | None = None
    modal_id: str | None = None
    modal_target: str | None = None
    modal_classes: str | None = "modal"
    modal_box_classes: str | None = DEFAULT_MODAL_BOX_CLASSES
    modal_body_classes: str | None = DEFAULT_MODAL_BODY_CLASSES
    bulk_modal_box_classes: str | None = None

    # table display parameters
    table_pixel_height_other_page_elements: int | float = 0
    table_max_height: int = 70

    table_max_col_width: int | None = None
    table_header_min_wrap_width: int | None = None

    table_classes: str = ""
    action_button_classes: str = ""
    extra_button_classes: str = ""
    extra_buttons_mode: str = "buttons"
    extra_actions_mode: str = "buttons"
    extra_actions_dropdown_open_upward_bottom_rows: int = 3
    show_record_count: bool = False
    show_bulk_selection_meta: bool = True
    extra_button_selection_controls_disabled: bool = False

    # filtering options
    default_filterset_fields: list[str] | None = None
    m2m_filter_and_logic = False
    dropdown_sort_options: dict = {}
    filter_null_fields_exclude: list[str] = []

    # async manager configuration
    async_manager_class = None
    async_manager_class_path: str | None = None
    async_manager_config: dict | None = None

    # pagination defaults
    paginate_by: int | None = DEFAULT_PAGINATE_BY
    page_size_options: list[int] | None = None
    page_size_all_enabled: bool = True

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
        "default_filterset_fields",
        "table_classes",
        "action_button_classes",
        "extra_button_classes",
        "extra_buttons_mode",
        "extra_actions_mode",
        "extra_actions_dropdown_open_upward_bottom_rows",
        "show_record_count",
        "show_bulk_selection_meta",
        "extra_button_selection_controls_disabled",
        "m2m_filter_and_logic",
        "inline_preserve_required_fields",
        "async_manager_class",
        "async_manager_class_path",
        "async_manager_config",
        "paginate_by",
        "page_size_options",
        "page_size_all_enabled",
        "extra_buttons",
        "extra_actions",
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
        "default_filterset_fields",
        "default_list_fields",
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
        class_config = resolve_class_config(type(self))
        self._powerfield_config_active = bool(
            getattr(class_config, "_powerfield_config_active", False)
        )
        self._powerfield_declared_primitive_names = set(
            getattr(class_config, "_powerfield_declared_primitive_names", set())
        )
        initial_config = {}
        for attr in _get_config_field_names():
            if hasattr(class_config, attr):
                initial_config[attr] = getattr(class_config, attr)
            if attr in self.__dict__:
                initial_config[attr] = getattr(self, attr)

        self._legacy_inline_edit_enabled_present = (
            "inline_edit_enabled" in initial_config
        )
        self._legacy_inline_edit_enabled_value = bool(
            initial_config.get("inline_edit_enabled", False)
        )

        if self._legacy_inline_edit_enabled_present:
            self._warn_inline_edit_enabled_legacy(
                initial_config.get("inline_edit_fields")
            )

        config_dict = {}
        for attr in PowerCRUDMixinValidator.model_fields.keys():
            if attr in initial_config:
                config_dict[attr] = initial_config[attr]

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
        self._normalize_list_cell_tooltip_fields()
        self._warn_list_cell_tooltip_fields_legacy()
        self._configure_fields()
        self._configure_properties()
        self._configure_default_list_fields()
        self._configure_detail_fields()
        self._configure_detail_properties()
        self._configure_field_labels()
        self._configure_column_alignments()
        self._configure_column_value_formats()
        self._configure_link_fields()
        self._configure_bulk_fields()
        self._configure_inline_edit_fields()
        self._warn_link_fields_inline_overlap()
        self._configure_form_fields()
        self._configure_form_display_fields()
        try:
            self._configure_extra_buttons()
            self._configure_extra_actions()
        except (TypeError, ValueError) as e:
            class_name = self.__class__.__name__
            raise ImproperlyConfigured(
                f"Invalid configuration in class '{class_name}': {str(e)}"
            ) from e

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

    def has_power_permission(self, permission: str, request: Any, obj: Any = None) -> bool:
        """
        Resolve a permission string for permission-aware affordance declarations.
        """
        user = getattr(request, "user", None)
        return bool(user and user.has_perm(permission))

    def has_power_create_permission(self, request: Any) -> bool:
        """
        Return whether the request may use PowerCRUD-owned create handling.
        """
        return True

    def has_power_detail_permission(self, request: Any, obj: Any) -> bool:
        """
        Return whether the request may use PowerCRUD-owned detail handling.
        """
        return True

    def has_power_update_permission(self, request: Any, obj: Any) -> bool:
        """
        Return whether the request may use PowerCRUD-owned update handling.
        """
        return True

    def has_power_delete_permission(self, request: Any, obj: Any) -> bool:
        """
        Return whether the request may use PowerCRUD-owned delete handling.
        """
        return True

    def has_power_bulk_update_permission(self, request: Any) -> bool:
        """
        Return whether the request may use PowerCRUD-owned bulk update handling.
        """
        return True

    def has_power_bulk_delete_permission(self, request: Any) -> bool:
        """
        Return whether the request may use PowerCRUD-owned bulk delete handling.
        """
        return True

    def handle_power_permission_denied(
        self,
        request: Any,
        operation: str,
        obj: Any = None,
    ) -> HttpResponseForbidden:
        """
        Return the response used when a PowerCRUD-owned operation is denied.
        """
        return HttpResponseForbidden(f"{operation} is not permitted.")

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

    def _normalize_list_cell_tooltip_fields(self) -> None:
        """
        Normalize list-cell tooltip config while preserving legacy list support.
        """
        value = getattr(self, "list_cell_tooltip_fields", None)
        if isinstance(value, list):
            self.list_cell_tooltip_fields = self._dedupe_preserving_first(value)
        elif isinstance(value, dict):
            self.list_cell_tooltip_fields = dict(value)

    def _warn_list_cell_tooltip_fields_legacy(self) -> None:
        """
        Warn when a view still uses the legacy list-cell tooltip list shape.
        """
        if not isinstance(getattr(self, "list_cell_tooltip_fields", None), list):
            return
        warnings.warn(
            'list_cell_tooltip_fields as a list is deprecated and targeted for '
            'removal before v1.0; use {"field_name": "hook_name"} instead.',
            FutureWarning,
            stacklevel=2,
        )

    def _configure_fields(self):
        if (
            self._powerfield_config_active
            and "fields" not in self._powerfield_declared_primitive_names
            and not self.fields
        ):
            self.fields = []
            if not isinstance(self.exclude, list):
                raise TypeError("exclude must be a list")
            return

        if not self.fields or self.fields == "__all__":
            self.fields = self._get_all_fields()
        elif isinstance(self.fields, list):
            invalid_fields = [
                field
                for field in self.fields
                if not self._is_known_list_field_name(field)
            ]
            if invalid_fields and not self._can_defer_queryset_field_validation():
                raise ValueError(
                    "The following fields are not model fields or queryset "
                    f"annotations in {self.model.__name__}: "
                    f"{', '.join(invalid_fields)}. If a field is a queryset "
                    "annotation, declare it with annotate(public_name=...) before "
                    "PowerCRUD resolves the list."
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

    def _configure_default_list_fields(self):
        """
        Validate the opt-in default visible list-column subset.

        Queryset annotation names may need request-time validation when a view
        adds annotations in ``get_queryset()``. In that case this method allows
        configured list-field names that are not yet known model fields.
        """
        if self.default_list_fields is None:
            return

        if not isinstance(self.default_list_fields, list):
            raise TypeError("default_list_fields must be a list")

        if not self.default_list_fields:
            raise ValueError("default_list_fields cannot be empty")

        allowed_columns = self._get_configurable_list_column_names()
        invalid_columns = [
            field_name
            for field_name in self.default_list_fields
            if field_name not in allowed_columns
        ]
        deferred_invalid_columns = [
            field_name
            for field_name in invalid_columns
            if field_name not in (self.properties or [])
        ]
        property_invalid_columns = [
            field_name
            for field_name in invalid_columns
            if field_name in (self.properties or [])
        ]
        if property_invalid_columns:
            raise ValueError(
                "The following default_list_fields are not valid list columns in "
                f"{self.model.__name__}: {', '.join(property_invalid_columns)}"
            )
        if deferred_invalid_columns and not self._can_defer_queryset_field_validation():
            raise ValueError(
                "The following default_list_fields are not model fields, queryset "
                f"annotations, or properties in {self.model.__name__}: "
                f"{', '.join(deferred_invalid_columns)}"
            )

    def _configure_detail_fields(self):
        if (
            self._powerfield_config_active
            and "detail_fields" not in self._powerfield_declared_primitive_names
            and not self.detail_fields
        ):
            self.detail_fields = []
            if not isinstance(self.detail_exclude, list):
                raise TypeError("detail_fields_exclude must be a list")
            return

        if self.detail_fields == "__all__":
            self.detail_fields = self._get_all_fields()
        elif not self.detail_fields or self.detail_fields == "__fields__":
            model_fields = set(self._get_all_fields())
            self.detail_fields = [
                field for field in self.fields if field in model_fields
            ]
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
        if (
            self._powerfield_config_active
            and "detail_properties" not in self._powerfield_declared_primitive_names
            and not self.detail_properties
        ):
            self.detail_properties = []
            if not isinstance(self.detail_properties_exclude, list):
                raise TypeError("detail_properties_exclude must be a list")
            return

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

        if (
            self._powerfield_config_active
            and "form_fields" not in self._powerfield_declared_primitive_names
            and not self.form_fields
        ):
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

    def _configure_column_alignments(self) -> None:
        """
        Validate optional rendered-column alignment overrides.

        Keys may reference either model fields or model properties so the
        mapping can describe whichever columns a downstream list chooses to
        render.
        """
        if self.column_alignments is None:
            self.column_alignments = {}
            return

        if not isinstance(self.column_alignments, dict):
            raise ValueError("column_alignments must be a dictionary when provided")

        valid_names = self._get_configurable_list_column_names()
        invalid_names = [
            name for name in self.column_alignments.keys() if name not in valid_names
        ]
        if invalid_names:
            raise ValueError(
                "The following column_alignments keys are not model fields, "
                "queryset annotations, configured list fields, or properties "
                f"in {self.model.__name__}: {', '.join(invalid_names)}"
            )

    @staticmethod
    def _get_allowed_temporal_value_formats(field: Any) -> set[str] | None:
        """Return permitted list-value formats for a temporal Django field."""
        if isinstance(field, models.DateTimeField):
            return {"date", "time", "datetime"}
        if isinstance(field, models.DateField):
            return {"date"}
        if isinstance(field, models.TimeField):
            return {"time"}
        return None

    def _raise_invalid_column_value_format(
        self,
        field_name: str,
        value_format: str,
        field: Any | None,
    ) -> None:
        """Raise a clear configuration error for an unusable temporal format."""
        if field is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__}.column_value_formats[{field_name!r}] "
                "must reference a model field or queryset annotation with an "
                "inferable temporal output_field."
            )

        allowed_formats = self._get_allowed_temporal_value_formats(field)
        field_type = field.get_internal_type()
        if allowed_formats is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__}.column_value_formats[{field_name!r}] "
                f"cannot format {field_type}. Only DateField, TimeField, and "
                "DateTimeField columns are supported."
            )
        if value_format not in allowed_formats:
            allowed = ", ".join(sorted(allowed_formats))
            raise ImproperlyConfigured(
                f"{self.__class__.__name__}.column_value_formats[{field_name!r}] "
                f"specifies {value_format!r}, but {field_name} is a {field_type}. "
                f"Allowed formats: {allowed}."
            )

    def _validate_column_value_formats_against_queryset(
        self,
        queryset: Any | None = None,
    ) -> None:
        """Validate configured temporal list formats against available field metadata."""
        for field_name, value_format in self.column_value_formats.items():
            if field_name in self._get_all_properties():
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__}.column_value_formats[{field_name!r}] "
                    "cannot reference a property because its temporal type cannot be "
                    "validated reliably."
                )
            model_field = None
            try:
                model_field = self.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                pass
            field = model_field or self._get_queryset_annotation_output_field(
                field_name,
                queryset=queryset,
            )
            self._raise_invalid_column_value_format(field_name, value_format, field)

    def _configure_column_value_formats(self) -> None:
        """Validate temporal list value-format configuration available at setup time."""
        if self.column_value_formats is None:
            self.column_value_formats = {}
            return

        if not isinstance(self.column_value_formats, dict):
            raise ImproperlyConfigured(
                "column_value_formats must be a dictionary when provided"
            )

        for field_name, value_format in self.column_value_formats.items():
            if field_name in self._get_all_properties():
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__}.column_value_formats[{field_name!r}] "
                    "cannot reference a property because its temporal type cannot be "
                    "validated reliably."
                )

            if self._is_model_field_name(field_name):
                self._validate_column_value_format_for_name(
                    field_name,
                    value_format,
                )
                continue

            if self._is_queryset_annotation_field(field_name):
                self._validate_column_value_format_for_name(
                    field_name,
                    value_format,
                )
                continue

            if self._can_defer_queryset_field_validation() and field_name in self.fields:
                continue

            raise ImproperlyConfigured(
                f"{self.__class__.__name__}.column_value_formats[{field_name!r}] "
                "must reference a model field or queryset annotation."
            )

    def _validate_column_value_format_for_name(
        self,
        field_name: str,
        value_format: str,
        queryset: Any | None = None,
    ) -> None:
        """Validate one temporal list-format entry against field metadata."""
        model_field = None
        try:
            model_field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            pass
        field = model_field or self._get_queryset_annotation_output_field(
            field_name,
            queryset=queryset,
        )
        self._raise_invalid_column_value_format(field_name, value_format, field)

    def _configure_field_labels(self) -> None:
        """
        Validate optional explicit display labels for fields and properties.

        Keys may reference model fields, properties, or configured queryset
        annotation columns so one label map can serve list, form, inline, and
        bulk-edit surfaces.
        """
        if self.field_labels is None:
            self.field_labels = {}
            return

        if not isinstance(self.field_labels, dict):
            raise ValueError("field_labels must be a dictionary when provided")

        valid_names = self._get_configurable_list_column_names()
        invalid_names = [
            name for name in self.field_labels.keys() if name not in valid_names
        ]
        if invalid_names:
            raise ValueError(
                "The following field_labels keys are not model fields, queryset "
                "annotations, configured list fields, or properties "
                f"in {self.model.__name__}: {', '.join(invalid_names)}"
            )

    def _configure_link_fields(self) -> None:
        """
        Validate and normalize declarative list-cell link configuration.

        Keys may reference either model fields or model properties. Unrendered
        names remain harmless, but unknown names should fail loudly so public
        config mistakes do not silently disappear.
        """
        if self.link_fields is None:
            self.link_fields = {}
            return

        if not isinstance(self.link_fields, dict):
            raise ValueError("link_fields must be a dictionary when provided")

        valid_names = self._get_configurable_list_column_names()
        invalid_names = [
            name for name in self.link_fields.keys() if name not in valid_names
        ]
        if invalid_names:
            raise ValueError(
                "The following link_fields keys are not model fields, queryset "
                "annotations, configured list fields, or properties "
                f"in {self.model.__name__}: {', '.join(invalid_names)}"
            )

        normalized: dict[str, dict[str, str]] = {}
        default_open_in = self._normalize_list_cell_open_in(
            self.list_cell_link_default_open_in
        )
        for name, config in self.link_fields.items():
            if isinstance(config, str):
                normalized[name] = {"view_name": config, "open_in": default_open_in}
                continue

            if not isinstance(config, dict):
                raise ValueError(
                    "link_fields values must be either a view-name string or a dict"
                )

            unsupported_keys = set(config.keys()) - {
                "view_name",
                "url",
                "pk_attr",
                "open_in",
                "modal_box_classes",
            }
            if unsupported_keys:
                raise ValueError(
                    "link_fields dict values only support one of 'view_name' or "
                    "'url', plus optional 'pk_attr', 'open_in', and "
                    "'modal_box_classes'. Unsupported keys: "
                    f"{', '.join(sorted(unsupported_keys))}"
                )

            view_name = str(config.get("view_name") or "").strip()
            url = str(config.get("url") or "").strip()
            if bool(view_name) == bool(url):
                raise ValueError(
                    "link_fields dict values must include exactly one non-empty "
                    "'view_name' or 'url'"
                )

            normalized[name] = {
                "open_in": self._normalize_list_cell_open_in(
                    config.get("open_in") or default_open_in
                )
            }
            if view_name:
                normalized[name]["view_name"] = view_name
            if url:
                normalized[name]["url"] = url

            if config.get("pk_attr"):
                if not view_name:
                    raise ValueError(
                        "link_fields.pk_attr is only supported with view_name links"
                    )
                normalized[name]["pk_attr"] = str(config["pk_attr"])

            modal_box_classes = config.get("modal_box_classes")
            if modal_box_classes is not None:
                if normalized[name]["open_in"] != "modal":
                    raise ValueError(
                        "link_fields.modal_box_classes is only supported when "
                        "open_in is 'modal'"
                    )
                if (
                    not isinstance(modal_box_classes, str)
                    or not modal_box_classes.strip()
                ):
                    raise ValueError(
                        "link_fields.modal_box_classes must be a non-empty string "
                        "when provided"
                    )
                normalized[name]["modal_box_classes"] = modal_box_classes.strip()

        self.link_fields = normalized

    @staticmethod
    def _normalize_list_cell_open_in(value: Any) -> str:
        """
        Normalize list-cell link opening modes for view-level configuration.
        """
        if not isinstance(value, str) or value.strip() not in {
            "current",
            "new",
            "modal",
        }:
            raise ValueError(
                "list_cell_link_default_open_in must be 'current', 'new', or 'modal'"
            )
        return value.strip()

    def _warn_link_fields_inline_overlap(self) -> None:
        """
        Warn when a configured list-cell link can never render because inline
        editing will always take precedence for the same field.
        """
        configured_links = set((self.link_fields or {}).keys())
        if not configured_links:
            return

        inline_value = getattr(self, "inline_edit_fields", None)
        overlapping_model_fields: set[str] = set()
        model_fields = set(self._get_all_fields())

        if isinstance(inline_value, list):
            overlapping_model_fields = configured_links & set(inline_value)
        elif inline_value in {"__all__", "__fields__"}:
            overlapping_model_fields = configured_links & model_fields

        if overlapping_model_fields:
            log.warning(
                "link_fields entries for %s overlap inline_edit_fields on %s; "
                "PowerCRUD will skip linking for inline-editable cells",
                ", ".join(sorted(overlapping_model_fields)),
                self.model.__name__,
            )

    def _get_queryset_annotations(self, queryset: Any | None = None) -> dict[str, Any]:
        """
        Return annotation expressions declared on a queryset without evaluation.

        Django stores public annotation names on ``query.annotations``. This is
        the stable point PowerCRUD can inspect to decide whether a configured
        read-only column is backed by the effective queryset.
        """
        if queryset is None:
            queryset = getattr(self, "queryset", None)

        query = getattr(queryset, "query", None)
        annotations = getattr(query, "annotations", None)
        if isinstance(annotations, dict):
            return annotations
        return {}

    def _get_queryset_annotation_names(self, queryset: Any | None = None) -> list[str]:
        """Return public annotation names declared on the queryset."""
        return list(self._get_queryset_annotations(queryset).keys())

    def _get_queryset_annotation_output_field(
        self,
        field_name: str,
        queryset: Any | None = None,
    ) -> Any | None:
        """Return the Django output field for a queryset annotation when known."""
        annotation = self._get_queryset_annotations(queryset).get(field_name)
        if annotation is None:
            return None
        try:
            return annotation.output_field
        except Exception:
            return None

    def _is_queryset_annotation_field(
        self,
        field_name: str,
        queryset: Any | None = None,
    ) -> bool:
        """Return whether a name is a public queryset annotation."""
        return field_name in self._get_queryset_annotations(queryset)

    def _is_model_field_name(self, field_name: str) -> bool:
        """Return whether a name is a model field known to Django metadata."""
        try:
            self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return False
        return True

    def _is_known_list_field_name(
        self,
        field_name: str,
        queryset: Any | None = None,
    ) -> bool:
        """Return whether a name can be rendered as a first-class list field."""
        return self._is_model_field_name(field_name) or self._is_queryset_annotation_field(
            field_name,
            queryset=queryset,
        )

    def _can_defer_queryset_field_validation(self) -> bool:
        """
        Return whether unresolved list fields may be request-time annotations.

        Views with custom ``get_queryset()`` can add annotations after instance
        initialization, so PowerCRUD validates those names once the effective
        queryset is available.
        """
        get_queryset = getattr(type(self), "get_queryset", None)
        if get_queryset is None:
            return False
        return getattr(get_queryset, "__module__", "") != "powercrud.mixins.core_mixin"

    def _get_configurable_list_column_names(self) -> set[str]:
        """
        Return names allowed in list-display configuration at setup time.

        This deliberately includes configured list fields so request-time
        annotations can be referenced by column help, alignment, and link config
        before the queryset exists.
        """
        configured_fields = getattr(self, "fields", []) or []
        configured_properties = getattr(self, "properties", []) or []
        return (
            set(self._get_all_fields())
            | set(self._get_queryset_annotation_names())
            | set(configured_fields)
            | set(self._get_all_properties())
            | set(configured_properties)
        )

    def validate_list_fields_against_queryset(
        self,
        field_names: list[str],
        queryset: Any | None = None,
        *,
        config_name: str = "fields",
    ) -> None:
        """
        Validate list-field names against model fields and queryset annotations.
        """
        invalid_fields = [
            field
            for field in field_names
            if not self._is_known_list_field_name(field, queryset=queryset)
        ]
        if invalid_fields:
            raise ValueError(
                f"The following {config_name} are not model fields or queryset "
                f"annotations in {self.model.__name__}: "
                f"{', '.join(invalid_fields)}. If a field is a queryset "
                "annotation, declare it with annotate(public_name=...) before "
                "PowerCRUD resolves the list."
            )

    def _configure_extra_buttons(self) -> None:
        """
        Validate and normalize extra button definitions.
        """
        extra_buttons = getattr(self, "extra_buttons", [])
        if extra_buttons is None:
            self.extra_buttons = []
            return
        if not isinstance(extra_buttons, list):
            raise ValueError("extra_buttons must be a list of dictionaries")

        normalized_buttons: list[dict[str, Any]] = []
        for index, button in enumerate(extra_buttons):
            if isinstance(button, PowerButton):
                button = button.to_dict()
            if not isinstance(button, dict):
                raise ValueError(
                    f"extra_buttons[{index}] must be a dictionary or PowerButton"
                )

            normalized = button.copy()
            uses_selection = bool(normalized.get("uses_selection", False))
            clear_selection_on_success = normalized.get(
                "clear_selection_on_success",
                uses_selection,
            )
            selection_min_count = normalized.get("selection_min_count", 0)
            selection_min_behavior = normalized.get("selection_min_behavior", "allow")

            try:
                selection_min_count = int(selection_min_count)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"extra_buttons[{index}].selection_min_count must be an integer"
                ) from exc

            if selection_min_count < 0:
                raise ValueError(
                    f"extra_buttons[{index}].selection_min_count must be >= 0"
                )

            if selection_min_behavior not in {"allow", "disable"}:
                raise ValueError(
                    "extra_buttons[%s].selection_min_behavior must be "
                    "'allow' or 'disable'" % index
                )

            if not isinstance(clear_selection_on_success, bool):
                raise ValueError(
                    f"extra_buttons[{index}].clear_selection_on_success must be True or False"
                )

            if uses_selection and normalized.get("needs_pk", False):
                raise ValueError(
                    f"extra_buttons[{index}] cannot set needs_pk=True when uses_selection=True"
                )

            selection_keys_present = any(
                key in normalized
                for key in (
                    "selection_min_count",
                    "selection_min_behavior",
                    "selection_min_reason",
                )
            )
            if not uses_selection and selection_keys_present:
                log.warning(
                    "extra_buttons[%s] defines selection_min_* settings without uses_selection=True; "
                    "PowerCRUD will ignore those selection thresholds",
                    index,
                )

            if clear_selection_on_success and not uses_selection:
                log.warning(
                    "extra_buttons[%s] defines clear_selection_on_success without uses_selection=True; "
                    "PowerCRUD will ignore the clear-on-success flag",
                    index,
                )
                clear_selection_on_success = False

            normalized["uses_selection"] = uses_selection
            normalized["clear_selection_on_success"] = clear_selection_on_success
            normalized["selection_min_count"] = selection_min_count
            normalized["selection_min_behavior"] = selection_min_behavior
            normalized["refresh_list_on_modal_close"] = (
                self._normalize_extra_modal_close_refresh_flag(
                    normalized,
                    index,
                    "extra_buttons",
                )
            )
            self._normalize_permission_affordance_config(
                normalized,
                index,
                "extra_buttons",
            )
            normalized_buttons.append(normalized)

        self.extra_buttons = normalized_buttons

    @staticmethod
    def _normalize_extra_modal_close_refresh_flag(
        item: dict[str, Any],
        index: int,
        config_name: str,
    ) -> bool:
        """
        Return the explicit modal-close refresh flag for a custom action/button.
        """
        value = item.get("refresh_list_on_modal_close", False)
        if not isinstance(value, bool):
            raise ValueError(
                f"{config_name}[{index}].refresh_list_on_modal_close must be True or False"
            )
        return value

    def _validate_optional_extra_string(
        self,
        value: Any,
        index: int,
        config_name: str,
        setting_name: str,
    ) -> str | None:
        """
        Return a non-empty optional string setting for an action/button item.
        """
        if value is None or value == "":
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{config_name}[{index}].{setting_name} must be a non-empty string"
            )
        return value

    def _resolve_extra_config_method(
        self, method_name: Any, index: int, setting_name: str, config_name: str
    ) -> str | None:
        """
        Resolve and validate a named action/button hook declared on the view.
        """
        if method_name is None or method_name == "":
            return None
        if not isinstance(method_name, str):
            raise ValueError(
                f"{config_name}[{index}].{setting_name} must be a method name string"
            )

        resolver = getattr(self, method_name, None)
        if not callable(resolver):
            raise ValueError(
                f"{config_name}[{index}].{setting_name} references unknown method '{method_name}'"
            )
        return method_name

    def _resolve_extra_action_method(
        self, method_name: Any, index: int, setting_name: str
    ) -> str | None:
        """
        Resolve and validate a named extra-action hook declared on the view.
        """
        return self._resolve_extra_config_method(
            method_name,
            index,
            setting_name,
            "extra_actions",
        )

    def _normalize_permission_affordance_config(
        self,
        item: dict[str, Any],
        index: int,
        config_name: str,
    ) -> None:
        """
        Normalize shared permission affordance settings for an action/button.
        """
        permission_keys_present = any(
            key in item
            for key in (
                "permission",
                "permission_check",
                "permission_behavior",
                "permission_denied_reason",
            )
        )
        permission = self._validate_optional_extra_string(
            item.get("permission"),
            index,
            config_name,
            "permission",
        )
        permission_check = self._resolve_extra_config_method(
            item.get("permission_check"),
            index,
            "permission_check",
            config_name,
        )
        permission_denied_reason = self._validate_optional_extra_string(
            item.get("permission_denied_reason"),
            index,
            config_name,
            "permission_denied_reason",
        )
        if permission and permission_check:
            raise ValueError(
                f"{config_name}[{index}] cannot combine permission with permission_check"
            )

        permission_behavior = item.get("permission_behavior")
        if (permission_behavior is None or permission_behavior == "") and (
            permission or permission_check
        ):
            permission_behavior = "hide"
        else:
            permission_behavior = self._validate_optional_extra_string(
                permission_behavior,
                index,
                config_name,
                "permission_behavior",
            )
        if permission_behavior and permission_behavior not in {"hide", "disable"}:
            raise ValueError(
                f"{config_name}[{index}].permission_behavior must be 'hide' or 'disable'"
            )

        if not permission_keys_present:
            return

        item["permission"] = permission
        item["permission_check"] = permission_check
        item["permission_behavior"] = permission_behavior
        item["permission_denied_reason"] = permission_denied_reason

    def _configure_extra_actions(self) -> None:
        """
        Validate and normalize extra row action definitions.
        """
        extra_actions = getattr(self, "extra_actions", [])
        if extra_actions is None:
            self.extra_actions = []
            return
        if not isinstance(extra_actions, list):
            raise ValueError("extra_actions must be a list of dictionaries")

        normalized_actions: list[dict[str, Any]] = []
        for index, action in enumerate(extra_actions):
            if isinstance(action, PowerAction):
                action = action.to_dict()
            if not isinstance(action, dict):
                raise ValueError(
                    f"extra_actions[{index}] must be a dictionary or PowerAction"
                )

            normalized = action.copy()
            hidden_if = self._resolve_extra_action_method(
                normalized.get("hidden_if"),
                index,
                "hidden_if",
            )
            hidden_if_mode = normalized.get("hidden_if_mode", "eager")
            if hidden_if_mode is None:
                hidden_if_mode = "eager"
            if hidden_if_mode not in {"eager", "lazy"}:
                raise ValueError(
                    "extra_actions[%s].hidden_if_mode must be 'eager' or 'lazy'"
                    % index
                )
            if hidden_if_mode == "lazy" and not hidden_if:
                raise ValueError(
                    "extra_actions[%s].hidden_if_mode='lazy' requires "
                    "hidden_if" % index
                )
            if (
                hidden_if_mode == "lazy"
                and getattr(self, "extra_actions_mode", "buttons") != "dropdown"
            ):
                raise ValueError(
                    "extra_actions[%s].hidden_if_mode='lazy' requires "
                    "extra_actions_mode='dropdown'" % index
                )
            disabled_state = self._resolve_extra_action_method(
                normalized.get("disabled_state"),
                index,
                "disabled_state",
            )
            disabled_state_mode = normalized.get("disabled_state_mode", "eager")
            if disabled_state_mode is None:
                disabled_state_mode = "eager"
            if disabled_state_mode not in {"eager", "lazy"}:
                raise ValueError(
                    "extra_actions[%s].disabled_state_mode must be 'eager' or 'lazy'"
                    % index
                )
            if disabled_state_mode == "lazy" and not disabled_state:
                raise ValueError(
                    "extra_actions[%s].disabled_state_mode='lazy' requires "
                    "disabled_state" % index
                )
            if (
                disabled_state_mode == "lazy"
                and getattr(self, "extra_actions_mode", "buttons") != "dropdown"
            ):
                raise ValueError(
                    "extra_actions[%s].disabled_state_mode='lazy' requires "
                    "extra_actions_mode='dropdown'" % index
                )
            disabled_if = self._resolve_extra_action_method(
                normalized.get("disabled_if"),
                index,
                "disabled_if",
            )
            disabled_reason = self._resolve_extra_action_method(
                normalized.get("disabled_reason"),
                index,
                "disabled_reason",
            )

            if disabled_state and (disabled_if or disabled_reason):
                raise ValueError(
                    "extra_actions[%s] cannot combine disabled_state with "
                    "disabled_if or disabled_reason" % index
                )

            if disabled_reason and not disabled_if:
                log.warning(
                    "extra_actions[%s] defines disabled_reason without disabled_if; "
                    "PowerCRUD will ignore the disabled reason hook",
                    index,
                )
                disabled_reason = None

            normalized["hidden_if"] = hidden_if
            if hidden_if_mode != "eager" or "hidden_if_mode" in normalized:
                normalized["hidden_if_mode"] = hidden_if_mode
            else:
                normalized.pop("hidden_if_mode", None)
            normalized["disabled_state"] = disabled_state
            if (
                disabled_state_mode != "eager"
                or "disabled_state_mode" in normalized
            ):
                normalized["disabled_state_mode"] = disabled_state_mode
            else:
                normalized.pop("disabled_state_mode", None)
            normalized["disabled_if"] = disabled_if
            normalized["disabled_reason"] = disabled_reason
            normalized["refresh_list_on_modal_close"] = (
                self._normalize_extra_modal_close_refresh_flag(
                    normalized,
                    index,
                    "extra_actions",
                )
            )
            self._normalize_permission_affordance_config(
                normalized,
                index,
                "extra_actions",
            )
            normalized_actions.append(normalized)

        self.extra_actions = normalized_actions

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
        config["selection_controls_enabled"] = bool(
            config["bulk_edit_enabled"]
            or (
                use_htmx_enabled
                and not config.get("extra_button_selection_controls_disabled", False)
                and has_selection_aware_extra_buttons(config.get("extra_buttons") or [])
            )
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
        config["modal_classes_resolved"] = config.get("modal_classes") or "modal"
        config["modal_box_classes_resolved"] = (
            config.get("modal_box_classes") or DEFAULT_MODAL_BOX_CLASSES
        )
        config["modal_body_classes_resolved"] = (
            config.get("modal_body_classes") or DEFAULT_MODAL_BODY_CLASSES
        )
        config["bulk_modal_box_classes_resolved"] = (
            config.get("bulk_modal_box_classes")
            or config["modal_box_classes_resolved"]
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
        if name == "extra_button_selection_controls_disabled":
            return bool(self._raw("extra_button_selection_controls_disabled", False))
        if name == "page_size_options":
            return self._raw("page_size_options")
        if name == "page_size_all_enabled":
            return self._raw("page_size_all_enabled", True) is not False
        if name == "selection_controls_enabled":
            return bool(
                self.__getattr__("bulk_edit_enabled")
                or (
                    self.__getattr__("use_htmx_enabled")
                    and not self.__getattr__(
                        "extra_button_selection_controls_disabled"
                    )
                    and has_selection_aware_extra_buttons(
                        self._raw("extra_buttons", []) or []
                    )
                )
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
        if name == "modal_classes_resolved":
            return self._raw("modal_classes") or "modal"
        if name == "modal_box_classes_resolved":
            return self._raw("modal_box_classes") or DEFAULT_MODAL_BOX_CLASSES
        if name == "modal_body_classes_resolved":
            return self._raw("modal_body_classes") or DEFAULT_MODAL_BODY_CLASSES
        if name == "bulk_modal_box_classes_resolved":
            return (
                self._raw("bulk_modal_box_classes")
                or self.__getattr__("modal_box_classes_resolved")
            )
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
        if name == "inline_save_refresh_policy":
            return self._raw("inline_save_refresh_policy") or "reset_if_filtered_out"
        if name == "paginate_by":
            return self._raw("paginate_by", ConfigMixin.paginate_by)
        if name == "view_help_default_color":
            return self._raw("view_help_default_color") or "base"
        if name == "view_help_min_width":
            return self._raw("view_help_min_width") or "40rem"
        if name == "column_sort_fields_override":
            return self._raw("column_sort_fields_override", {}) or {}
        if name == "column_alignments":
            return self._raw("column_alignments", {}) or {}
        if name == "column_value_formats":
            return self._raw("column_value_formats", {}) or {}
        if name == "default_datetime_value_format":
            return self._raw("default_datetime_value_format") or "date"
        if name == "link_fields":
            return self._raw("link_fields", {}) or {}
        if name == "list_cell_link_default_open_in":
            value = self._raw("list_cell_link_default_open_in") or "new"
            if value not in {"current", "new", "modal"}:
                return "new"
            return value
        if name == "list_cell_tooltip_fields":
            value = self._raw("list_cell_tooltip_fields", {}) or {}
            if isinstance(value, dict):
                return dict(value)
            if isinstance(value, list):
                return ConfigMixin._dedupe_preserving_first(value)
            return {}
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
            "default_filterset_fields",
            "default_list_fields",
        }:
            return ConfigMixin._dedupe_preserving_first(self._raw(name, []) or [])
        if name in {
            "column_alignments",
            "column_value_formats",
            "column_sort_fields_override",
            "dropdown_sort_options",
            "field_queryset_dependencies",
            "field_labels",
            "link_fields",
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


def _copy_config_value(value: Any) -> Any:
    """Return a shallow copy for mutable config values."""
    if isinstance(value, list):
        return value.copy()
    if isinstance(value, dict):
        return value.copy()
    if isinstance(value, set):
        return value.copy()
    return value


def _class_declares_powerfields(view_cls: type) -> bool:
    """Return whether a class declares a non-empty PowerField config list."""
    if "power_fields" not in view_cls.__dict__:
        return False
    return bool(view_cls.__dict__.get("power_fields"))


def _declared_field_intent_names(view_cls: type) -> set[str]:
    """Return primitive Field Intent names declared directly on a class."""
    if view_cls is ConfigMixin:
        return set()
    return {
        name
        for name in FIELD_INTENT_CONFIG_FIELDS
        if name in getattr(view_cls, "__dict__", {})
    }


def _validate_field_intent_style(view_cls: type) -> bool:
    """
    Enforce the v1 rule that class hierarchies use one Field Intent style.

    PowerField declarations may inherit from other PowerField declarations, and
    primitive declarations may inherit from primitive declarations. Mixing the
    two styles in one hierarchy is intentionally rejected for v1.
    """
    primitive_declarations: dict[str, set[str]] = {}
    powerfield_classes: list[str] = []

    for cls in view_cls.__mro__:
        if cls is ConfigMixin:
            break
        if cls is object:
            continue

        primitive_names = _declared_field_intent_names(cls)
        if primitive_names:
            primitive_declarations[cls.__name__] = primitive_names
        if _class_declares_powerfields(cls):
            powerfield_classes.append(cls.__name__)

    if powerfield_classes and primitive_declarations:
        primitive_summary = ", ".join(
            f"{class_name}({', '.join(sorted(names))})"
            for class_name, names in primitive_declarations.items()
        )
        powerfield_summary = ", ".join(powerfield_classes)
        raise ImproperlyConfigured(
            "PowerCRUD v1 cannot mix power_fields with primitive Field Intent "
            "config in one class hierarchy. "
            f"PowerField classes: {powerfield_summary}. "
            f"Primitive Field Intent declarations: {primitive_summary}."
        )

    return bool(powerfield_classes)


def _get_config_field_names() -> set[str]:
    """Return all config names captured by class and instance snapshots."""
    return (
        set(PowerCRUDMixinValidator.model_fields.keys())
        | ConfigMixin.EXTRA_CONFIG_FIELDS
        | {"inline_edit_enabled", "power_fields"}
    )


def _resolve_paginate_by_class_default(view_cls: type) -> int | None:
    """
    Return a view-declared pagination default, falling back to PowerCRUD's default.

    Django and Neapolitan expose ``paginate_by = None`` on their base views.
    PowerCRUD should only treat ``None`` as an explicit opt-out when it is
    declared on the PowerCRUD side of the hierarchy before ``ConfigMixin``.
    """
    for cls in view_cls.__mro__:
        if cls is ConfigMixin:
            break
        if "paginate_by" in getattr(cls, "__dict__", {}):
            return cls.__dict__["paginate_by"]

    return ConfigMixin.paginate_by


def resolve_class_config(view_cls):
    """
    Return a shallow class-level configuration snapshot for URL registration.

    Some PowerCRUD URLs are registered before a view instance exists. This helper
    centralizes that class-time read path so primitive config and future compiled
    config can be consumed through the same access point.
    """
    powerfield_config_active = _validate_field_intent_style(view_cls)
    field_names = _get_config_field_names()
    config: dict[str, Any] = {}
    for attr in field_names:
        if attr == "paginate_by":
            config[attr] = _resolve_paginate_by_class_default(view_cls)
            continue
        if hasattr(view_cls, attr):
            value = getattr(view_cls, attr)
            config[attr] = _copy_config_value(value)

    powerfield_declared_primitive_names: set[str] = set()
    if powerfield_config_active:
        try:
            compiled_powerfields = compile_powerfields(config.get("power_fields") or [])
        except ValueError as exc:
            class_name = view_cls.__name__
            raise ImproperlyConfigured(
                f"Invalid power_fields configuration in class '{class_name}': {exc}"
            ) from exc
        config.update(
            {
                name: _copy_config_value(value)
                for name, value in compiled_powerfields.items()
            }
        )
        powerfield_declared_primitive_names = set(compiled_powerfields.keys())

    config["_powerfield_config_active"] = powerfield_config_active
    config["_powerfield_declared_primitive_names"] = (
        powerfield_declared_primitive_names
    )
    return SimpleNamespace(**config)


__all__ = [
    "ConfigMixin",
    "has_lazy_list_cell_tooltip_state",
    "has_lazy_row_action_state",
    "has_selection_aware_extra_buttons",
    "resolve_config",
    "resolve_class_config",
]
