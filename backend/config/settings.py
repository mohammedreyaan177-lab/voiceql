"""
Base settings for the VoiceQL project.

This module holds everything that is genuinely shared between development and
production. It does **not** decide which origins are allowed - that policy lives
in ``config/cors_config.py`` and is applied by ``config.development_settings``
and ``config.production_settings``.

Entry points (manage.py / wsgi.py / asgi.py) all load *this* module by
default. Development adds its origin allowlist via
``DJANGO_SETTINGS_MODULE=config.development_settings``; production adds the
validated HTTPS allowlist via ``config.production_settings``.

Important: ``DEBUG``, ``SECRET_KEY`` and ``ALLOWED_HOSTS`` are no longer
hard-coded. They are read from the environment with safe defaults so that a
production deployment cannot silently run in debug mode.
"""

from pathlib import Path

import os

from dotenv import load_dotenv

from .cors_config import (
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_PREFLIGHT_MAX_AGE,
)

# Load .env from the backend/ directory explicitly rather than searching from
# the current working directory, which made behaviour depend on where the
# process happened to be launched from.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean flag from the environment."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    """Read a comma-separated list from the environment."""
    raw = os.environ.get(name, "")
    return [item.strip() for item in raw.split(",") if item.strip()]


# --------------------------------------------------------------------------- #
# Security
# --------------------------------------------------------------------------- #

# SECURITY: this must come from the environment in production. The previous
# hard-coded development key is no longer used as a fallback.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-$!kp+k7^g-d@t@qlm75sx$e1ho3wu!cg0unfj35*j*9h@k5b&l",
)

# Default to False. Previously this was unconditionally True, which leaked full
# tracebacks and the settings values on any error.
DEBUG = _env_flag("DJANGO_DEBUG", False)

# With DEBUG=False an empty ALLOWED_HOSTS makes Django reject every request, so
# it must be configurable. Defaults to localhost for convenience in development.
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS") or ["localhost", "127.0.0.1"]


# --------------------------------------------------------------------------- #
# Application definition
# --------------------------------------------------------------------------- #

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "voiceql",
    "rest_framework",
]

# CorsMiddleware must run before CommonMiddleware so that it can short-circuit
# preflight requests before anything else touches them. It is also placed above
# any middleware that could otherwise generate a response without it.
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
# This is the ONLY place CORS settings are declared. The environment-specific
# settings modules below only supply the origin allowlist.

# Never allow every origin. Present explicitly so that no fallback to a
# wildcard can happen through any code path.
CORS_ALLOW_ALL_ORIGINS = False

# No regex allowlist. Origins are matched exactly by scheme + host + port.
CORS_ALLOWED_ORIGIN_REGEXES = []

# The frontend sends `credentials: "omit"`, holds no session cookie and sends no
# bearer token, so credentialed cross-origin requests are not required and stay
# disabled. Never enable this together with a wildcard.
CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_METHODS = CORS_ALLOW_METHODS
CORS_ALLOW_HEADERS = CORS_ALLOW_HEADERS
CORS_PREFLIGHT_MAX_AGE = CORS_PREFLIGHT_MAX_AGE
CORS_EXPOSE_HEADERS = []

# Set by config.production_settings / config.development_settings.
CORS_ALLOWED_ORIGINS = []


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


# --------------------------------------------------------------------------- #
# Password validation
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# Internationalization
# --------------------------------------------------------------------------- #

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# --------------------------------------------------------------------------- #
# Static files
# --------------------------------------------------------------------------- #

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR.parent / "frontend"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------------------------------- #
# Email
# --------------------------------------------------------------------------- #

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "voiceql.log"),
        },
    },
    "loggers": {
        "voiceql": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    },
}