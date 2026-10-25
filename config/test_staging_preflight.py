from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from scripts import staging_preflight


class StagingConfigurationTests(SimpleTestCase):
    def configuration(self):
        root = Path("/tmp/scs-gyan-test")
        return SimpleNamespace(
            DEBUG=False,
            SECRET_KEY="x" * 60,
            ALLOWED_HOSTS=["staging.example.org"],
            CSRF_TRUSTED_ORIGINS=["https://staging.example.org"],
            SECURE_SSL_REDIRECT=True,
            DATABASES={"default": {
                "ENGINE": "mssql",
                "USER": "staging_user",
                "PASSWORD": "test-only-strong-database-secret",
            }},
            PRIVATE_MEDIA_ROOT=root / "private_files",
            MEDIA_ROOT=root / "public_media",
            STATIC_ROOT=root / "public_static",
        )

    def test_configured_staging_passes(self):
        with patch.object(staging_preflight, "settings", self.configuration()):
            self.assertEqual(staging_preflight.issues(), [])

    def test_placeholder_credentials_and_debug_are_rejected(self):
        settings = self.configuration()
        settings.DEBUG = True
        settings.SECRET_KEY = "replace-with-an-unsafe-placeholder"
        settings.ALLOWED_HOSTS = ["*"]
        settings.CSRF_TRUSTED_ORIGINS = ["http://staging.example.org"]
        settings.DATABASES["default"]["ENGINE"] = "django.db.backends.sqlite3"
        settings.DATABASES["default"]["USER"] = "sa"
        settings.DATABASES["default"]["PASSWORD"] = "replace-with-db-password"
        with patch.object(staging_preflight, "settings", settings):
            self.assertGreaterEqual(len(staging_preflight.issues()), 6)

    def test_private_files_cannot_be_nested_under_public_media(self):
        settings = self.configuration()
        settings.PRIVATE_MEDIA_ROOT = Path(settings.MEDIA_ROOT) / "private"
        with patch.object(staging_preflight, "settings", settings):
            self.assertTrue(any(
                "PRIVATE_MEDIA_ROOT" in error
                for error in staging_preflight.issues()
            ))
