"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# A production ASGI server must be started with an explicit settings module so
# the strict production CORS policy is used:
#
#     DJANGO_SETTINGS_MODULE=config.production_settings uvicorn config.asgi:application
#
# See config/wsgi.py for why the fallback below is development-only.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
