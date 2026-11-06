from django.apps import AppConfig


class CoordinatorTestAppConfig(AppConfig):
    """Register the small model set used by coordinator tests."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "coordinator_tests.testapp"
    label = "coordinator_testapp"
