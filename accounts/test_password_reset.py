import re
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


class PasswordRecoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="recovery_student", email="recovery@example.com",
            password="OldPassword123!safe",
        )

    @override_settings(PASSWORD_RESET_ENABLED=False)
    def test_recovery_is_hidden_and_unavailable_without_email_setup(self):
        self.assertNotContains(self.client.get(reverse("login")), "Forgot password?")
        url = reverse("password_reset")
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"email": self.user.email}).status_code, 404)

    @override_settings(
        PASSWORD_RESET_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_recovery_email_token_and_password_change(self):
        url = reverse("password_reset")
        self.assertContains(self.client.get(reverse("login")), "Forgot password?")
        response = self.client.post(url, {"email": self.user.email}, follow=True)
        self.assertEqual(response.redirect_chain, [(reverse("password_reset_done"), 302)])
        self.assertContains(response, "Check your inbox")
        self.assertEqual(len(mail.outbox), 1)
        link = re.search(r"https?://[^\s]+", mail.outbox[0].body)
        self.assertIsNotNone(link)
        confirmation = self.client.get(urlsplit(link.group(0)).path, follow=True)
        self.assertContains(confirmation, "Choose a new password")
        response = self.client.post(confirmation.request["PATH_INFO"], {
            "new_password1": "UpdatedPassword123!safe",
            "new_password2": "UpdatedPassword123!safe",
        }, follow=True)
        self.assertContains(response, "Password updated")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("UpdatedPassword123!safe"))

    @override_settings(
        PASSWORD_RESET_ENABLED=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_unknown_email_gets_generic_response(self):
        response = self.client.post(reverse("password_reset"), {
            "email": "missing@example.com",
        }, follow=True)
        self.assertContains(response, "If an active account")
        self.assertEqual(len(mail.outbox), 0)
