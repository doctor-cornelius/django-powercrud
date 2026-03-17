import json
from typing import List, Any

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from powercrud.conf import get_powercrud_setting
from powercrud.logging import get_logger

log = get_logger(__name__)


class SelectionMixin:
    """Mixin for managing bulk selection state, providing session-based persistence and HTMX handlers."""

    def get_bulk_max_selected_records(self) -> int:
        """
        Return the maximum number of records PowerCRUD should allow in a bulk selection.
        """
        value = get_powercrud_setting("BULK_MAX_SELECTED_RECORDS", 1000)
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 1000

    def get_storage_key(self) -> str:
        """
        Return the storage key for the bulk selection.

        Returns:
            str: The unique key used to store selection data in the session.
        """
        return f"powercrud_bulk_{self.model.__name__.lower()}_{self.get_bulk_selection_key_suffix()}"

    def get_bulk_selection_key_suffix(self) -> str:
        """
        Return a suffix to be appended to the bulk selection storage key.

        Override this method to add custom constraints to selection persistence.

        Returns:
            str: A string to append to the selection storage key.
        """
        return ""

    def get_selected_ids_from_session(self, request: HttpRequest) -> List[str]:
        """
        Get selected IDs for the current model from the Django session.

        Args:
            request: The HTTP request object.

        Returns:
            List[str]: A list of selected object IDs.
        """
        session_key = self.get_storage_key()
        selected_ids = request.session.get("powercrud_selections", {}).get(
            session_key, []
        )
        return selected_ids

    def save_selected_ids_to_session(
        self, request: HttpRequest, ids: List[Any]
    ) -> None:
        """
        Save selected IDs for the current model to the Django session.

        Args:
            request: The HTTP request object.
            ids: A list of object IDs to save.
        """
        session_key = self.get_storage_key()
        if "powercrud_selections" not in request.session:
            request.session["powercrud_selections"] = {}
        request.session["powercrud_selections"][session_key] = list(map(str, ids))
        request.session.modified = True

    def toggle_selection_in_session(
        self, request: HttpRequest, obj_id: Any
    ) -> List[str]:
        """
        Toggle an individual object's selection state in the Django session.

        Args:
            request: The HTTP request object.
            obj_id: The ID of the object to toggle.

        Returns:
            List[str]: The updated list of selected object IDs.
        """
        selected_ids = self.get_selected_ids_from_session(request)
        obj_id_str = str(obj_id)
        if obj_id_str in selected_ids:
            selected_ids.remove(obj_id_str)
        else:
            selected_ids.append(obj_id_str)
        self.save_selected_ids_to_session(request, selected_ids)
        return selected_ids

    def toggle_selection_view(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Toggle an individual object's selection state via an HTMX request.

        Args:
            request: The HTTP request object.
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments, including the object ID.

        Returns:
            HttpResponse: Renders the bulk selection status partial.
        """
        if not (hasattr(request, "htmx") and request.htmx):
            return HttpResponseBadRequest(
                "Only HTMX requests are supported for this operation."
            )

        object_id = kwargs.get(self.lookup_url_kwarg)
        if not object_id:
            return HttpResponseBadRequest("Object ID not provided.")

        selected_ids = self.toggle_selection_in_session(request, object_id)
        current_count = len(selected_ids)

        context = {"selected_ids": selected_ids, "selected_count": current_count}
        response = render(
            request,
            f"{self.templates_path}/object_list.html#bulk_selection_status",
            context,
        )
        response["HX-Trigger"] = json.dumps({"refreshTable": True})
        return response

    def clear_selection_from_session(self, request: HttpRequest) -> None:
        """
        Clear all selections for the current model from the Django session.

        Args:
            request: The HTTP request object.
        """
        session_key = self.get_storage_key()
        if "powercrud_selections" in request.session:
            if session_key in request.session["powercrud_selections"]:
                del request.session["powercrud_selections"][session_key]
                request.session.modified = True

    def clear_selection_view(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Clear all selected items for the current model via an HTMX request.

        Args:
            request: The HTTP request object.
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            HttpResponse: Renders the bulk selection status partial with an empty state.
        """
        if not (hasattr(request, "htmx") and request.htmx):
            return HttpResponseBadRequest(
                "Only HTMX requests are supported for this operation."
            )

        self.clear_selection_from_session(request)

        # Return ONLY bulk actions container with empty state
        context = {"selected_ids": [], "selected_count": 0}
        response = render(
            request,
            f"{self.templates_path}/object_list.html#bulk_selection_status",
            context,
        )
        response["HX-Trigger"] = json.dumps({"refreshTable": True})
        return response

    def toggle_all_selection_in_session(
        self,
        request: HttpRequest,
        object_ids: List[Any],
        action: str | None = None,
    ) -> List[str]:
        """
        Update the selection state of all provided object IDs in the Django session.

        If an explicit action is supplied, add or remove the provided IDs.
        Otherwise, preserve the legacy toggle-all behaviour used by the page-level
        select-all checkbox.

        Args:
            request: The HTTP request object.
            object_ids: A list of object IDs to toggle.
            action: Optional explicit action (`"add"` or `"remove"`).

        Returns:
            List[str]: The updated list of selected object IDs.
        """
        current_selected_ids = set(self.get_selected_ids_from_session(request))
        object_ids_set = set(map(str, object_ids))

        if action == "add":
            new_selected_ids = current_selected_ids.union(object_ids_set)
        elif action == "remove":
            new_selected_ids = current_selected_ids - object_ids_set
        else:
            # Check if all current page objects are already selected
            all_on_page_selected = object_ids_set.issubset(current_selected_ids)

            if all_on_page_selected:
                # Deselect all objects on the current page
                new_selected_ids = current_selected_ids - object_ids_set
            else:
                # Select all objects on the current page
                new_selected_ids = current_selected_ids.union(object_ids_set)

        self.save_selected_ids_to_session(request, list(new_selected_ids))
        return list(new_selected_ids)

    def toggle_all_selection_view(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Toggle the selection state of all items on the current page via an HTMX request.

        Args:
            request: The HTTP request object.
            *args: Variable positional arguments.
            **kwargs: Variable keyword arguments.

        Returns:
            HttpResponse: Renders the bulk selection status partial.
        """
        if not (hasattr(request, "htmx") and request.htmx):
            return HttpResponseBadRequest(
                "Only HTMX requests are supported for this operation."
            )

        # Get object_ids from the request body (sent by HTMX). Prefer repeated
        # values, but also accept a CSV fallback for JS-triggered batch requests.
        object_ids = request.POST.getlist("object_ids")
        if not object_ids:
            csv_ids = request.POST.get("object_ids_csv", "")
            object_ids = [obj_id for obj_id in csv_ids.split(",") if obj_id]

        # Ensure IDs are integers
        object_ids = [int(obj_id) for obj_id in object_ids]
        action = request.POST.get("action") or None
        selected_ids = self.toggle_all_selection_in_session(
            request, object_ids, action=action
        )
        context = self.get_context_data()
        context["selected_ids"] = selected_ids
        context["selected_count"] = len(selected_ids)

        response = render(
            request,
            f"{self.templates_path}/object_list.html#bulk_selection_status",
            context,
        )
        response["HX-Trigger"] = json.dumps({"refreshTable": True})
        return response

    def get_filtered_selection_queryset(self):
        """
        Return the queryset for the current list view with active filters applied.
        """
        queryset = self.get_queryset()
        filterset = self.get_filterset(queryset)
        if filterset is not None:
            queryset = filterset.qs
        return queryset

    def select_all_matching_in_session(
        self, request: HttpRequest, matching_ids: List[Any]
    ) -> List[str]:
        """
        Add all provided matching IDs to the persisted selection, preserving any prior selection.
        """
        selected_ids = self.get_selected_ids_from_session(request)
        selected_id_set = set(selected_ids)

        for object_id in matching_ids:
            object_id_str = str(object_id)
            if object_id_str in selected_id_set:
                continue
            selected_ids.append(object_id_str)
            selected_id_set.add(object_id_str)

        self.save_selected_ids_to_session(request, selected_ids)
        return selected_ids

    def get_selectable_matching_ids(
        self, request: HttpRequest, queryset: Any
    ) -> List[Any]:
        """
        Return the next matching queryset IDs that can fit within the configured selection cap.
        """
        current_selected_ids = self.get_selected_ids_from_session(request)
        current_selected_id_set = set(current_selected_ids)
        remaining_capacity = max(
            0, self.get_bulk_max_selected_records() - len(current_selected_ids)
        )
        if remaining_capacity == 0:
            return []

        selectable_ids: List[Any] = []
        for object_id in queryset.values_list("pk", flat=True):
            if str(object_id) in current_selected_id_set:
                continue
            selectable_ids.append(object_id)
            if len(selectable_ids) >= remaining_capacity:
                break
        return selectable_ids

    def select_all_matching_view(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """
        Add every record matching the current filtered queryset to the persisted bulk selection.
        """
        if not (hasattr(request, "htmx") and request.htmx):
            return HttpResponseBadRequest(
                "Only HTMX requests are supported for this operation."
            )

        queryset = self.get_filtered_selection_queryset()
        selectable_ids = self.get_selectable_matching_ids(request, queryset)
        if selectable_ids:
            selected_ids = self.select_all_matching_in_session(request, selectable_ids)
        else:
            selected_ids = self.get_selected_ids_from_session(request)

        context = {
            "selected_ids": selected_ids,
            "selected_count": len(selected_ids),
        }
        response = render(
            request,
            f"{self.templates_path}/object_list.html#bulk_selection_status",
            context,
        )
        response["HX-Trigger"] = json.dumps({"refreshTable": True})
        return response
