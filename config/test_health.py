from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse


class ReadinessTests(TestCase):
    def test_db_ready(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
        self.assertIn("no-store", response.headers["Cache-Control"])

    @patch("config.health.connection.cursor", side_effect=OperationalError("private host secret"))
    def test_db_unavailable_returns_generic_response(self, cursor):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(response.content, {"status": "unavailable"})
        self.assertNotIn(b"private host secret", response.content)

    def test_post_does_not_probe_database(self):
        self.assertEqual(self.client.post(reverse("health_check")).status_code, 405)
