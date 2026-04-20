"""Views for the optional PowerCRUD favourites contrib app."""

from __future__ import annotations

import json

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import FavouriteActionForm, FavouriteSaveForm, FavouriteUpdateForm
from .models import SavedFilterFavourite
from .services import (
    build_query_string_from_state,
    build_toolbar_context,
    create_saved_favourite,
)


def _build_default_save_form(
    *,
    view_key: str,
    list_view_url: str,
    toolbar_dom_id: str,
    current_state_json: str,
    original_target: str,
    selected_favourite_id: int | None = None,
) -> FavouriteSaveForm:
    """Return a pre-populated inline save form for the toolbar panel."""

    return FavouriteSaveForm(
        initial={
            "view_key": view_key,
            "list_view_url": list_view_url,
            "toolbar_dom_id": toolbar_dom_id,
            "current_state_json": current_state_json,
            "state_json": current_state_json,
            "original_target": original_target,
            "selected_favourite_id": selected_favourite_id,
        }
    )


def _build_toolbar_render_context(
    *,
    request: HttpRequest,
    view_key: str,
    list_view_url: str,
    toolbar_dom_id: str,
    current_state_json: str,
    original_target: str,
    selected_favourite_id: int | None = None,
    show_save_form: bool = False,
    save_form: FavouriteSaveForm | None = None,
) -> dict[str, object]:
    """Return a consistent toolbar context for initial and refreshed renders."""

    resolved_save_form = save_form or _build_default_save_form(
        view_key=view_key,
        list_view_url=list_view_url,
        toolbar_dom_id=toolbar_dom_id,
        current_state_json=current_state_json,
        original_target=original_target,
        selected_favourite_id=selected_favourite_id,
    )

    return build_toolbar_context(
        user=request.user,
        view_key=view_key,
        list_view_url=list_view_url,
        toolbar_dom_id=toolbar_dom_id,
        current_state_json=current_state_json,
        original_target=original_target,
        toolbar_url=reverse("powercrud:favourites-toolbar"),
        save_url=reverse("powercrud:favourites-save"),
        apply_url=reverse("powercrud:favourites-apply"),
        update_url=reverse("powercrud:favourites-update"),
        delete_url=reverse("powercrud:favourites-delete"),
        selected_favourite_id=selected_favourite_id,
        show_save_form=show_save_form,
        save_form=resolved_save_form,
    )


def _render_toolbar_response(
    *,
    request: HttpRequest,
    view_key: str,
    list_view_url: str,
    toolbar_dom_id: str,
    current_state_json: str,
    original_target: str,
    selected_favourite_id: int | None = None,
    show_save_form: bool = False,
    save_form: FavouriteSaveForm | None = None,
) -> HttpResponse:
    """Render the toolbar partial for HTMX or direct include use."""

    context = _build_toolbar_render_context(
        request=request,
        view_key=view_key,
        list_view_url=list_view_url,
        toolbar_dom_id=toolbar_dom_id,
        current_state_json=current_state_json,
        original_target=original_target,
        selected_favourite_id=selected_favourite_id,
        show_save_form=show_save_form,
        save_form=save_form,
    )
    return render(
        request,
        "powercrud/contrib/favourites/toolbar.html",
        context,
    )


def _render_toolbar_panel_response(
    *,
    request: HttpRequest,
    view_key: str,
    list_view_url: str,
    toolbar_dom_id: str,
    current_state_json: str,
    original_target: str,
    selected_favourite_id: int | None = None,
    show_save_form: bool = False,
    save_form: FavouriteSaveForm | None = None,
    status: int = 200,
) -> HttpResponse:
    """Render only the mutable favourites dropdown panel content."""

    context = _build_toolbar_render_context(
        request=request,
        view_key=view_key,
        list_view_url=list_view_url,
        toolbar_dom_id=toolbar_dom_id,
        current_state_json=current_state_json,
        original_target=original_target,
        selected_favourite_id=selected_favourite_id,
        show_save_form=show_save_form,
        save_form=save_form,
    )
    return render(
        request,
        "powercrud/contrib/favourites/toolbar_panel.html",
        context,
        status=status,
    )


