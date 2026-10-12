from .cors_config import (
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    DEV_ALLOWED_ORIGINS,
    allow_null_origin,
)
from .settings import *  # noqa: F401,F403
from .settings import CORS_ALLOW_ALL_ORIGINS, CORS_EXPOSE_HEADERS

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

# Explicit local allowlist. `localhost` and `127.0.0.1` are both listed because
# a browser treats them as separate origins.
CORS_ALLOWED_ORIGINS = list(DEV_ALLOWED_ORIGINS)

# Only add `null` if explicitly requested; it is off by default.
if allow_null_origin():
    CORS_ALLOWED_ORIGINS.append("null")

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS = CORS_ALLOW_METHODS
CORS_ALLOW_HEADERS = CORS_ALLOW_HEADERS
CORS_EXPOSE_HEADERS = CORS_EXPOSE_HEADERS

CSRF_TRUSTED_ORIGINS = list(DEV_ALLOWED_ORIGINS)