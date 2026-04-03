import json
from typing import Any

from django import forms
from django.forms import models as form_models
from django.db import models as db_models
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import render
from django.urls import reverse

from urllib.parse import urlencode

try:  # Optional dependency: crispy-forms
    from crispy_forms.helper import FormHelper
except ImportError:  # pragma: no cover - environments without crispy_forms
    FormHelper = None  # type: ignore[assignment]
from neapolitan.views import Role
from powercrud.logging import get_logger
from .config_mixin import ConfigMixin, resolve_config

log = get_logger(__name__)


class FormMixin:
    """
    Provides form handling and Crispy Forms integration for powercrud views.
    """

    FIELD_QUERYSET_DEPENDENCY_EMPTY_BEHAVIORS = {"none", "all"}

    def persist_single_object(
        self,
        *,
        form: forms.BaseModelForm,
        mode: str,
        instance: Any | None = None,
    ):
        """Persist one validated form-backed object and return the saved instance.

        Args:
            form: Validated Django form driving the persistence operation.
            mode: Persistence surface using the hook, currently ``"form"`` or
                ``"inline"``.
            instance: Optional object reference from the calling code. Downstream
                overrides may use this to compare the original object with the
                saved result.

        Returns:
            Model instance returned by the default ``form.save()`` behavior.

        Important:
            If an override bypasses ``form.save()`` directly, that override owns
            any required ``form.save_m2m()`` handling.
        """
        return form.save()

    def get_form_disabled_fields(self) -> list[str]:
        """
        Return the configured list of form fields that should be disabled.
        """
        return list(resolve_config(self).form_disabled_fields or [])

    def get_form_display_fields(self) -> list[str]:
        """
        Return the configured list of display-only model fields shown above forms.
        """
        return list(resolve_config(self).form_display_fields or [])

    def get_use_crispy(self):
        """
        Determine if crispy forms should be used.

        This method is called in get_context_data() to set the 'use_crispy' context
        variable for templates. It checks if the crispy_forms app is installed and
        if the use_crispy attribute is explicitly set.

        Returns:
            bool: True if crispy forms should be used, False otherwise

        Note:
            - If use_crispy is explicitly set to True but crispy_forms is not installed,
              it logs a warning and returns False.
            - If use_crispy is not set, it returns True if crispy_forms is installed,
              False otherwise.
        """
        return bool(resolve_config(self).use_crispy_enabled)

    def get_searchable_selects(self) -> bool:
        """
        Determine whether searchable-select enhancement is enabled for this view.

        Returns:
            bool: True when selectable single-value dropdowns should be enhanced.
        """
        return bool(resolve_config(self).searchable_selects_enabled)

    def get_searchable_select_enabled_for_field(
        self, field_name: str, bound_field: forms.Field | None = None
    ) -> bool:
        """
        Hook for per-field searchable-select opt-out.

        Args:
            field_name: Form field name being considered.
            bound_field: Concrete Django form field instance, when available.

        Returns:
            bool: True to enhance the field, False to keep a native select.
        """
        return True

    def _is_boolean_like_select_field(self, field: forms.Field) -> bool:
        """
        Return True when a select field represents a boolean choice set.
        """
        if isinstance(field, forms.BooleanField):
            return True

        choices = [choice for choice in getattr(field, "choices", []) if choice]
        normalized_values = {
            str(value).strip().lower()
            for value, _label in choices
            if str(value).strip() != ""
        }
        if not normalized_values:
            return False
        boolean_values = {"true", "false", "1", "0"}
        return normalized_values.issubset(boolean_values)

    def _is_searchable_select_candidate(
        self, field_name: str, field: forms.Field
    ) -> bool:
        """
        Check whether a form field should be marked for searchable-select enhancement.
        """
        widget = getattr(field, "widget", None)
        if widget is None:
            return False
        if not isinstance(widget, forms.Select):
            return False
        if getattr(widget, "allow_multiple_selected", False):
            return False
        if self._is_boolean_like_select_field(field):
            return False
        return bool(
            self.get_searchable_select_enabled_for_field(
                field_name=field_name, bound_field=field
            )
        )

    def _apply_searchable_select_attrs(self, form: forms.BaseForm) -> forms.BaseForm:
        """
        Tag eligible select fields for frontend searchable-select enhancement.
        """
        if not form:
            return form
        if not self.get_searchable_selects():
            return form

        for field_name, field in form.fields.items():
            attrs = field.widget.attrs
            if self._is_searchable_select_candidate(field_name, field):
                attrs["data-powercrud-searchable-select"] = "true"
            else:
                attrs.pop("data-powercrud-searchable-select", None)
        return form

    def _apply_disabled_form_fields(self, form: forms.BaseForm) -> forms.BaseForm:
        """
        Disable configured form fields using Django's native field disabling.

        Using ``field.disabled = True`` ensures submitted tampering is ignored and
        the persisted instance value is preserved on validation and save.

        PowerCRUD applies this only to update forms. Disabling fields on create
        forms can make required inputs impossible to populate and is not the
        intended use of the feature.
        """
        if not form:
            return form

        instance = getattr(form, "instance", None)
        if instance is None or getattr(instance, "pk", None) is None:
            return form

        disabled_fields = self.get_form_disabled_fields()
        if not disabled_fields:
            return form

        missing_fields = sorted(
            field_name for field_name in disabled_fields if field_name not in form.fields
        )
        if missing_fields:
            raise ImproperlyConfigured(
                f"Invalid configuration in class '{self.__class__.__name__}': "
                "form_disabled_fields must reference fields present on the built form. "
                f"Missing: {', '.join(missing_fields)}"
            )

        for field_name in disabled_fields:
            form.fields[field_name].disabled = True

        return form

    def _format_form_display_value(
        self, instance: Any, field: db_models.Field, field_name: str
    ) -> str:
        """
        Format a display-only model field value for the object form context block.
        """
        value = getattr(instance, field_name, None)

        if field.many_to_many:
            related_manager = value
            if related_manager is None:
                return ""
            return ", ".join(str(item) for item in related_manager.all())

        if field.is_relation:
            return "" if value is None else str(value)

        if isinstance(field, db_models.BooleanField):
            return "Yes" if value else "No"

        if isinstance(field, db_models.DateTimeField) and value is not None:
            normalized_value = field.to_python(value)
            return normalized_value.strftime("%d/%m/%Y")

        if isinstance(field, db_models.DateField) and value is not None:
            normalized_value = field.to_python(value)
            return normalized_value.strftime("%d/%m/%Y")

        if isinstance(field, db_models.TimeField) and value is not None:
            normalized_value = field.to_python(value)
            return normalized_value.strftime("%H:%M:%S")

        return "" if value in (None, "") else str(value)

    def get_form_display_items(self, instance: Any | None = None) -> list[dict[str, str]]:
        """
        Build the display-only model field metadata shown above update forms.

        The v1 API is intentionally narrow:
        - model fields only
        - update forms only
        - plain text label/value pairs
        """
        display_fields = self.get_form_display_fields()
        resolved_instance = instance or getattr(self, "object", None)

        if (
            not display_fields
            or resolved_instance is None
            or not getattr(resolved_instance, "pk", None)
        ):
            return []

        items: list[dict[str, str]] = []
        for field_name in display_fields:
            field = self.model._meta.get_field(field_name)
            items.append(
                {
                    "name": field_name,
                    "label": str(field.verbose_name).title(),
                    "value": self._format_form_display_value(
                        resolved_instance,
                        field,
                        field_name,
                    ),
                }
            )
        return items

    def get_field_queryset_dependencies(
        self,
        *,
        available_fields: set[str] | None = None,
        warn_on_unavailable: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """
        Resolve declarative field queryset dependency configuration.

        Args:
            available_fields: Optional field-name set used to filter dependencies to
                the current form surface.
            warn_on_unavailable: When True, log warnings for fields or parents that
                are not present in `available_fields`.

        Returns:
            dict[str, dict[str, Any]]: Normalised dependency metadata keyed by the
            dependent child field name.
        """
        cfg = resolve_config(self)
        dependencies = cfg.field_queryset_dependencies or {}
        resolved: dict[str, dict[str, Any]] = {}

        for field_name, meta in dependencies.items():
            if not isinstance(meta, dict):
                continue

            if available_fields is not None and field_name not in available_fields:
                if warn_on_unavailable:
                    log.warning(
                        "Field queryset dependency for '%s' ignored because the field is not present on %s",
                        field_name,
                        self.__class__.__name__,
                    )
                continue

            depends_on = meta.get("depends_on") or []
            if not isinstance(depends_on, list):
                log.warning(
                    "Field queryset dependency for '%s' ignored because depends_on is not a list on %s",
                    field_name,
                    self.__class__.__name__,
                )
                continue

            valid_depends_on: list[str] = []
            unavailable_parents: set[str] = set()
            for parent in depends_on:
                if not isinstance(parent, str):
                    unavailable_parents.add(str(parent))
                    continue
                if available_fields is not None and parent not in available_fields:
                    unavailable_parents.add(parent)
                    continue
                valid_depends_on.append(parent)
            valid_depends_on = ConfigMixin._dedupe_preserving_first(valid_depends_on)

            if unavailable_parents and warn_on_unavailable:
                log.warning(
                    "Field queryset dependency for '%s' references unavailable parent fields %s on %s",
                    field_name,
                    sorted(unavailable_parents),
                    self.__class__.__name__,
                )

            filter_by = meta.get("filter_by") or {}
            if not isinstance(filter_by, dict):
                log.warning(
                    "Field queryset dependency for '%s' ignored because filter_by is not a dictionary on %s",
                    field_name,
                    self.__class__.__name__,
                )
                continue

            valid_filter_by: dict[str, str] = {}
            invalid_filter_parents: set[str] = set()
            for child_lookup, parent_field in filter_by.items():
                if not isinstance(child_lookup, str) or not isinstance(parent_field, str):
                    continue
                if parent_field not in valid_depends_on:
                    invalid_filter_parents.add(parent_field)
                    continue
                valid_filter_by[child_lookup] = parent_field

            if invalid_filter_parents and warn_on_unavailable:
                log.warning(
                    "Field queryset dependency for '%s' ignored invalid filter_by parents %s on %s",
                    field_name,
                    sorted(invalid_filter_parents),
                    self.__class__.__name__,
                )

            static_filters = meta.get("static_filters") or {}
            if not isinstance(static_filters, dict):
                log.warning(
                    "Field queryset dependency for '%s' ignored non-dictionary static_filters on %s",
                    field_name,
                    self.__class__.__name__,
                )
                static_filters = {}

            has_dynamic_filters = bool(valid_depends_on and valid_filter_by)
            if not has_dynamic_filters and not static_filters:
                continue

            empty_behavior = meta.get("empty_behavior") or "none"
            if empty_behavior not in self.FIELD_QUERYSET_DEPENDENCY_EMPTY_BEHAVIORS:
                log.warning(
                    "Field queryset dependency for '%s' on %s uses invalid empty_behavior '%s'; defaulting to 'none'",
                    field_name,
                    self.__class__.__name__,
                    empty_behavior,
                )
                empty_behavior = "none"

            order_by = meta.get("order_by")
            if order_by is not None and not isinstance(order_by, str):
                log.warning(
                    "Field queryset dependency for '%s' ignored non-string order_by on %s",
                    field_name,
                    self.__class__.__name__,
                )
                order_by = None

            resolved[field_name] = {
                "depends_on": valid_depends_on if has_dynamic_filters else [],
                "filter_by": valid_filter_by if has_dynamic_filters else {},
                "static_filters": static_filters,
                "empty_behavior": empty_behavior,
                "order_by": order_by,
            }

        return resolved

    def _dependency_value_is_empty(self, value: Any) -> bool:
        """
        Determine whether a resolved dependency value should be treated as empty.
        """
        if value is None:
            return True
        if isinstance(value, str):
            return value == ""
        if isinstance(value, (list, tuple, set)):
            return not any(item not in ("", None) for item in value)
        return False

    def _resolve_dependency_form_value(self, form: forms.BaseForm, field_name: str) -> Any:
        """
        Resolve a parent field value from the current form state.

        Bound values take precedence, followed by the current instance and then any
        initial values. This mirrors normal Django form behaviour closely enough for
        simple declarative dependency scoping.
        """
        if field_name in getattr(form, "fields", {}):
            try:
                value = form[field_name].value()
            except Exception:
                value = None
            if not self._dependency_value_is_empty(value):
                return value

        instance = getattr(form, "instance", None)
        if instance is not None:
            instance_fk_attr = f"{field_name}_id"
            if hasattr(instance, instance_fk_attr):
                value = getattr(instance, instance_fk_attr, None)
                if not self._dependency_value_is_empty(value):
                    return value
            if hasattr(instance, field_name):
                attr = getattr(instance, field_name)
                if hasattr(attr, "all"):
                    values = list(attr.values_list("pk", flat=True))
                    if values:
                        return values
                if hasattr(attr, "pk"):
                    value = getattr(attr, "pk", None)
                    if not self._dependency_value_is_empty(value):
                        return value
                if not self._dependency_value_is_empty(attr):
                    return attr

        initial = getattr(form, "initial", {})
        if isinstance(initial, dict):
            value = initial.get(field_name)
            if not self._dependency_value_is_empty(value):
                return value

        return None

    def _apply_field_queryset_dependencies(
        self, form: forms.BaseForm
    ) -> forms.BaseForm:
        """
        Scope child relation field querysets using declarative dependency config.
        """
        if not form:
            return form

        dependencies = self.get_field_queryset_dependencies(
            available_fields=set(form.fields.keys())
        )

        for field_name, meta in dependencies.items():
            field = form.fields.get(field_name)
            queryset = getattr(field, "queryset", None)
            if field is None or queryset is None:
                log.warning(
                    "Field queryset dependency for '%s' ignored because the form field is not queryset-backed on %s",
                    field_name,
                    self.__class__.__name__,
                )
                continue

            static_filters = meta.get("static_filters") or {}
            if static_filters:
                queryset = queryset.filter(**static_filters)

            child_filters: dict[str, Any] = {}
            dependency_unresolved = False
            unsupported_multi_value = False

            for child_lookup, parent_field in meta["filter_by"].items():
                parent_value = self._resolve_dependency_form_value(form, parent_field)

                if isinstance(parent_value, (list, tuple, set)):
                    cleaned_values = [
                        value for value in parent_value if value not in ("", None)
                    ]
                    if len(cleaned_values) > 1 and not child_lookup.endswith("__in"):
                        unsupported_multi_value = True
                        log.warning(
                            "Field queryset dependency for '%s' on %s resolved multiple values for parent '%s', which requires an '__in' filter",
                            field_name,
                            self.__class__.__name__,
                            parent_field,
                        )
                        break
                    if not cleaned_values:
                        dependency_unresolved = True
                        break
                    parent_value = (
                        cleaned_values
                        if child_lookup.endswith("__in")
                        else cleaned_values[0]
                    )

                if self._dependency_value_is_empty(parent_value):
                    dependency_unresolved = True
                    break

                child_filters[child_lookup] = parent_value

            if unsupported_multi_value:
                field.queryset = (
                    queryset.none() if meta["empty_behavior"] == "none" else queryset
                )
                continue

            if dependency_unresolved:
                if meta["empty_behavior"] == "none":
                    queryset = queryset.none()
            elif child_filters:
                queryset = queryset.filter(**child_filters)

            if meta.get("order_by"):
                queryset = queryset.order_by(meta["order_by"])

            field.queryset = queryset

        return form

    def _finalize_form(
        self, form: forms.BaseForm, *, inline: bool = False
    ) -> forms.BaseForm:
        """
        Apply PowerCRUD form instance behavior after construction.
        """
        if not inline:
            form = self._apply_disabled_form_fields(form)
        form = self._apply_field_queryset_dependencies(form)
        return self._apply_searchable_select_attrs(form)

    def get_context_data(self, **kwargs):
        """
        Add form display-only metadata to the standard template context.
        """
        context = super().get_context_data(**kwargs)
        form = kwargs.get("form") or context.get("form") or getattr(self, "object_form", None)
        instance = getattr(form, "instance", None) if form is not None else None
        context["form_display_items"] = self.get_form_display_items(instance=instance)
        return context

    def get_form(self, *args, **kwargs):
        """
        Build the view form and apply searchable-select widget markers.
        """
        form = super().get_form(*args, **kwargs)
        return self._finalize_form(form)

    def _apply_crispy_helper(self, form_class):
        """Helper method to apply crispy form settings to a form class."""
        if not self.get_use_crispy():
            # Apply dropdown sorting even if not using crispy
            self._apply_dropdown_sorting(form_class)
            return form_class

        # Create a new instance to check if it has a helper
        _temp_form = form_class()
        has_helper = hasattr(_temp_form, "helper")

        if not has_helper:
            old_init = form_class.__init__

            def new_init(self, *args, **kwargs):
                old_init(self, *args, **kwargs)
                self.helper = FormHelper()
                self.helper.form_tag = False
                self.helper.disable_csrf = True

            form_class.__init__ = new_init
        else:
            old_init = form_class.__init__

            def new_init(self, *args, **kwargs):
                old_init(self, *args, **kwargs)

                # Check if form_tag has been explicitly set to True
                if self.helper.form_tag is True:
                    self.helper.form_tag = False

                # Check if disable_csrf has been explicitly set to False
                if self.helper.disable_csrf is False:
                    self.helper.disable_csrf = True

            form_class.__init__ = new_init

        # Apply dropdown sorting
        self._apply_dropdown_sorting(form_class)

        return form_class

    def _apply_dropdown_sorting(self, form_class):
        """Apply dropdown sorting to form fields."""
        sort_options = resolve_config(self).dropdown_sort_options
        for field_name, sort_field in sort_options.items():
            if field_name in form_class.base_fields:
                form_field = form_class.base_fields[field_name]
                if hasattr(form_field, "queryset") and form_field.queryset is not None:
                    # sort_field can be "name" or "-name" - Django's order_by handles both
                    form_field.queryset = form_field.queryset.order_by(sort_field)

    def get_form_class(self):
        """Override get_form_class to use form_fields for form generation."""

        # Use explicitly defined form class if provided
        cfg = resolve_config(self)
        if cfg.form_class is not None:
            return self._apply_crispy_helper(cfg.form_class)

        # Generate a default form class using form_fields
        if self.model is not None and cfg.form_fields:
            # Configure HTML5 input widgets for date/time fields
            widgets = {}
            for field in self.model._meta.get_fields():
                if field.name not in cfg.form_fields:
                    continue
                if isinstance(field, db_models.DateField):
                    widgets[field.name] = forms.DateInput(
                        attrs={"type": "date", "class": "form-control"}
                    )
                elif isinstance(field, db_models.DateTimeField):
                    widgets[field.name] = forms.DateTimeInput(
                        attrs={"type": "datetime-local", "class": "form-control"}
                    )
                elif isinstance(field, db_models.TimeField):
                    widgets[field.name] = forms.TimeInput(
                        attrs={"type": "time", "class": "form-control"}
                    )

            # Create the form class with our configured widgets
            form_class = form_models.modelform_factory(
                self.model, fields=cfg.form_fields, widgets=widgets
            )

            # Apply dropdown sorting to form fields
            sort_options = cfg.dropdown_sort_options
            for field_name, sort_field in sort_options.items():
                if field_name in cfg.form_fields:
                    model_field = self.model._meta.get_field(field_name)
                    if (
                        hasattr(model_field, "related_model")
                        and model_field.related_model
                    ):
                        form_field = form_class.base_fields[field_name]
                        form_field.queryset = (
                            model_field.related_model.objects.order_by(sort_field)
                        )

            # Apply crispy forms if enabled
            if self.get_use_crispy():
                old_init = form_class.__init__

                def new_init(self, *args, **kwargs):
                    old_init(self, *args, **kwargs)
                    self.helper = FormHelper()
                    self.helper.form_tag = False
                    self.helper.disable_csrf = True

                form_class.__init__ = new_init

            return form_class

        msg = (
            "'%s' must either define 'form_class' or both 'model' and "
            "'form_fields', or override 'get_form_class()'"
        )
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_inline_form_kwargs(self, *, instance, data=None, files=None):
        """
        Build kwargs for an inline form instance so inline endpoints can reuse the
        standard form pipeline without duplicating logic.
        """
        kwargs = {"instance": instance}
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files
        return kwargs

    def build_inline_form(self, *, instance, data=None, files=None):
        """
        Construct a ModelForm for inline editing using the same configuration as
        regular edit forms.
        """
        form_class = self.get_form_class()
        form_kwargs = self.get_inline_form_kwargs(
            instance=instance, data=data, files=files
        )
        form = form_class(**form_kwargs)
        return self._finalize_form(form, inline=True)

    def show_form(self, request, *args, **kwargs):
        """Override to check for conflicts before showing edit form"""
        # Only check conflicts for UPDATE operations (not CREATE)
        pk = None
        current_object = None
        if self.role == Role.UPDATE:
            try:
                current_object = self.get_object()
                pk = current_object.pk
            except Exception:
                pk = None

        if (
            self.role == Role.UPDATE
            and self.get_conflict_checking_enabled()
            and pk is not None
            and self._check_for_conflicts(selected_ids=[pk])
        ):
            if current_object is None:
                current_object = self.get_object()
            self.object = current_object

            # Get filter params (like sort selection does)
            filter_params = request.GET.copy()
            if "sort" in filter_params:
                filter_params.pop("sort")
            if "page" in filter_params:
                filter_params.pop("page")

            # Return conflict response
            context = self.get_context_data(
                conflict_detected=True,
                conflict_message=(
                    f"Cannot update - bulk operation in progress on "
                    f"{self.model._meta.verbose_name_plural}. Please try again later."
                ),
                filter_params=filter_params.urlencode() if filter_params else "",
            )
            return self.render_to_response(context)

        # No conflict, proceed normally
        return super().show_form(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Handle form validation success with HTMX support.

        This method saves the form and then handles the response differently based on
        whether it's an HTMX request or not:

        For HTMX requests:
        1. Temporarily changes the role to LIST to access list view functionality
        2. Sets the template to the filtered_results partial from object_list.html
        3. Uses the existing list() method to handle pagination and filtering
        4. Adds HTMX headers to:
        - Close the modal (via formSuccess trigger)
        - Target the filtered_results div (via HX-Retarget)

        For non-HTMX requests:
        - Redirects to the success URL (typically the list view)

        This approach ensures consistent behavior with the standard list view,
        including proper pagination and filtering, while avoiding code duplication.

        Args:
            form: The validated form instance

        Returns:
            HttpResponse: Either a rendered list view or a redirect
        """
        if self.role == Role.UPDATE and self.get_conflict_checking_enabled():
            pk = getattr(form.instance, "pk", None) or self.kwargs.get(
                getattr(self, "pk_url_kwarg", "pk")
            )
            if pk and self._check_for_conflicts(selected_ids=[pk]):
                self.object = form.instance
                return self._render_conflict_response(self.request, pk, "update")

        self.object = self.persist_single_object(
            form=form,
            mode="form",
            instance=getattr(form, "instance", None),
        )

        # If this is an HTMX request, handle it specially
        if hasattr(self, "request") and getattr(self.request, "htmx", False):
            # unpack hidden filter parameters
            filter_params = QueryDict("", mutable=True)
            # prefix is set in object_form.html
            filter_prefix = "_powercrud_filter_"

            for k, v in self.request.POST.lists():
                if k.startswith(filter_prefix):
                    real_key = k[len(filter_prefix) :]
                    for value in v:
                        filter_params.appendlist(real_key, value)

            # Build canonical list URL with current filter/sort params
            clean_params = {}
            for k, v in filter_params.lists():
                # filter out keys with no values
                if v:
                    clean_params[k] = v[-1]

            # determine the canonical url that includes the filter parameters
            if self.namespace:
                list_url_name = f"{self.namespace}:{self.url_base}-list"
            else:
                list_url_name = f"{self.url_base}-list"
            list_path = reverse(list_url_name)

            if clean_params:
                canonical_query = urlencode(clean_params)
                canonical_url = f"{list_path}?{canonical_query}"
            else:
                canonical_url = list_path

            # Patch self.request.GET
            original_get = self.request.GET
            self.request.GET = filter_params
            # Temporarily change the role to LIST
            self.role = Role.LIST
            # Use the list method to handle pagination and filtering
            response = self.list(self.request)
            # Restore original GET
            self.request.GET = original_get

            response["HX-Trigger"] = json.dumps({"formSuccess": True})
            response["HX-Retarget"] = f"{self.get_original_target()}"
            response["HX-Push-Url"] = canonical_url
            return response
        # For non-HTMX requests, use the default redirect
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        """
        Handle form validation errors, ensuring proper display in modals.

        This method handles form validation errors differently based on whether
        it's an HTMX request with modals enabled:

        For HTMX requests with modals:
        1. Stores the form with errors
        2. Sets a flag to indicate the modal should stay open
        3. Ensures the correct form template is used (not object_list)
        4. Adds HTMX headers to:
        - Keep the modal open (via formError and showModal triggers)
        - Target the modal content (via HX-Retarget)

        For other requests:
        - Uses the default form_invalid behavior

        Args:
            form: The form with validation errors

        Returns:
            HttpResponse: The rendered form with error messages
        """
        # Store the form with errors
        self.object_form = form

        # If using modals, set a flag to indicate we need to show the modal again
        if self.get_use_modal():
            self.form_has_errors = True

        # For HTMX requests with modals, ensure we use the form template
        if (
            hasattr(self, "request")
            and getattr(self.request, "htmx", False)
            and self.get_use_modal()
        ):
            # Set template to the form partial
            if self.object:  # Update form
                self.template_name = (
                    f"{self.templates_path}/object_form.html#pcrud_content"
                )
            else:  # Create form
                self.template_name = (
                    f"{self.templates_path}/object_form.html#pcrud_content"
                )

            # Render the response with the form template
            context = self.get_context_data(form=form)
            response = render(
                request=self.request,
                template_name=self.template_name,
                context=context,
            )

            # Add HTMX headers to keep the modal open
            modal_id = self.get_modal_id()[1:]  # Remove the # prefix
            response["HX-Trigger"] = json.dumps(
                {"formError": True, "showModal": modal_id}
            )
            response["HX-Retarget"] = self.get_modal_target()

            return response

        # For non-HTMX requests or without modals, use the default behavior
        return super().form_invalid(form)