def _coerce_selected_favourite_id(raw_value: str | None) -> int | None:
    """Return a validated integer favourite id or ``None``."""

    if not raw_value:
        return None
    try:
        selected_id = int(str(raw_value).strip())
    except (TypeError, ValueError):
        return None
    return selected_id if selected_id > 0 else None


def _forbidden_response(message: str) -> HttpResponseForbidden:
    """Return a consistent forbidden response for unauthenticated actions."""

    return HttpResponseForbidden(message)


@require_GET
def favourites_toolbar(request: HttpRequest) -> HttpResponse:
    """Render the favourites toolbar partial for one list view."""

    view_key = request.GET.get("view_key", "").strip()
    list_view_url = request.GET.get("list_view_url", "").strip()
    toolbar_dom_id = request.GET.get("toolbar_dom_id", "").strip()
    current_state_json = request.GET.get("current_state_json", "").strip()
    original_target = request.GET.get("original_target", "").strip()
    show_save_form = request.GET.get("show_save_form", "").strip() == "1"
    selected_favourite_id = _coerce_selected_favourite_id(
        request.GET.get("selected_favourite_id") or request.GET.get("favourite_id")
    )

    if show_save_form:
        save_form = _build_default_save_form(
            view_key=view_key,
            list_view_url=list_view_url,
            toolbar_dom_id=toolbar_dom_id,
            current_state_json=current_state_json,
            original_target=original_target,
            selected_favourite_id=selected_favourite_id,
        )
        return _render_toolbar_panel_response(
            request=request,
            view_key=view_key,
            list_view_url=list_view_url,
            toolbar_dom_id=toolbar_dom_id,
            current_state_json=current_state_json,
            original_target=original_target,
            selected_favourite_id=selected_favourite_id,
            show_save_form=True,
            save_form=save_form,
        )

    return _render_toolbar_response(
        request=request,
        view_key=view_key,
        list_view_url=list_view_url,
        toolbar_dom_id=toolbar_dom_id,
        current_state_json=current_state_json,
        original_target=original_target,
        selected_favourite_id=selected_favourite_id,
    )


@require_POST
def favourite_save(request: HttpRequest) -> HttpResponse:
    """Persist a new saved favourite for the current user."""

    if not request.user.is_authenticated:
        return _forbidden_response("Sign in to save favourites.")

    form = FavouriteSaveForm(request.POST)
    if form.is_valid():
        if SavedFilterFavourite.objects.filter(
            user=request.user,
            view_key=form.cleaned_data["view_key"],
            name=form.cleaned_data["name"].strip(),
        ).exists():
            form.add_error(
                "name",
                "A saved favourite with this name already exists for this list.",
            )
        else:
            saved_favourite = create_saved_favourite(
                user=request.user,
                view_key=form.cleaned_data["view_key"],
                name=form.cleaned_data["name"],
                state=form.cleaned_data["normalized_state"],
            )

    if not form.is_valid():
        return _render_toolbar_panel_response(
            request=request,
            view_key=form.data.get("view_key", "").strip(),
            list_view_url=form.data.get("list_view_url", "").strip(),
            toolbar_dom_id=form.data.get("toolbar_dom_id", "").strip(),
            current_state_json=form.data.get("current_state_json", "").strip(),
            original_target=form.data.get("original_target", "").strip(),
            selected_favourite_id=_coerce_selected_favourite_id(
                form.data.get("selected_favourite_id")
            ),
            show_save_form=True,
            save_form=form,
            status=200,
        )

    response = _render_toolbar_panel_response(
        request=request,
        view_key=form.cleaned_data["view_key"],
        list_view_url=form.cleaned_data["list_view_url"],
        toolbar_dom_id=form.cleaned_data["toolbar_dom_id"],
        current_state_json=form.cleaned_data["state_json"],
        original_target=form.cleaned_data["original_target"],
        selected_favourite_id=saved_favourite.pk,
    )
    response["HX-Trigger"] = json.dumps(
        {"powercrud:favourite-saved": {"favouriteId": saved_favourite.pk}}
    )
    return response


