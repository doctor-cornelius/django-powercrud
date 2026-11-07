from django.conf import settings


def test_coordinator_uses_owned_django_configuration():
    """Keep the suite independent of PowerCRUD's consumer test settings."""
    installed = set(settings.INSTALLED_APPS)
    assert settings.ROOT_URLCONF == "coordinator_tests.urls", "Coordinator URLConf must be suite-owned"
    assert "django_q" in installed, "Coordinator settings must install django-q2"
    assert "coordinator_tests.testapp.apps.CoordinatorTestAppConfig" in installed, "Coordinator test app must be installed"
    assert "powercrud" not in installed, "PowerCRUD must not be installed in coordinator settings"
    assert "sample" not in installed, "Sample app must not be installed in coordinator settings"
    assert not hasattr(settings, "POWERCRUD_SETTINGS"), "Coordinator settings must not define PowerCRUD settings"
