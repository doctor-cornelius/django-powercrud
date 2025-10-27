import os

SECRET_KEY = "just-for-testing-secret-key"

if os.environ.get("DATABASE_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DATABASE_NAME"),
            "USER": os.environ.get("POSTGRES_USER"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
            "HOST": os.environ.get("DATABASE_HOST"),
            "PORT": "5433",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(os.path.dirname(__file__), "test.sqlite3"),
        }
    }

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]


ROOT_URLCONF = "config.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Session Settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # Default, using database
SESSION_COOKIE_AGE = 300  # 5 minutes in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Sessions expire when browser closes
SESSION_SAVE_EVERY_REQUEST = True  # Update session expiry on every request

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(os.path.dirname(__file__), "staticfiles")
os.makedirs(STATIC_ROOT, exist_ok=True)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": True,
            "builtins": [
                "django.templatetags.i18n",
                "django.templatetags.static",
                "django_htmx.templatetags.django_htmx",
                "template_partials.templatetags.partials",
            ],
        },
    },
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "template_partials",
    'django_htmx',
    "django_filters",

    # for async
    'django_q',
    'django_redis',
    "django_vite",

    "neapolitan",
    "powercrud",
    "sample",
    "tests",
]


TEST_CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(TEST_CACHE_DIR, exist_ok=True)
os.makedirs(os.path.join(TEST_CACHE_DIR, "default"), exist_ok=True)
os.makedirs(os.path.join(TEST_CACHE_DIR, "async"), exist_ok=True)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(TEST_CACHE_DIR, "default"),
        "TIMEOUT": None,
    },
    "powercrud_async": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(TEST_CACHE_DIR, "async"),
        "TIMEOUT": None,
    },
}


POWERCRUD_SETTINGS = {
     # this is for the rendering of powercrud forms
    'POWERCRUD_CSS_FRAMEWORK': 'daisyUI',
    # location of the safelist json file for tailwind tree shaker)
    'TAILWIND_SAFELIST_JSON_LOC': 'sample/templates/sample/', 

    # async settings
    'ASYNC_ENABLED': True,
    'CONFLICT_TTL': 3600,  # 1 hour
    'PROGRESS_TTL': 7200,  # 2 hours
    'CLEANUP_GRACE_PERIOD': 86400,  # 24 hours
    'MAX_TASK_DURATION': 3600,  # For detecting stuck tasks
    'CLEANUP_SCHEDULE_INTERVAL': 300,  # 5 minutes for scheduled cleanup
    'CACHE_NAME': 'powercrud_async',  # Which cache from CACHES to use for conflict/progress
    'QCLUSTER_PROBE_TIMEOUT_MS': 1500,
}

# django-q2 settings
Q_CLUSTER = {
    'name': 'powercrud',
    'workers': 4, 
    'recycle': 500,
    'timeout': 250,
    'retry': 300,
    'save_limit': 250,
    'queue_limit': 500,
    'sync': True,
    # NB if you set orm then other backend settings (eg django_redis, redis) are ignored
    'orm': 'default',  # database connection to use
    'django_redis': 'default',  # cache name
}
