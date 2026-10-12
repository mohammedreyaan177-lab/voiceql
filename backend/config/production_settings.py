from django.core.exceptions import ImproperlyConfigured

from .cors_config import (
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_PREFLIGHT_MAX_AGE,
    allow_null_origin,
    production_allowed_origins,
)
from .settings import *  # noqa: F401,F403
from .settings import _env_list, CORS_EXPOSE_HEADERS


# --------------------------------------------------------------------------- #
# Refuse to start in debug mode
# --------------------------------------------------------------------------- #

if DEBUG is True:  # noqa: F405
    raise ImproperlyConfigured(
        "DEBUG must be False in production. Set DJANGO_DEBUG=false."
    )


# --------------------------------------------------------------------------- #
# Refuse to start with the development secret key
# --------------------------------------------------------------------------- #

DEV_SECRET_MARKER = "django-insecure-"

if SECRET_KEY.startswith(DEV_SECRET_MARKER):  # noqa: F405
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is still the insecure development default. "
        "Set DJANGO_SECRET_KEY to a real secret before deploying."
    )


CORS_ALLOWED_ORIGINS = list(production_allowed_origins())

if allow_null_origin():
    CORS_ALLOWED_ORIGINS.append("null")

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGIN_REGEXES = []
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS = CORS_ALLOW_METHODS
CORS_ALLOW_HEADERS = CORS_ALLOW_HEADERS
CORS_PREFLIGHT_MAX_AGE = CORS_PREFLIGHT_MAX_AGE
CORS_EXPOSE_HEADERS = CORS_EXPOSE_HEADERS


# --------------------------------------------------------------------------- #
# Security hardening that only makes sense off-development
# --------------------------------------------------------------------------- #

ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS")

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS is required in production "
        "(comma-separated hostnames)."
    )

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Redirect plain HTTP to HTTPS.
SECURE_SSL_REDIRECT = True