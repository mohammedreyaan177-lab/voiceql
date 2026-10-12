"""
DEPRECATED - superseded by ``config.development_settings``.

This module used to activate the wildcard middleware in ``config/cors.py`` and
was only reachable through an undocumented shell environment variable::

    DJANGO_SETTINGS_MODULE=config.cors_settings

That was the configuration-bypass risk: because ``manage.py`` / ``wsgi.py`` /
``asgi.py`` all use ``os.environ.setdefault``, any shell that happened to export
this value silently changed the CORS policy, and a deployment without that
variable got an entirely different (no-CORS-at-all) policy.

It is kept as a thin alias so that an existing shell export still boots, but it
now delegates to the real development settings and carries no CORS logic of its
own. ``config/__init__.py`` prints a deprecation warning when it is selected.

Use ``config.development_settings`` directly.
"""

from .development_settings import *  # noqa: F401,F403