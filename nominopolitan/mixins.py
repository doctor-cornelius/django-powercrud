from neapolitan.views import Role
from django.urls import NoReverseMatch, path, reverse
from django.utils.decorators import classonlymethod
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.template.response import TemplateResponse

from django.conf import settings

import logging
log = logging.getLogger("nominopolitan")


class NominopolitanMixin:
    namespace = None
    create_form_class = None
    templates_path = "nominopolitan" # path to overridden set of templates
    base_template_path = "nominopolitan/base.html" # location of template

    use_crispy = None # True = use crispy-forms if installed; False otherwise.

    use_htmx = None
    htmx_crud_target = None # if specified, allows separate htmx target for CRUD (eg modal)
    use_modal = None

    @classonlymethod
    def get_session_prefix(cls):
        return "nominopolitan_list_target_"

    def get_use_htmx(self):
        # return True if it was set to be True, and False otherwise
        return self.use_htmx is True

    def get_use_modal(self):
        return self.use_modal is True

    def get_htmx_target(self):

        # only if using htmx
        if not self.get_use_htmx():
            htmx_target = None

        elif self.htmx_crud_target:
            # return the specified target
            htmx_target = f"#{self.htmx_crud_target}"

        elif self.use_modal:
            htmx_target = "#modalContent"
        else:
            # return whatever htmx target was set for the incoming request
            htmx_target = f"#{self.request.htmx.target}"

        log.debug(f"get_htmx_target - htmx_target: {htmx_target}")

        return htmx_target

    def get_use_crispy(self):
        # check if attribute was set
        use_crispy_set = self.use_crispy is not None
        # check if crispy_forms is installed
        crispy_installed = "crispy_forms" in settings.INSTALLED_APPS

        if use_crispy_set:
            if self.use_crispy is True and not crispy_installed:
                log.warning("use_crispy is set to True, but crispy_forms is not installed. Forcing to False.")
                return False
            return self.use_crispy
        # user did not set attribute. Return True if crispy_forms is installed else False
        return crispy_installed

    @staticmethod
    def get_url(role, view_cls):
        return path(
            role.url_pattern(view_cls),
            view_cls.as_view(role=role),
            name=f"{view_cls.url_base}-{role.url_name_component}",
        )

    @classonlymethod
    def get_urls(cls, roles=None):
        if roles is None:
            roles = iter(Role)
        return [NominopolitanMixin.get_url(role, cls) for role in roles]

    def reverse(self, role, view, object=None):
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
        try:
            return self.reverse(view, object)
        except NoReverseMatch:
            return None

    def get_form_class(self):
        if self.create_form_class and self.role is Role.CREATE:
            return self.create_form_class
        return super().get_form_class()

    def get_prefix(self):
        return f"{self.namespace}:{self.url_base}" if self.namespace else self.url_base

    def safe_reverse(self, viewname, kwargs=None):
        """Attempt to reverse a URL, returning None if it fails."""
        try:
            return reverse(viewname, kwargs=kwargs)
        except NoReverseMatch:
            return None

    def get_template_names(self):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Override the create_view_url to use our namespaced reverse
        view_name = f"{self.get_prefix()}-create"
        context["create_view_url"] = self.safe_reverse(view_name)

        if self.object:
            update_view_name = f"{self.get_prefix()}-update"
            context["update_view_url"] = self.safe_reverse(update_view_name, kwargs={"pk": self.object.pk})

        # to be used in partials to update the header title
        context["header_title"] = f"{self.url_base.title()}-{self.role.value.title()}"

        # set base_template_path
        context["base_template_path"] = self.base_template_path

        # set use_crispy for templates
        context["use_crispy"] = self.get_use_crispy()

        # set use_htmx for templates
        context["use_htmx"] = self.get_use_htmx()

        context['use_modal'] = self.get_use_modal()

        session_key = f"{self.__class__.get_session_prefix()}{self.url_base}"
        context["original_target"] = self.request.session.get(session_key)

        if self.request.htmx:
            context["htmx_target"] = self.get_htmx_target()

        # Add related fields for list view
        if self.role == Role.LIST and hasattr(self, "object_list"):
            context["related_fields"] = {
                field.name: field.related_model._meta.verbose_name
                for field in self.model._meta.fields
                if field.is_relation
            }

        # Add related objects for detail view
        if self.role == Role.DETAIL and hasattr(self, "object"):
            context["related_objects"] = {
                field.name: str(getattr(self.object, field.name))
                for field in self.model._meta.fields
                if field.is_relation and getattr(self.object, field.name)
            }

        return context

    def get_success_url(self):
        # Verify that a model is defined for this view
        # This is required to construct the URL patterns
        assert self.model is not None, (
            "'%s' must define 'model' or override 'get_success_url()'"
            % self.__class__.__name__
        )

        # Construct the list URL name, using namespace if provided
        # Example: "sample:author-list" or just "author-list"
        url_name = (
            f"{self.namespace}:{self.url_base}-list"
            if self.namespace
            else f"{self.url_base}-list"
        )

        # Different behavior based on the role
        if self.role in (Role.DELETE, Role.UPDATE, Role.CREATE):
            # After deletion, go to the list view
            success_url = reverse(url_name)
        else:
            # For create/update, construct detail URL
            # Example: "sample:author-detail" or "author-detail"
            detail_url = (
                f"{self.namespace}:{self.url_base}-detail"
                if self.namespace
                else f"{self.url_base}-detail"
            )
            # Reverse the detail URL with the object's primary key
            success_url = reverse(detail_url, kwargs={"pk": self.object.pk})

        return success_url

    def render_to_response(self, context={}):
        """Handle both HTMX and regular requests"""
        template_names = self.get_template_names()
        template_name = template_names[0] if self.template_name else template_names[1]

        if self.request.htmx:
            # Store original target when first receiving list view
            if self.role == Role.LIST:
                session_key = f"{self.__class__.get_session_prefix()}{self.url_base}"
                context["session_key"] = session_key
                self.request.session[session_key] = f"#{self.request.htmx.target}"
                context["original_target"] = f"#{self.request.htmx.target}"
            return render(
                request=self.request,
                template_name=f"{template_name}#content",
                context=context,
            )
        else:
            return TemplateResponse(
                request=self.request, template=template_name, context=context
            )
