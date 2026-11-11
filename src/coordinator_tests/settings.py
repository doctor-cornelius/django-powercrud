"""Django settings isolated from the PowerCRUD consumer test app."""

import os
import tempfile


BASE_DIR = os.path.dirname(__file__)
TEST_CACHE_DIR = os.environ.get(
    "POWERCRUD_COORDINATOR_CACHE_DIR",
    os.path.join(tempfile.gettempdir(), f"powercrud-coordinator-cache-{os.getpid()}"),
)
SECRET_KEY = "coordinator-test-secret"
DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "coordinator_tests.urls"
ALLOWED_HOSTS = ["testserver", "localhost"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_q",
    "powercrud._coordinator.apps.CoordinatorConfig",
    "coordinator_tests.testapp.apps.CoordinatorTestAppConfig",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(TEST_CACHE_DIR, "coordinator.sqlite3"),
    }
}

CACHES = {
    alias: {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(TEST_CACHE_DIR, alias),
        "TIMEOUT": None,
    }
    for alias in ("default", "coordinator_async")
}

Q_CLUSTER = {
    "name": "coordinator-tests",
    "workers": 1,
    "timeout": 30,
    "retry": 60,
    "save_limit": 250,
    "sync": True,
    "orm": "default",
}

MIGRATION_MODULES = {"coordinator_testapp": None}
