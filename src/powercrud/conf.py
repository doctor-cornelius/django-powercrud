# powercrud/conf.py
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

DEFAULTS = {
    "ASYNC_ENABLED": False,
    "CONFLICT_TTL": 3600,
    "PROGRESS_TTL": 7200,
    "CLEANUP_GRACE_PERIOD": 86400,
    "MAX_TASK_DURATION": 3600,
    "CLEANUP_SCHEDULE_INTERVAL": 300,
    "CACHE_NAME": "default",
    "QCLUSTER_PROBE_TIMEOUT_MS": 300,
    "POWERCRUD_CSS_FRAMEWORK": "daisyUI",  # this is for the rendering of powercrud forms
    "TAILWIND_SAFELIST_JSON_LOC": ".",  # location of the safelist json file for tailwind tree shaker
}


def get_powercrud_setting(key: str, default=None):
    """Retrieve settings from POWERCRUD_SETTINGS dict with defaults.

    POWERCRUD_SETTINGS is expected to be a dict. When Django settings have not
    yet been configured (for example in lightweight scripts or nanodjango-style
    setups that import powercrud before initialising Django), this helper
    silently falls back to PowerCRUD's internal defaults rather than raising
    ImproperlyConfigured.
    """
    # Avoid touching LazySettings before Django has been configured. Accessing
    # arbitrary attributes on an unconfigured settings object would trigger
    # settings._setup() and raise ImproperlyConfigured. In that early-import
    # phase we only honour the library defaults and any explicit `default`.
    if not getattr(settings, "configured", False):
        if default is not None:
            return default
        return DEFAULTS.get(key)

    user_settings = getattr(settings, "POWERCRUD_SETTINGS", None)
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
