"""
Project package initialiser.

Runs whenever any ``config.<something>`` settings module is imported, which
makes it the one place that can catch the environment-variable bypass that used
to affect this project.
"""

import os

#: Settings modules that used to carry the wildcard CORS policy.
#:
#: ``cors_settings`` selected the removed hand-rolled middleware and was only
#: ever activated by an undocumented shell variable. ``cors`` was never a
#: settings module but is rejected too, to catch a typo in a deployment command.
_DEPRECATED_SETTINGS_MODULES = frozenset(
    {
        "config.cors_settings",
        "config.cors",
    }
)


def _reject_deprecated_settings_module() -> None:
    """Refuse to silently run under a deprecated CORS settings module."""
    selected = os.environ.get("DJANGO_SETTINGS_MODULE")

    if selected in _DEPRECATED_SETTINGS_MODULES:
        raise RuntimeError(
            f"DJANGO_SETTINGS_MODULE={selected!r} is deprecated and is no "
            "longer a supported way to configure this project.\n"
            "It used to activate a middleware that allowed every origin.\n"
            "Use one of:\n"
            "  config.development_settings  (local development)\n"
            "  config.production_settings   (deployment)\n"
            "or leave DJANGO_SETTINGS_MODULE unset to get config.settings."
        )


_reject_deprecated_settings_module()