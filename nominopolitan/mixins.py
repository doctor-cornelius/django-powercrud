from neapolitan.views import CRUDView, Role
from django.urls import NoReverseMatch, path, reverse
from django.utils.decorators import classonlymethod
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from django.template.response import TemplateResponse

import logging
log = logging.getLogger(__name__)

class NominopolitanMixin:
    namespace = None
    create_form_class = None

    template_path = "nominopolitan"
    base_template_path = "nominopolitan/base.html"
    use_htmx_partials = True


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
                f"{self.template_path}/object{self.template_name_suffix}.html",
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

        # to be used in partials to update the header title
        context["header_title"] = f"{self.url_base.title()}-{self.role.value.title()}"

        # set base_template_path
        context["base_template_path"] = self.base_template_path

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
        assert self.model is not None, (
            "'%s' must define 'model' or override 'get_success_url()'"
            % self.__class__.__name__
        )

        url_name = (
            f"{self.namespace}:{self.url_base}-list"
            if self.namespace
            else f"{self.url_base}-list"
        )
        if self.role is Role.DELETE:
            success_url = reverse(url_name)
        else:
            detail_url = (
                f"{self.namespace}:{self.url_base}-detail"
                if self.namespace
                else f"{self.url_base}-detail"
            )
            success_url = reverse(detail_url, kwargs={"pk": self.object.pk})

        return success_url

    def render_to_response(self, context={}):
        """Handle both HTMX and regular requests"""
        template_names = self.get_template_names()

        # context["base_template_path"] = self.base_template_path

        if self.template_name:
            # an override template was provided, so use it
            template_name = template_names[0]
        else:
            # revert to using the default template
            template_name = template_names[1]

        if self.request.htmx:
            partial_name = f"{template_name}"
            if self.use_htmx_partials:
                partial_name += "#content"

            return render(
                request=self.request,
                template_name=partial_name,
                context=context,
            )
        else:
            return TemplateResponse(
                request=self.request, template=template_name, context=context
            )

