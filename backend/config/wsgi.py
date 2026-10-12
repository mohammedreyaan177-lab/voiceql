"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# A production WSGI server must be started with an explicit settings module so
# the strict production CORS policy is used:
#
#     DJANGO_SETTINGS_MODULE=config.production_settings gunicorn config.wsgi:application
#
# The fallback below exists so `runserver` keeps working locally; it is never
# the intended production configuration because config.production_settings
# refuses to start without DJANGO_DEBUG=false, a real DJANGO_SECRET_KEY,
# DJANGO_ALLOWED_HOSTS and a validated VOICEQL_CORS_ALLOWED_ORIGINS.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
