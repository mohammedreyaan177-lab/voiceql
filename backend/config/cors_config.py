from __future__ import annotations
import os
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

#Only these four are allowed. No wildcard ports, no other hosts.
DEV_ALLOWED_ORIGINS = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

PLACEHOLDER_PRODUCTION_ORIGINS = ("https://app.example.com",)

PRODUCTION_ORIGINS_ENV_VAR = "VOICEQL_CORS_ALLOWED_ORIGINS"

NULL_ORIGIN_ENV_VAR = "VOICEQL_CORS_ALLOW_NULL_ORIGIN"


# --------------------------------------------------------------------------- #
# Methods and headers
# --------------------------------------------------------------------------- #

CORS_ALLOW_METHODS = ("GET", "POST", "OPTIONS")

CORS_ALLOW_HEADERS = ("accept", "content-type", "origin", "x-requested-with")

CORS_PREFLIGHT_MAX_AGE = 600


def allow_null_origin() -> bool:
    """Return True only if ``null`` origins were explicitly opted into."""
    return os.environ.get(NULL_ORIGIN_ENV_VAR, "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


# --------------------------------------------------------------------------- #
# Production origin validation
# --------------------------------------------------------------------------- #


def validate_production_origins(raw: str) -> tuple[str, ...]:
    if raw is None or not raw.strip():
        raise ImproperlyConfigured(
            f"{PRODUCTION_ORIGINS_ENV_VAR} is not set. "
            "Production requires an explicit allowlist of HTTPS frontend "
            f"origins. Example: {PRODUCTION_ORIGINS_ENV_VAR}="
            '"https://app.your-company.com". Do not use a wildcard.'
        )

    candidates = [part.strip() for part in raw.split(",")]
    origins: list[str] = []
    problems: list[str] = []

    for origin in candidates:
        if not origin:
            # Tolerate a stray trailing comma, but say nothing about it.
            continue

        if origin == "*":
            problems.append(
                "'*' is a wildcard origin and is never allowed; list each "
                "origin explicitly instead"
            )
            continue

        if origin == "null":
            problems.append(
                "'null' cannot be attributed to a specific site and is not "
                f"allowed here; if you truly need it set {NULL_ORIGIN_ENV_VAR}"
            )
            continue

        try:
            parsed = urlsplit(origin)
        except ValueError:
            problems.append(f"{origin!r} is not a parsable URL")
            continue

        if parsed.scheme == "" or parsed.netloc == "":
            problems.append(
                f"{origin!r} is missing a scheme or a host "
                "(expected something like https://app.example.com)"
            )
            continue

        if parsed.scheme != "https":
            problems.append(
                f"{origin!r} uses {parsed.scheme!r}; production origins must "
                "use https"
            )
            continue

        if parsed.path not in ("", "/"):
            problems.append(
                f"{origin!r} contains a path; an origin is scheme + host + "
                "port only"
            )
            continue

        if parsed.query or parsed.fragment:
            problems.append(
                f"{origin!r} contains a query string or fragment, which are "
                "not part of an origin"
            )
            continue

        if "@" in parsed.netloc:
            problems.append(
                f"{origin!r} embeds credentials in the host; CORS origins must "
                "not carry a username or password"
            )
            continue

        if parsed.port is not None and parsed.port not in (443,):
            problems.append(
                f"{origin!r} uses a non-standard port {parsed.port}; production "
                "origins are expected on the default HTTPS port 443"
            )
            continue

        normalised = f"{parsed.scheme}://{parsed.netloc}"

        if normalised in PLACEHOLDER_PRODUCTION_ORIGINS:
            problems.append(
                f"{normalised!r} is the documented placeholder, not a real "
                "domain. Replace it with your actual frontend origin before "
                "deploying."
            )
            continue

        if normalised not in origins:
            origins.append(normalised)

    if problems:
        raise ImproperlyConfigured(
            f"{PRODUCTION_ORIGINS_ENV_VAR} is invalid:\n  - "
            + "\n  - ".join(problems)
        )

    if not origins:
        raise ImproperlyConfigured(
            f"{PRODUCTION_ORIGINS_ENV_VAR} did not contain any usable origin."
        )

    return tuple(origins)


def production_allowed_origins() -> tuple[str, ...]:
    return validate_production_origins(
        os.environ.get(PRODUCTION_ORIGINS_ENV_VAR, "")
    )