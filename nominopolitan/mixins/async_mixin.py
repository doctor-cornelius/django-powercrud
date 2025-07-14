from typing import List, Tuple
from django.conf import settings


class AsyncMixin:
    """
    Provides asynchronous bulk processing capabilities.
    """
    # bulk async methods
    def get_bulk_async_enabled(self) -> bool:
        """
        Determine if async bulk processing should be enabled.
        
        Returns:
            bool: True if async processing is enabled and backend is available
        """
        return self.bulk_async and self.is_async_backend_available()

    def get_bulk_min_async_records(self) -> int:
        """
        Get the minimum number of records required to trigger async processing.
        
        Returns:
            int: Minimum record count for async processing
        """
        return self.bulk_min_async_records

    def get_bulk_async_backend(self) -> str:
        """
        Get the configured async backend.
        
        Returns:
            str: Backend name ('database', 'celery', 'asgi')
        """
        return self.bulk_async_backend

    def get_bulk_async_notification(self) -> str:
        """
        Get the configured notification method for async operations.
        
        Returns:
            str: Notification method ('status_page', 'messages', 'email', 'callback', 'none')
        """
        return self.bulk_async_notification

    def should_process_async(self, record_count: int) -> bool:
        """
        Determine if a bulk operation should be processed asynchronously.
        
        Args:
            record_count: Number of records to be processed
            
        Returns:
            bool: True if operation should be async, False for sync processing
        """
        if not self.get_bulk_async_enabled():
            return False
        
        return record_count >= self.get_bulk_min_async_records()

    def is_async_backend_available(self) -> bool:
        """
        Check if the configured async backend is available and properly configured.
        
        Returns:
            bool: True if backend is available, False otherwise
        """
        backend = self.get_bulk_async_backend()
        
        if backend == 'q2':
            try:
                import django_q
                
                # Check if django_q is in INSTALLED_APPS
                if 'django_q' not in settings.INSTALLED_APPS:
                    return False
                    
                # Basic check - more comprehensive validation can be added later
                return True
                
            except ImportError:
                return False
        
        # Future backends (celery, etc.) would be checked here
        return False

    def validate_async_configuration(self) -> Tuple[bool, List[str]]:
        """
        Placeholder for validating async config.
        """

        return (False, [])