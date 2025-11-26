# powercrud/conf.py
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULTS = {
    'ASYNC_ENABLED': False,
    'CONFLICT_TTL': 3600,
    'PROGRESS_TTL': 7200,
    'CLEANUP_GRACE_PERIOD': 86400,
    'MAX_TASK_DURATION': 3600,
    'CLEANUP_SCHEDULE_INTERVAL': 300,
    'CACHE_NAME': 'default',
    'QCLUSTER_PROBE_TIMEOUT_MS': 300,

    'POWERCRUD_CSS_FRAMEWORK': 'daisyUI', # this is for the rendering of powercrud forms
    'TAILWIND_SAFELIST_JSON_LOC': '.',  # location of the safelist json file for tailwind tree shaker
}


def get_powercrud_setting(key: str, default=None):
    """Retrieve settings from POWERCRUD_SETTINGS dict with defaults.

    POWERCRUD_SETTINGS is expected to be a dict; if a project overrides it with
    a non-mapping value, raise a clear ImproperlyConfigured error rather than
    failing with a TypeError when looking up keys.
    """
    user_settings = getattr(settings, 'POWERCRUD_SETTINGS', None)
    if user_settings is None:
        user_settings = {}
    elif not isinstance(user_settings, dict):
        raise ImproperlyConfigured(
            f"POWERCRUD_SETTINGS must be a dict if defined; found {type(user_settings).__name__} instead."
        )

    if key in user_settings:
        return user_settings[key]
    if default is not None:
        return default
    return DEFAULTS.get(key)
