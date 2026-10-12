#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Default to config.settings only when nothing is configured. An explicit
    # DJANGO_SETTINGS_MODULE (config.development_settings or
    # config.production_settings) is honoured so deployment tooling can select
    # the intended policy. Deprecated CORS modules are rejected in
    # config/__init__.py, which runs on import of any config.* module.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
