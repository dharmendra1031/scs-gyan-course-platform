"""Validate settings and SQL connection before starting IIS staging."""
import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.conf import settings
from django.db import DatabaseError, connections


def issues():
    errors = []
    if settings.DEBUG:
        errors.append("Set DEBUG=False.")
    secret = settings.SECRET_KEY
    if len(secret) < 40 or any(
        token in secret.lower()
        for token in ("replace-with", "local-development", "change-me", "placeholder")
    ):
        errors.append("Use a newly generated unpredictable SECRET_KEY.")
    if not settings.ALLOWED_HOSTS or "*" in settings.ALLOWED_HOSTS or all(
        host in ("localhost", "127.0.0.1") for host in settings.ALLOWED_HOSTS
    ):
        errors.append("Configure a specific staging ALLOWED_HOSTS hostname.")
    if not settings.CSRF_TRUSTED_ORIGINS or any(
        not host.startswith("https://") for host in settings.CSRF_TRUSTED_ORIGINS
    ):
        errors.append("Set a trusted HTTPS CSRF_TRUSTED_ORIGINS host.")
    if not getattr(settings, "SECURE_SSL_REDIRECT", False):
        errors.append("Enable SECURE_SSL_REDIRECT on staging.")
    database = settings.DATABASES["default"]
    if database["ENGINE"] != "mssql":
        errors.append("Use an isolated SQL Server database on staging.")
    if database.get("USER") in ("", "sa"):
        errors.append("Use a dedicated SQL Server application user, not sa.")
    if not database.get("PASSWORD") or "replace-with" in database["PASSWORD"].lower():
        errors.append("Set a real SQL Server password.")
    private_root = Path(settings.PRIVATE_MEDIA_ROOT).resolve()
    for exposed_root in (settings.MEDIA_ROOT, settings.STATIC_ROOT):
        public_root = Path(exposed_root).resolve()
        if private_root == public_root or public_root in private_root.parents:
            errors.append("PRIVATE_MEDIA_ROOT must be outside public storage.")
    return errors


def main():
    problems = issues()
    if problems:
        for problem in problems:
            print("Staging error: " + problem, file=sys.stderr)
        return 1
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        print("Staging error: SQL Server is unavailable.", file=sys.stderr)
        return 1
    print("Staging configuration and database ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
