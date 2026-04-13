from __future__ import annotations

import json

from django.core.exceptions import ValidationError
from django.forms.forms import NON_FIELD_ERRORS
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import render
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template

from powercrud.logging import get_logger

log = get_logger(__name__)


class DeleteMixin:
    """Handle single-object delete flows, including graceful delete refusals."""

    DELETE_FILTER_PREFIX = "_powercrud_filter_"

    def process_deletion(self, request, *args, **kwargs):
        """Delete the current object and gracefully redisplay delete refusals."""
        self.request = request
        self.kwargs = kwargs
        self.object = self.get_object()

        try:
            self.object.delete()
        except ValidationError as exc:
            return self._render_delete_validation_error_response(request, exc)

        return HttpResponseRedirect(self.get_success_url())

    def _render_delete_validation_error_response(self, request, error):
        """Render a handled delete-error response for HTMX and normal requests."""
        template_name = self._resolve_delete_template_name()
        delete_errors = self._normalize_delete_validation_error(error)
        filter_params = self._extract_delete_filter_params(request)

        original_get = request.GET
        if filter_params:
            request.GET = filter_params

        try:
            context = self.get_context_data(delete_errors=delete_errors)

            if getattr(request, "htmx", False):
                response = render(
                    request=request,
                    template_name=f"{template_name}#pcrud_content",
                    context=context,
                )
                if self.get_use_modal():
                    modal_id = self.get_modal_id()[1:]
                    response["HX-Trigger"] = json.dumps(
                        {
                            "formError": True,
                            "showModal": modal_id,
                        }
                    )
                    response["HX-Retarget"] = self.get_modal_target()
                return response

            return render(
                request=request,
                template_name=template_name,
                context=context,
            )
        finally:
            request.GET = original_get

    def _resolve_delete_template_name(self) -> str:
        """Return the first available delete template from the standard chain."""
        template_names = self.get_template_names()

        for template_name in template_names:
            try:
                get_template(template_name)
                return template_name
            except TemplateDoesNotExist:
                continue
            except Exception as exc:  # pragma: no cover - defensive logging path
                log.error(
                    "Unexpected error checking delete template %s: %s",
                    template_name,
                    exc,
                )

        return template_names[-1]

    def _extract_delete_filter_params(self, request) -> QueryDict:
        """Rehydrate list filters posted through the delete confirmation form."""
        filter_params = QueryDict("", mutable=True)

        if request.method != "POST":
            return filter_params

        for key, values in request.POST.lists():
            if not key.startswith(self.DELETE_FILTER_PREFIX):
                continue
            actual_key = key[len(self.DELETE_FILTER_PREFIX) :]
            for value in values:
                filter_params.appendlist(actual_key, value)

        return filter_params

    def _normalize_delete_validation_error(self, error: ValidationError) -> list[str]:
        """Flatten delete refusal errors into user-displayable message strings."""
        if hasattr(error, "message_dict"):
            messages: list[str] = []
            for field, field_messages in error.message_dict.items():
                if field == NON_FIELD_ERRORS:
                    messages.extend(str(message) for message in field_messages)
                    continue
                messages.extend(
                    f"{field}: {message}" for message in field_messages
                )
            return messages or [str(error)]

        if hasattr(error, "messages"):
            return [str(message) for message in error.messages]

        return [str(error)]