@require_GET
def favourite_apply(request: HttpRequest) -> HttpResponse:
    """Apply a saved favourite and navigate to the saved list state."""

    if not request.user.is_authenticated:
        return _forbidden_response("Sign in to apply saved favourites.")

    form = FavouriteActionForm(request.GET)
    if not form.is_valid():
        return HttpResponse("Invalid favourite selection.", status=400)

    favourite = get_object_or_404(
        SavedFilterFavourite,
        pk=form.cleaned_data["favourite_id"],
        user=request.user,
        view_key=form.cleaned_data["view_key"],
    )
    query_string = build_query_string_from_state(favourite.state)
    target_url = form.cleaned_data["list_view_url"]
    if query_string:
        target_url = f"{target_url}?{query_string}"

    if request.htmx:
        response = HttpResponse()
        hx_location_payload = {
            "path": target_url,
            "push": target_url,
        }
        original_target = form.cleaned_data.get("original_target", "").strip()
        if original_target:
            hx_location_payload["target"] = original_target
            hx_location_payload["swap"] = "innerHTML"
        response["HX-Location"] = json.dumps(hx_location_payload)
        return response

    return redirect(target_url)


@require_http_methods(["POST"])
def favourite_update(request: HttpRequest) -> HttpResponse:
    """Update the selected favourite with the current list state."""

    if not request.user.is_authenticated:
        return _forbidden_response("Sign in to update saved favourites.")

    form = FavouriteUpdateForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Invalid favourite selection.", status=400)

    favourite = get_object_or_404(
        SavedFilterFavourite,
        pk=form.cleaned_data["favourite_id"],
        user=request.user,
        view_key=form.cleaned_data["view_key"],
    )
    favourite.state = form.cleaned_data["normalized_state"]
    favourite.save(update_fields=["state", "updated_at"])

    response = _render_toolbar_panel_response(
        request=request,
        view_key=form.cleaned_data["view_key"],
        list_view_url=form.cleaned_data["list_view_url"],
        toolbar_dom_id=form.cleaned_data["toolbar_dom_id"],
        current_state_json=form.cleaned_data["state_json"],
        original_target=form.cleaned_data["original_target"],
        selected_favourite_id=favourite.pk,
    )
    response["HX-Trigger"] = json.dumps(
        {"powercrud:favourite-updated": {"favouriteId": favourite.pk}}
    )
    return response


@require_http_methods(["POST"])
def favourite_delete(request: HttpRequest) -> HttpResponse:
    """Delete a saved favourite for the current authenticated user."""

    if not request.user.is_authenticated:
        return _forbidden_response("Sign in to delete saved favourites.")

    form = FavouriteActionForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Invalid favourite selection.", status=400)

    favourite = get_object_or_404(
        SavedFilterFavourite,
        pk=form.cleaned_data["favourite_id"],
        user=request.user,
        view_key=form.cleaned_data["view_key"],
    )
    favourite_id = favourite.pk
    favourite.delete()

    response = _render_toolbar_panel_response(
        request=request,
        view_key=form.cleaned_data["view_key"],
        list_view_url=form.cleaned_data["list_view_url"],
        toolbar_dom_id=form.cleaned_data["toolbar_dom_id"],
        current_state_json=form.cleaned_data["current_state_json"],
        original_target=form.cleaned_data["original_target"],
    )
    response["HX-Trigger"] = json.dumps(
        {"powercrud:favourite-deleted": {"favouriteId": favourite_id}}
    )
    return response
