from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

print(f"BASE_DIR: {BASE_DIR}")

APP_DIRS = True

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "o5i8xzi$x^1)4f-ko+%xfif_vxfrtl9t3^hr_7$$!r75txzf$d"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "powercrud": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django_vite",
    "template_partials",
    'django_htmx',

    "crispy_forms",
    # "crispy_bootstrap5",
    "crispy_tailwind",
    "crispy_daisyui",

    # for async
    'django_q',
    'django_redis',

    # project apps
    "powercrud",
    "neapolitan",
    "sample",
    
]


# NB we use crispy_tailwind because crispy_daisyui classes don't seem to work with daisyUI v5
# (and they don't come through to the tailwind tree shaker either even when you include the repo files in templates)
CRISPY_ALLOWED_TEMPLATE_PACKS = ['tailwind', 'daisyui']
CRISPY_TEMPLATE_PACK = 'tailwind'

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

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "sample" / "templates",
        ],
        "APP_DIRS": True,  # Change this to True
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "builtins": [
                "django.templatetags.i18n",
                "django.templatetags.static",
                "django_htmx.templatetags.django_htmx",
                "template_partials.templatetags.partials",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "powercrud" / "assets", # for vite setup
]

STATIC_ROOT = BASE_DIR / "powercrud" / "staticfiles"

VITE_HOST = os.getenv("DJANGO_VITE_HOST", "localhost")
VITE_PORT = int(os.getenv("DJANGO_VITE_PORT", 5174))

DJANGO_VITE = {
  "default": {
    "dev_mode": DEBUG, # set to use DEBUG variable (ie False in Production)
    "dev_server_port": VITE_PORT, # match setting in server key of vite.config.mjs
    "dev_server_host": VITE_HOST,
  }
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session Settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Default, using database
SESSION_COOKIE_AGE = 300  # 5 minutes in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Sessions expire when browser closes
SESSION_SAVE_EVERY_REQUEST = True  # Update session expiry on every request

DATABASES = {
    # postgres
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("DATABASE_HOST"),
        "PORT": "5433",
    }
}


# django-q2 settings
Q_CLUSTER = {
    "name": "powercrud",
    "workers": 4,
    "recycle": 500,
    "timeout": 250,
    "retry": 300,
    "save_limit": 250,
    "queue_limit": 500,
    # NB if you set orm then other backend settings (eg django_redis, redis) are ignored
    "orm": "default",  # database connection to use
    # 'django_redis': 'default',  # cache name
}

POWERCRUD_SETTINGS = {
    # this is for the rendering of powercrud forms
    "POWERCRUD_CSS_FRAMEWORK": "daisyUI",
    # location of the safelist json file for tailwind tree shaker)
    "TAILWIND_SAFELIST_JSON_LOC": "sample/templates/sample/",
    # async settings
    "ASYNC_ENABLED": True,
    "CONFLICT_TTL": 3600,  # 1 hour
    "PROGRESS_TTL": 7200,  # 2 hours
    "CLEANUP_GRACE_PERIOD": 86400,  # 24 hours
    "MAX_TASK_DURATION": 3600,  # For detecting stuck tasks
    "CLEANUP_SCHEDULE_INTERVAL": 300,  # 5 minutes for scheduled cleanup
    "CACHE_NAME": "default",  # Which cache from CACHES to use for async conflict/progress
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",  # Use database 1 for default cache
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.environ.get("REDIS_PASSWORD"),
        },
        "KEY_PREFIX": "powercrud",
    },
    "powercrud_async": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "powercrud_async_cache",
        "KEY_PREFIX": "powercrud",
        "TIMEOUT": None,
    },
    "db_cache": {  # for testing db backed cache for conflict/progress
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "async_cache_table", 
        "KEY_PREFIX": "powercrud",
    }
}

# increase to allow max selected_ids for bulk ops
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
