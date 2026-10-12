"""
CORS security tests for the VoiceQL configuration.

These tests use Django's test client, so no network calls and no real database
mutations occur.

They deliberately assert on **response headers**, not just status codes. An
unapproved preflight request can return HTTP 200 and still correctly withhold
``Access-Control-Allow-Origin``; a test that only checked the status code would
report a false pass.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings

from config import cors_config


ALLOWED = "http://localhost:8000"
UNAPPROVED = "http://evil.example.com"

PREFLIGHT = {
    "HTTP_ACCESS_CONTROL_REQUEST_METHOD": "POST",
    "HTTP_ACCESS_CONTROL_REQUEST_HEADERS": "content-type",
}


class CorsMiddlewareIsTheOnlyImplementationTests(TestCase):
    """Requirement 10: the intended middleware is actually loaded."""

    def test_corsheaders_middleware_is_first(self):
        self.assertEqual(
            settings.MIDDLEWARE[0],
            "corsheaders.middleware.CorsMiddleware",
        )

    def test_corsheaders_middleware_precedes_common_middleware(self):
        cors = settings.MIDDLEWARE.index("corsheaders.middleware.CorsMiddleware")
        common = settings.MIDDLEWARE.index("django.middleware.common.CommonMiddleware")
        self.assertLess(cors, common)

    def test_corsheaders_app_is_installed(self):
        self.assertIn("corsheaders", settings.INSTALLED_APPS)

    def test_custom_wildcard_middleware_is_not_in_the_stack(self):
        for entry in settings.MIDDLEWARE:
            self.assertNotIn("config.cors", entry)

    def test_csrf_middleware_is_still_enabled(self):
        # CORS must never be "fixed" by disabling CSRF.
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware",
            settings.MIDDLEWARE,
        )

    def test_wildcard_mode_is_off(self):
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)

    def test_no_regex_origin_allowlist(self):
        self.assertEqual(list(settings.CORS_ALLOWED_ORIGIN_REGEXES), [])

    def test_credentials_are_disabled(self):
        # The frontend uses credentials:"omit", so this must stay False.
        self.assertFalse(settings.CORS_ALLOW_CREDENTIALS)

    def test_deprecated_custom_middleware_raises_if_used(self):
        from config.cors import CorsMiddleware as RemovedMiddleware

        with self.assertRaises(RuntimeError):
            RemovedMiddleware(lambda request: None)

    def test_deprecated_settings_module_is_rejected(self):
        with mock.patch.dict(
            "os.environ", {"DJANGO_SETTINGS_MODULE": "config.cors_settings"}
        ):
            with self.assertRaises(RuntimeError):
                import config  # noqa: F401
                import importlib

                importlib.reload(config)


@override_settings(
    CORS_ALLOWED_ORIGINS=[ALLOWED, "http://127.0.0.1:8000"],
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGIN_REGEXES=[],
)
class SimpleRequestHeaderTests(SimpleTestCase):
    """Requirements 1-6: what the browser sees on ordinary requests."""

    def test_1_approved_origin_is_echoed_back(self):
        response = self.client.get("/", headers={"origin": ALLOWED})

        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"), ALLOWED
        )

    def test_1b_response_varies_on_origin(self):
        # Without Vary: Origin a shared cache could serve one origin's
        # authorised response to a different origin.
        response = self.client.get("/", headers={"origin": ALLOWED})
        self.assertIn("origin", response.headers.get("Vary", "").lower())

    def test_2_unapproved_origin_gets_no_authorisation_header(self):
        response = self.client.get("/", headers={"origin": UNAPPROVED})

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        # And it must not be the wildcard either.
        self.assertNotEqual(
            response.headers.get("Access-Control-Allow-Origin"), "*"
        )

    def test_3_wildcard_is_never_emitted(self):
        for origin in (ALLOWED, UNAPPROVED, "null", "http://127.0.0.1:9999"):
            with self.subTest(origin=origin):
                response = self.client.get("/", headers={"origin": origin})
                self.assertNotEqual(
                    response.headers.get("Access-Control-Allow-Origin"), "*"
                )

    def test_4_null_origin_is_not_authorised(self):
        response = self.client.get("/", headers={"origin": "null"})

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_5_different_port_is_rejected(self):
        response = self.client.get(
            "/", headers={"origin": "http://localhost:9999"}
        )

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_6_unexpected_subdomain_is_rejected(self):
        response = self.client.get(
            "/", headers={"origin": "http://evil.localhost:8000"}
        )

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_6b_scheme_must_match_exactly(self):
        # http://localhost:8000 is allowed; https://localhost:8000 is not.
        rejected = self.client.get(
            "/", headers={"origin": "https://localhost:8000"}
        )
        self.assertIsNone(
            rejected.headers.get("Access-Control-Allow-Origin")
        )

    def test_request_without_origin_gets_no_cors_header(self):
        response = self.client.get("/")

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

    def test_no_allow_credentials_header_when_credentials_disabled(self):
        response = self.client.get("/", headers={"origin": ALLOWED})

        self.assertIsNone(
            response.headers.get("Access-Control-Allow-Credentials")
        )


@override_settings(
    CORS_ALLOWED_ORIGINS=[ALLOWED],
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGIN_REGEXES=[],
    CORS_ALLOW_METHODS=("GET", "POST", "OPTIONS"),
    CORS_ALLOW_HEADERS=("accept", "content-type", "origin", "x-requested-with"),
)
class PreflightTests(SimpleTestCase):
    """Requirements 7-8: preflight behaviour."""

    def test_7_allowed_preflight_returns_only_permitted_methods_and_headers(self):
        response = self.client.options("/", headers={"origin": ALLOWED, **PREFLIGHT})

        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"), ALLOWED
        )
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Methods"),
            "GET, POST, OPTIONS",
        )
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Headers"),
            "accept, content-type, origin, x-requested-with",
        )

    def test_7b_dangerous_methods_are_not_advertised(self):
        response = self.client.options("/", headers={"origin": ALLOWED, **PREFLIGHT})

        advertised = response.headers.get("Access-Control-Allow-Methods", "")
        for method in ("PUT", "PATCH", "DELETE"):
            self.assertNotIn(method, advertised)

    def test_7c_authorization_header_is_not_permitted(self):
        response = self.client.options("/", headers={"origin": ALLOWED, **PREFLIGHT})

        advertised = response.headers.get("Access-Control-Allow-Headers", "")
        self.assertNotIn("authorization", advertised.lower())

    def test_8_unapproved_preflight_is_not_granted_access(self):
        response = self.client.options(
            "/", headers={"origin": UNAPPROVED, **PREFLIGHT}
        )

        # The status code may well be 200; the browser is denied by the
        # *absence* of the header, which is what actually matters.
        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        self.assertIsNone(response.headers.get("Access-Control-Allow-Methods"))

    def test_8b_null_origin_preflight_is_not_granted_access(self):
        response = self.client.options("/", headers={"origin": "null", **PREFLIGHT})

        self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))


class ProductionOriginValidationTests(SimpleTestCase):
    """Requirement 9: production fails safely."""

    def test_valid_https_origin_is_accepted(self):
        result = cors_config.validate_production_origins(
            "https://app.your-company.com"
        )
        self.assertEqual(result, ("https://app.your-company.com",))

    def test_multiple_valid_origins_are_accepted(self):
        result = cors_config.validate_production_origins(
            "https://a.example.org, https://b.example.org"
        )
        self.assertEqual(
            result, ("https://a.example.org", "https://b.example.org")
        )

    def test_missing_configuration_raises(self):
        for raw in ("", "   ", None):
            with self.subTest(raw=raw):
                with self.assertRaises(ImproperlyConfigured):
                    cors_config.validate_production_origins(raw)

    def test_wildcard_is_rejected(self):
        for raw in ("*", "https://ok.example.com,*"):
            with self.subTest(raw=raw):
                with self.assertRaises(ImproperlyConfigured):
                    cors_config.validate_production_origins(raw)

    def test_null_origin_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            cors_config.validate_production_origins("null")

    def test_non_https_scheme_is_rejected(self):
        for raw in (
            "http://app.example.org",
            "ftp://app.example.org",
            "//app.example.org",
            "app.example.org",
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(ImproperlyConfigured):
                    cors_config.validate_production_origins(raw)

    def test_path_query_and_fragment_are_rejected(self):
        for raw in (
            "https://app.example.org/dashboard",
            "https://app.example.org?a=1",
            "https://app.example.org#frag",
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(ImproperlyConfigured):
                    cors_config.validate_production_origins(raw)

    def test_embedded_credentials_are_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            cors_config.validate_production_origins(
                "https://user:pass@app.example.org"
            )

    def test_non_standard_port_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            cors_config.validate_production_origins("https://app.example.org:8443")

    def test_documented_placeholder_is_rejected(self):
        # The placeholder must never be accepted, or a deployment could ship
        # pointing at a domain nobody owns.
        with self.assertRaises(ImproperlyConfigured):
            cors_config.validate_production_origins(
                "https://app.example.com"
            )

    def test_error_message_names_the_offending_value(self):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            cors_config.validate_production_origins("http://insecure.example.org")
        self.assertIn("http://insecure.example.org", str(ctx.exception))


class ProductionSettingsFailSafeTests(SimpleTestCase):
    """
    Requirement 9 (continued): the production settings module itself refuses to
    start.

    These run in a subprocess because the module raises at *import* time. That
    is the behaviour being tested, and doing it in-process would mean reloading
    ``config.settings`` and mutating the module object Django is already using,
    which would corrupt the rest of the test run.
    """

    VALID = {
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": "a-real-production-secret-value",
        "DJANGO_ALLOWED_HOSTS": "api.your-company.com",
        "VOICEQL_CORS_ALLOWED_ORIGINS": "https://app.your-company.com",
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend_dir = str(settings.BASE_DIR)

    def _load_production_settings(self, overrides):
        """
        Import config.production_settings in a clean subprocess.

        Returns (exit_code, combined_output).
        """
        env = dict(os.environ)
        env.update(self.VALID)
        env.update(overrides)
        env["DJANGO_SETTINGS_MODULE"] = "config.production_settings"
        # Keep the Whisper model out of the child process; it is unrelated to
        # settings validation and takes seconds to load.
        env["PYTHONPATH"] = self.backend_dir

        code = (
            "import json;"
            "import config.production_settings as p;"
            "print(json.dumps({"
            "'origins': p.CORS_ALLOWED_ORIGINS,"
            "'allow_all': p.CORS_ALLOW_ALL_ORIGINS,"
            "'credentials': p.CORS_ALLOW_CREDENTIALS,"
            "'debug': p.DEBUG,"
            "'middleware0': p.MIDDLEWARE[0],"
            "'methods': list(p.CORS_ALLOW_METHODS),"
            "'secure_cookies': getattr(p, 'SESSION_COOKIE_SECURE', None),"
            "}))"
        )

        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=self.backend_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        return completed.returncode, completed.stdout + completed.stderr

    def _assert_refuses(self, overrides, expected_fragment):
        code, output = self._load_production_settings(overrides)
        self.assertNotEqual(
            code,
            0,
            msg=f"Expected production settings to refuse to start, but they "
            f"loaded. Output:\n{output}",
        )
        self.assertIn("ImproperlyConfigured", output)
        self.assertIn(expected_fragment, output)

    def test_production_refuses_without_allowed_origins(self):
        self._assert_refuses(
            {"VOICEQL_CORS_ALLOWED_ORIGINS": ""},
            "VOICEQL_CORS_ALLOWED_ORIGINS",
        )

    def test_production_refuses_with_wildcard(self):
        self._assert_refuses(
            {"VOICEQL_CORS_ALLOWED_ORIGINS": "*"},
            "wildcard",
        )

    def test_production_refuses_with_placeholder(self):
        self._assert_refuses(
            {"VOICEQL_CORS_ALLOWED_ORIGINS": "https://app.example.com"},
            "placeholder",
        )

    def test_production_refuses_non_https_origin(self):
        self._assert_refuses(
            {"VOICEQL_CORS_ALLOWED_ORIGINS": "http://app.your-company.com"},
            "https",
        )

    def test_production_refuses_null_origin(self):
        self._assert_refuses(
            {"VOICEQL_CORS_ALLOWED_ORIGINS": "null"},
            "null",
        )

    def test_production_refuses_when_debug_is_true(self):
        self._assert_refuses({"DJANGO_DEBUG": "true"}, "DEBUG must be False")

    def test_production_refuses_with_development_secret_key(self):
        self._assert_refuses(
            {
                "DJANGO_SECRET_KEY": (
                    "django-insecure-$!kp+k7^g-d@t@qlm75sx$e1ho3wu!cg0unfj35"
                    "*j*9h@k5b&l"
                )
            },
            "insecure development default",
        )

    def test_production_refuses_without_allowed_hosts(self):
        self._assert_refuses(
            {"DJANGO_ALLOWED_HOSTS": ""},
            "DJANGO_ALLOWED_HOSTS",
        )

    def test_production_loads_with_a_fully_valid_configuration(self):
        code, output = self._load_production_settings({})

        self.assertEqual(code, 0, msg=f"Expected production settings to load. "
                                       f"Output:\n{output}")

        # The child printed one JSON line; find it.
        payload = json.loads(
            [line for line in output.splitlines() if line.startswith("{")][-1]
        )

        self.assertEqual(
            payload["origins"], ["https://app.your-company.com"]
        )
        self.assertFalse(payload["allow_all"])
        self.assertFalse(payload["credentials"])
        self.assertFalse(payload["debug"])
        self.assertEqual(
            payload["middleware0"], "corsheaders.middleware.CorsMiddleware"
        )
        self.assertEqual(
            set(payload["methods"]), {"GET", "POST", "OPTIONS"}
        )
        self.assertTrue(payload["secure_cookies"])


class DeprecatedSettingsModuleIsRejectedTests(SimpleTestCase):
    """
    Requirement 5: the undocumented shell variable must not change the policy.

    Verifies that selecting the old wildcard settings module now fails loudly
    instead of silently enabling a permissive policy.
    """

    def _import_with(self, selected):
        env = dict(os.environ)
        env["DJANGO_SETTINGS_MODULE"] = selected
        env["PYTHONPATH"] = str(settings.BASE_DIR)

        completed = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            cwd=str(settings.BASE_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        return completed.returncode, completed.stdout + completed.stderr

    def test_deprecated_cors_settings_module_is_rejected(self):
        code, output = self._import_with("config.cors_settings")

        self.assertNotEqual(code, 0, msg=output)
        self.assertIn("deprecated", output)
        self.assertIn("config.development_settings", output)

    def test_cors_module_cannot_be_used_as_settings(self):
        code, output = self._import_with("config.cors")

        self.assertNotEqual(code, 0, msg=output)
        self.assertIn("deprecated", output)


class EntrypointSelectionTests(SimpleTestCase):
    """Requirement 5: the real entry points select the intended module."""

    ENTRYPOINTS = ("manage.py", "config/wsgi.py", "config/asgi.py")

    def _entrypoint_source(self, name):
        path = Path(settings.BASE_DIR) / name
        return path.read_text(encoding="utf-8")

    def test_entrypoints_default_to_base_settings(self):
        for name in self.ENTRYPOINTS:
            with self.subTest(entrypoint=name):
                source = self._entrypoint_source(name)
                self.assertIn(
                    "os.environ.setdefault('DJANGO_SETTINGS_MODULE'",
                    source,
                )
                self.assertIn("config.settings", source)

    def test_entrypoints_do_not_reference_the_removed_middleware(self):
        for name in self.ENTRYPOINTS:
            with self.subTest(entrypoint=name):
                self.assertNotIn(
                    "config.cors.CorsMiddleware",
                    self._entrypoint_source(name),
                )

    def test_only_base_settings_module_owns_the_middleware_stack(self):
        # development/production inherit it via `from .settings import *` and
        # must not redefine it, so there is exactly one middleware definition.
        for name in (
            "development_settings.py",
            "production_settings.py",
            "cors_settings.py",
        ):
            with self.subTest(module=name):
                source = (
                    Path(settings.BASE_DIR) / "config" / name
                ).read_text(encoding="utf-8")
                self.assertNotIn("MIDDLEWARE = [", source)

    def test_base_settings_defines_middleware_once(self):
        source = self._entrypoint_source("config/settings.py")
        self.assertEqual(source.count("MIDDLEWARE = ["), 1)


class DevelopmentAllowlistTests(SimpleTestCase):
    """Requirement 3 (development half): narrow, explicit local allowlist."""

    def test_development_allowlist_is_explicit(self):
        from config.development_settings import CORS_ALLOWED_ORIGINS

        self.assertIn("http://localhost:8000", CORS_ALLOWED_ORIGINS)
        self.assertNotIn("*", CORS_ALLOWED_ORIGINS)
        self.assertNotIn("null", CORS_ALLOWED_ORIGINS)

    def test_development_allowlist_contains_no_wildcard_ports(self):
        from config.development_settings import CORS_ALLOWED_ORIGINS

        # Every origin must name an explicit host and an explicit port, so no
        # entry can mean "any port on this host".
        for origin in CORS_ALLOWED_ORIGINS:
            with self.subTest(origin=origin):
                self.assertTrue(origin.startswith("http://"))
                self.assertIn(":", origin)
                host, _, port = origin[len("http://") :].partition(":")
                self.assertNotIn("*", host)
                self.assertIn(port, {"8000", "5173"})

    def test_development_does_not_disable_csrf(self):
        from config import development_settings as dev

        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware", dev.MIDDLEWARE
        )


class DocsTest(SimpleTestCase):
    """Guard against the policy file drifting from its own documentation."""

    def test_placeholder_origin_is_documented(self):
        self.assertEqual(
            cors_config.PLACEHOLDER_PRODUCTION_ORIGINS,
            ("https://app.example.com",),
        )

    def test_allowed_methods_are_only_what_the_frontend_uses(self):
        self.assertEqual(
            set(cors_config.CORS_ALLOW_METHODS), {"GET", "POST", "OPTIONS"}
        )

    def test_allowed_headers_are_only_what_the_frontend_uses(self):
        self.assertNotIn(
            "authorization", cors_config.CORS_ALLOW_HEADERS
        )
        self.assertNotIn("x-csrftoken", cors_config.CORS_ALLOW_HEADERS)
