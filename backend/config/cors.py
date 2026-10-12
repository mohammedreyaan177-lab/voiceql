"""
DEPRECATED - the hand-rolled wildcard CORS middleware has been removed.

The middleware that used to live here set::

    response["Access-Control-Allow-Origin"] = "*"

on every response, unconditionally, for every origin, with no allowlist. It has
been replaced by the maintained ``django-cors-headers`` package, configured in
``config.cors_config``.

This module is kept only so that any leftover reference fails loudly with a
clear explanation instead of silently reintroducing a wildcard policy. It is not
imported by any settings module.

Do not add this class back to MIDDLEWARE. Use::

    "corsheaders.middleware.CorsMiddleware"
"""


class CorsMiddleware:
    """
    Raises ``RuntimeError`` when instantiated.

    This exists as a tombstone so that a stale ``MIDDLEWARE`` entry produces an
    immediate, obvious failure rather than a silently permissive API.
    """

    def __init__(self, get_response):
        raise RuntimeError(
            "config.cors.CorsMiddleware has been removed. It allowed every "
            "origin with Access-Control-Allow-Origin: *. Use "
            "'corsheaders.middleware.CorsMiddleware' instead; the allowed "
            "origins are configured in config/cors_config.py and applied by "
            "config/development_settings.py or config/production_settings.py."
        )


# Preserve the old constants only so that importing them for reference does not
# break; they are intentionally unused.
ALLOWED_METHODS = "GET, POST, OPTIONS"
ALLOWED_HEADERS = "Accept, Content-Type, Origin, X-Requested-With"