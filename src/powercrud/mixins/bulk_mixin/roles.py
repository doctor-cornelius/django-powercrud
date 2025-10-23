import enum
from typing import Dict, Any

from django.urls import path
from django.views import View

# Create a standalone BulkEditRole class
class BulkEditRole:
    """A role for bulk editing that mimics the interface of Django-neapolitan's Role."""
    
    def handlers(self) -> Dict[str, str]:
        """
        Define the view handlers for the bulk edit role.

        Returns:
            Dict[str, str]: A dictionary mapping HTTP methods to view method names.
        """
        return {"get": "bulk_edit", "post": "bulk_edit"}
    
    def extra_initkwargs(self) -> Dict[str, str]:
        """
        Provide extra keyword arguments for the view's __init__ method.

        Returns:
            Dict[str, str]: A dictionary of extra init kwargs.
        """
        return {"template_name_suffix": "_bulk_edit"}
    
    @property
    def url_name_component(self) -> str:
        """
        Return the URL name component for the bulk edit role.

        Returns:
            str: The URL name component.
        """
        return "bulk-edit"
    
    def url_pattern(self, view_cls: type[View]) -> str:
        """
        Generate the URL pattern for the bulk edit role.

        Args:
            view_cls: The Django View class.

        Returns:
            str: The URL pattern string.
        """
        return f"{view_cls.url_base}/bulk-edit/"
    
    def get_url(self, view_cls: type[View]):
        """
        Get the URL path object for the bulk edit role.

        Args:
            view_cls: The Django View class.

        Returns:
            path: The Django URL path object.
        """
        return path(
            self.url_pattern(view_cls),
            view_cls.as_view(role=self),
            name=f"{view_cls.url_base}-{self.url_name_component}",
        )

class BulkActions(enum.Enum):
    """Enum defining various bulk action types and their associated view handling."""
    TOGGLE_SELECTION = "toggle-selection"
    CLEAR_SELECTION = "clear-selection"
    TOGGLE_ALL_SELECTION = "toggle-all-selection"

    def handlers(self) -> Dict[str, str]:
        """
        Define the view handlers for each bulk action.

        Returns:
            Dict[str, str]: A dictionary mapping HTTP methods to view method names.
        """
        match self:
            case BulkActions.TOGGLE_SELECTION:
                return {"post": "toggle_selection_view"}
            case BulkActions.CLEAR_SELECTION:
                return {"post": "clear_selection_view"}
            case BulkActions.TOGGLE_ALL_SELECTION:
                return {"post": "toggle_all_selection_view"}

    def extra_initkwargs(self) -> Dict[str, str]:
        """
        Provide extra keyword arguments for the view's __init__ method based on the action.

        Returns:
            Dict[str, str]: A dictionary of extra init kwargs.
        """
        match self:
            case BulkActions.TOGGLE_SELECTION:
                return {"template_name_suffix": "_toggle_selection"}
            case BulkActions.CLEAR_SELECTION:
                return {"template_name_suffix": "_clear_selection"}
            case BulkActions.TOGGLE_ALL_SELECTION:
                return {"template_name_suffix": "_toggle_all_selection"}

    @property
    def url_name_component(self) -> str:
        """
        Return the URL name component for the specific bulk action.

        Returns:
            str: The URL name component.
        """
        return self.value

    def url_pattern(self, view_cls: type[View]) -> str:
        """
        Generate the URL pattern for the specific bulk action.

        Args:
            view_cls: The Django View class.

        Returns:
            str: The URL pattern string.
        """
        url_kwarg = view_cls.lookup_url_kwarg or view_cls.lookup_field
        match self:
            case BulkActions.TOGGLE_SELECTION:
                return f"{view_cls.url_base}/toggle-selection/<int:{url_kwarg}>/"
            case BulkActions.CLEAR_SELECTION:
                return f"{view_cls.url_base}/clear-selection/"
            case BulkActions.TOGGLE_ALL_SELECTION:
                return f"{view_cls.url_base}/toggle-all-selection/"

    def get_url(self, view_cls: type[View]):
        """
        Get the URL path object for the specific bulk action.

        Args:
            view_cls: The Django View class.

        Returns:
            path: The Django URL path object.
        """
        return path(
            self.url_pattern(view_cls),
            view_cls.as_view(
                role=self,
                lookup_url_kwarg=view_cls.lookup_url_kwarg or view_cls.lookup_field,
                lookup_field=view_cls.lookup_field,
            ),
            name=f"{view_cls.url_base}-{self.url_name_component}",
        )

