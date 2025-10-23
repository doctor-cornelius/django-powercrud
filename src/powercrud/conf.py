# powercrud/conf.py
from django.conf import settings

DEFAULTS = {
    'ASYNC_ENABLED': False,
    'CONFLICT_TTL': 3600,
    'PROGRESS_TTL': 7200,
    'CLEANUP_GRACE_PERIOD': 86400,
    'MAX_TASK_DURATION': 3600,
    'CLEANUP_SCHEDULE_INTERVAL': 300,
    'CACHE_NAME': 'default',

    'POWERCRUD_CSS_FRAMEWORK': 'daisyUI', # this is for the rendering of powercrud forms
    'TAILWIND_SAFELIST_JSON_LOC': '.',  # location of the safelist json file for tailwind tree shaker
}

def get_powercrud_setting(key: str, default=None):
    """Retrieve settings from POWERCRUD_SETTINGS dict with defaults."""
    user_settings = getattr(settings, 'POWERCRUD_SETTINGS', {})
    if key in user_settings:
        return user_settings[key]
    elif default is not None:
        return default
    else:
        return DEFAULTS.get(key)
