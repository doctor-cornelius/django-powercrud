from django.urls import path, reverse, NoReverseMatch
from django.utils.decorators import classonlymethod
from django.core.exceptions import ImproperlyConfigured
from neapolitan.views import Role

from .bulk_mixin import BulkEditRole, BulkActions

import logging
log = logging.getLogger("powercrud")

class UrlMixin:
    """
    Provides URL generation and reversing for powercrud views.
    """
    def get_prefix(self):
        """
        Generate a prefix for URL names.

        This method is used in get_context_data to create namespaced URL names.

        Returns:
            str: A prefix string for URL names, including namespace if set.
        """
        return f"{self.namespace}:{self.url_base}" if self.namespace else self.url_base

    def get_template_names(self):
        """
        Determine the appropriate template names for the current view.

        This method is called by Django's template rendering system to find the correct template.
        It overrides the default behavior to include custom template paths.

        Returns:
            list: A list of template names to be used for rendering.

        Raises:
            ImproperlyConfigured: If neither template_name nor model and template_name_suffix are defined.
        """
        if self.template_name is not None:
            return [self.template_name]

        if self.model is not None and self.template_name_suffix is not None:
            names = [
                f"{self.model._meta.app_label}/"
                f"{self.model._meta.object_name.lower()}"
                f"{self.template_name_suffix}.html",
                f"{self.templates_path}/object{self.template_name_suffix}.html",
            ]
            return names
        msg = (
            "'%s' must either define 'template_name' or 'model' and "
            "'template_name_suffix', or override 'get_template_names()'"
        )
        raise ImproperlyConfigured(msg % self.__class__.__name__)


    def safe_reverse(self, viewname, kwargs=None):
        """
        Safely attempt to reverse a URL, returning None if it fails.

        This method is used in get_context_data to generate URLs for various views.

        Args:
            viewname (str): The name of the view to reverse.
            kwargs (dict, optional): Additional keyword arguments for URL reversing.

        Returns:
            str or None: The reversed URL if successful, None otherwise.
        """
        try:
            return reverse(viewname, kwargs=kwargs)
        except NoReverseMatch:
            return None

    def reverse(self, role, view, object=None):
        """
        Override of neapolitan's reverse method.
        
        Generates a URL for a given role, view, and optional object.
        Handles namespaced and non-namespaced URLs.

        Args:
            role (Role): The role for which to generate the URL.
            view (View): The view class for which to generate the URL.
            object (Model, optional): The model instance for detail, update, and delete URLs.

        Returns:
            str: The generated URL.

        Raises:
            ValueError: If object is None for detail, update, and delete URLs.
        """
        url_name = (
            f"{view.namespace}:{view.url_base}-{role.url_name_component}"
            if view.namespace
            else f"{view.url_base}-{role.url_name_component}"
        )
        url_kwarg = view.lookup_url_kwarg or view.lookup_field

        match role:
            case Role.LIST | Role.CREATE:
                return reverse(url_name)
            case _:
                if object is None:
                    raise ValueError("Object required for detail, update, and delete URLs")
                return reverse(
                    url_name,
                    kwargs={url_kwarg: getattr(object, view.lookup_field)},
                )

    def maybe_reverse(self, view, object=None):
        """
        Override of neapolitan's maybe_reverse method.
        
        Attempts to reverse a URL, returning None if it fails.

        Args:
            view (View): The view class for which to generate the URL.
            object (Model, optional): The model instance for detail, update, and delete URLs.

        Returns:
            str or None: The generated URL if successful, None otherwise.
        """
        try:
            return self.reverse(view, object)
        except NoReverseMatch:
            return None

    def get_success_url(self):
        """
        Determine the URL to redirect to after a successful form submission.

        This method constructs the appropriate success URL based on the current role
        (CREATE, UPDATE, DELETE) and the view's configuration. It uses the namespace
        and url_base attributes to generate the correct URL patterns.

        Returns:
            str: The URL to redirect to after a successful form submission.

        Raises:
            AssertionError: If the model is not defined for this view.
        """
        assert self.model is not None, (
            "'%s' must define 'model' or override 'get_success_url()'"
            % self.__class__.__name__
        )

        url_name = (
            f"{self.namespace}:{self.url_base}-list"
            if self.namespace
            else f"{self.url_base}-list"
        )

        if self.role in (Role.DELETE, Role.UPDATE, Role.CREATE):
            success_url = reverse(url_name)
        else:
            detail_url = (
                f"{self.namespace}:{self.url_base}-detail"
                if self.namespace
                else f"{self.url_base}-detail"
            )
            success_url = reverse(detail_url, kwargs={"pk": self.object.pk})

        return success_url

    @staticmethod
    def get_url(role, view_cls):
        """
        Generate a URL pattern for a specific role and view class.

        This method is used internally by the get_urls method to create individual URL patterns.

        Args:
            role (Role): The role for which to generate the URL.
            view_cls (class): The view class for which to generate the URL.

        Returns:
            path: A Django URL pattern for the specified role and view class.
        """
        return path(
            role.url_pattern(view_cls),
            view_cls.as_view(role=role),
            name=f"{view_cls.url_base}-{role.url_name_component}",
        )

    @classonlymethod
    def get_urls(cls, roles=None):
        """
        Generate a list of URL patterns for all roles or specified roles.

        This method is typically called from the urls.py file of a Django app to generate
        URL patterns for all CRUD views associated with a model.

        Args:
            roles (iterable, optional): An iterable of Role objects. If None, all roles are used.

        Returns:
            list: A list of URL patterns for the specified roles.
        """
        if roles is None:
            roles = iter(Role)

        # Standard CRUD URLs
        urls = [cls.get_url(role, cls) for role in roles]

        # Add bulk edit URL if bulk_fields are defined OR bulk_delete is enabled
        if (hasattr(cls, 'bulk_fields') and cls.bulk_fields) or getattr(cls, 'bulk_delete', False):
            bulk_edit_role = BulkEditRole()
            urls.append(bulk_edit_role.get_url(cls))
            
            # Add URLs for bulk actions using the new BulkActions enum
            urls.append(BulkActions.TOGGLE_SELECTION.get_url(cls))
            urls.append(BulkActions.CLEAR_SELECTION.get_url(cls))
            urls.append(BulkActions.TOGGLE_ALL_SELECTION.get_url(cls))

        return urls
    
    def get_context_data(self, **kwargs):
        """
        Prepare and return the context data for template rendering.

        This method extends the base context with additional data specific to the view,
        including URLs for CRUD operations, HTMX-related settings, and related object information.

        Args:
            **kwargs: Additional keyword arguments passed to the method.
                - NB parent class neapolitan.views.get_context_data() expects:
                    - 

        Returns:
            dict: The context dictionary containing all the data for template rendering.
        """
        kwargs = super().get_context_data(**kwargs)

        # Generate and add URLs for create, update, and delete operations

        view_name = f"{self.get_prefix()}-{Role.CREATE.value}"

        kwargs["create_view_url"] = self.safe_reverse(view_name)

        if self.object:
            update_view_name = f"{self.get_prefix()}-{Role.UPDATE.value}"
            kwargs["update_view_url"] = self.safe_reverse(update_view_name, kwargs={"pk": self.object.pk})
            delete_view_name = f"{self.get_prefix()}-{Role.DELETE.value}"
            kwargs["delete_view_url"] = self.safe_reverse(delete_view_name, kwargs={"pk": self.object.pk})

        # send list_view_url
        if self.namespace:
            list_url_name = f"{self.namespace}:{self.url_base}-list"
        else:
            list_url_name = f"{self.url_base}-list"
        kwargs["list_view_url"] = reverse(list_url_name)

        # Set header title for partial updates
        kwargs["header_title"] = f"{self.url_base.title()}-{self.role.value.title()}"

        # Add template and feature configuration
        kwargs["base_template_path"] = self.base_template_path
        kwargs['framework_template_path'] = self.templates_path
        kwargs["use_crispy"] = self.get_use_crispy()
        kwargs["use_htmx"] = self.get_use_htmx()
        kwargs['use_modal'] = self.get_use_modal()
        kwargs["original_target"] = self.get_original_target()

        # bulk edit context vars
        kwargs['enable_bulk_edit'] = self.get_bulk_edit_enabled()
        kwargs['enable_bulk_delete'] = self.get_bulk_delete_enabled()
        kwargs['storage_key'] = self.get_storage_key()

        # Set table styling parameters
        kwargs['table_pixel_height_other_page_elements'] = self.get_table_pixel_height_other_page_elements()
        kwargs['get_table_max_height'] = self.get_table_max_height()
        kwargs['table_max_col_width'] = f"{self.get_table_max_col_width()}"
        kwargs['table_header_min_wrap_width'] = f"{self.get_table_header_min_wrap_width()}"
        kwargs['table_classes'] = self.get_table_classes()

        # Add HTMX-specific context if enabled
        if self.get_use_htmx():
            kwargs["htmx_target"] = self.get_htmx_target()

        # Add related fields information for list view
        if self.role == Role.LIST and hasattr(self, "object_list"):
            kwargs["related_fields"] = {
                field.name: field.related_model._meta.verbose_name
                for field in self.model._meta.fields
                if field.is_relation
            }

        # Add related objects information for detail view
        if self.role == Role.DETAIL and hasattr(self, "object"):
            kwargs["related_objects"] = {
                field.name: str(getattr(self.object, field.name))
                for field in self.model._meta.fields
                if field.is_relation and getattr(self.object, field.name)
            }

        # Add sort parameter to context
        kwargs['sort'] = self.request.GET.get('sort', '')

        # pagination variables
        kwargs['page_size_options'] = self.get_page_size_options()
        kwargs['default_page_size'] = str(self.paginate_by) if self.paginate_by is not None else None

        # If we have a form with errors and modals are enabled,
        # ensure the htmx_target is set to the modal target
        if hasattr(self, 'object_form') and hasattr(self.object_form, 'errors') and self.object_form.errors and self.get_use_modal():
            kwargs['htmx_target'] = self.get_modal_target()

        # if bulk ops enabled then pass selected_ids
        request = kwargs.get('request')
        if request and self.get_bulk_edit_enabled():
            selected_ids = self.get_selected_ids_from_session(request)
            kwargs["selected_ids"] = selected_ids
            kwargs["selected_count"] = len(selected_ids)

        return kwargs