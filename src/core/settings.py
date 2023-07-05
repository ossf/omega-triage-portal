import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from . import to_bool

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read environment variables from a file
try:
    import dotenv

    dotenv.load_dotenv(os.path.join(BASE_DIR, ".env-template"))
except Exception as ex:
    raise ImproperlyConfigured(
        "A .env-template file was not found. Environment variables are not set.",
    ) from ex

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = to_bool(os.getenv("DEBUG"))
TRIAGE_PORTAL_DEVELOPMENT_MODE = to_bool(os.getenv("TRIAGE_PORTAL_DEVELOPMENT_MODE"))

INTERNAL_IPS = []
if TRIAGE_PORTAL_DEVELOPMENT_MODE:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ["omega-triageportal-dev1.azurewebsites.net"]

if "CODESPACE_NAME" in os.environ:
    codespace_name = os.getenv("CODESPACE_NAME")
    codespace_domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
    CSRF_TRUSTED_ORIGINS = [f"https://{codespace_name}-8001.{codespace_domain}"]
    X_FRAME_OPTIONS = "ALLOW-FROM preview.app.github.dev"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "taggit",
    "triage",
    "debug_toolbar",
    "core",
    "data",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

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
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

STATIC_ROOT = "/opt/omega/static"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        # Comment out for Local dev values
        "ENGINE": os.getenv("DATABASE_ENGINE"),
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT"),
    },
}
if not TRIAGE_PORTAL_DEVELOPMENT_MODE:
    DATABASES["default"]["OPTIONS"] = {
        "sslmode": "require",
        "options": "-c statement_timeout=5000",
    }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Set up caching
DEFAULT_CACHE_TIMEOUT = 60 * 30  # 30 minutes
CACHES = {}
if to_bool(os.getenv("ENABLE_CACHE")):
    if to_bool(os.getenv("CACHE_USE_REDIS")):
        CACHES = {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": os.getenv("CACHE_REDIS_CONNECTION"),
                "OPTIONS": {
                    "CLIENT_CLASS": "django_redis.client.DefaultClient",
                    "TIMEOUT": DEFAULT_CACHE_TIMEOUT,
                    "PASSWORD": os.getenv("CACHE_REDIS_PASSWORD"),
                },
            },
        }
    else:
        CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "unique-snowflake",
                "TIMEOUT": DEFAULT_CACHE_TIMEOUT,
            },
        }

# Configure application logging
# Disable logging if pylint or pytest is running
if "PYLINT" not in os.environ and "pytest" not in sys.modules:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)s] %(message)s",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
                "level": "WARNING",
            },
            #'appinsights': {
            #    'class': 'applicationinsights.django.LoggingHandler',
            #    'level': 'INFO',
            # },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(BASE_DIR, "..", "logs", "omega-triage.log"),
                "maxBytes": 1024 * 1024 * 50,  # 50 MB
                "backupCount": 5,
                "formatter": "verbose",
                "encoding": "utf-8",
            },
            "database-log": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": os.path.join(BASE_DIR, "..", "logs", "database.log"),
                "maxBytes": 1024 * 1024 * 50,  # 50 MB
                "backupCount": 1,
                "formatter": "verbose",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["file", "console"],
                "level": "WARNING",
                "propagate": True,
            },
            "django": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "django.db": {
                "level": "DEBUG",
                "handlers": ["database-log"],
                "propagate": True,
            },
            "triage": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
else:
    LOGGING = {}

TOOLSHED_BLOB_STORAGE_CONTAINER_SECRET = os.getenv("TOOLSHED_BLOB_STORAGE_CONTAINER")
TOOLSHED_BLOB_STORAGE_URL_SECRET = os.getenv("TOOLSHED_BLOB_STORAGE_URL")

OSSGADGET_PATH = os.getenv("OSSGADGET_PATH")

AUTH_USER_MODEL = "auth.User"  # pylint: disable=hard-coded-auth-user

# File Storage Providers for files, attachments, etc.
FILE_STORAGE_PROVIDERS = {
    "default": {
        "provider": "triage.util.content_managers.file_manager.FileManager",
        "args": {"root_path": "/home/vscode/omega-fs"},
    },
}
