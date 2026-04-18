"""Forms for the optional PowerCRUD favourites contrib app."""

from __future__ import annotations

import json

from django import forms

from .models import SavedFilterFavourite
from .services import normalise_saved_state


def _clean_and_normalize_state_json(raw_value: str) -> tuple[str, dict[str, object]]:
    """Return validated serialized state plus its normalized dict form."""

    normalized_raw_value = raw_value.strip()
    if not normalized_raw_value:
        raise forms.ValidationError("Saved favourite state is required.")
    try:
        parsed_value = json.loads(normalized_raw_value)
    except json.JSONDecodeError as exc:
        raise forms.ValidationError("Saved favourite state is invalid JSON.") from exc

    normalized_value = normalise_saved_state(parsed_value)
    return json.dumps(normalized_value, sort_keys=True), normalized_value


class FavouriteMetadataForm(forms.Form):
    """Validate shared toolbar metadata passed through favourite requests."""

    view_key = forms.CharField(max_length=255, widget=forms.HiddenInput)
    list_view_url = forms.CharField(max_length=500, widget=forms.HiddenInput)
    toolbar_dom_id = forms.CharField(max_length=255, widget=forms.HiddenInput)
    original_target = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.HiddenInput,
    )
    current_state_json = forms.CharField(required=False, widget=forms.HiddenInput)
    selected_favourite_id = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput,
    )

    def clean_list_view_url(self) -> str:
        """Restrict list targets to local paths."""

        value = self.cleaned_data["list_view_url"].strip()
        if not value.startswith("/"):
            raise forms.ValidationError("List view URL must be a local path.")
        return value


class FavouriteActionForm(FavouriteMetadataForm):
    """Validate toolbar metadata plus a selected favourite id."""

    favourite_id = forms.IntegerField(min_value=1)


class FavouriteSaveForm(FavouriteMetadataForm):
    """Validate save-favourite payloads including serialized list state."""

    name = forms.CharField(
        max_length=SavedFilterFavourite.NAME_MAX_LENGTH,
        widget=forms.TextInput(
            attrs={
                "class": "input input-bordered w-full",
                "maxlength": str(SavedFilterFavourite.NAME_MAX_LENGTH),
                "placeholder": "Favourite name",
            }
        ),
    )
    state_json = forms.CharField(widget=forms.HiddenInput)

    def clean_state_json(self) -> str:
        """Validate and normalize the serialized list state payload."""

        serialized_value, normalized_value = _clean_and_normalize_state_json(
            self.cleaned_data["state_json"]
        )
        self.cleaned_data["normalized_state"] = normalized_value
        return serialized_value


class FavouriteUpdateForm(FavouriteActionForm):
    """Validate update-favourite payloads including serialized list state."""

    state_json = forms.CharField(widget=forms.HiddenInput)

    def clean_state_json(self) -> str:
        """Validate and normalize the serialized list state payload."""

        serialized_value, normalized_value = _clean_and_normalize_state_json(
            self.cleaned_data["state_json"]
        )
        self.cleaned_data["normalized_state"] = normalized_value
        return serialized_value
