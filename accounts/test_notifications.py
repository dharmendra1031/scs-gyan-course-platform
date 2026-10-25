from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import StudentNotification
from .notifications import notify


class NotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.first = User.objects.create_user(
            username="notifyuser", email="notify@example.com",
            password="ExamplePassword123!",
        )
        cls.second = User.objects.create_user(
            username="othernotify", email="othernotify@example.com",
            password="ExamplePassword123!",
        )

    def test_inbox_requires_login_and_is_private(self):
        notice, created = notify(
            self.first, "enrolled-course-10", "Course enrolled",
            "Your course is available.",
        )
        self.assertTrue(created)
        url = reverse("notification_inbox")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")
        self.client.force_login(self.second)
        self.assertNotContains(self.client.get(url), "Your course is available.")
        self.assertEqual(
            self.client.post(reverse("notification_read", args=[notice.pk])).status_code,
            404,
        )
        self.client.force_login(self.first)
        response = self.client.get(url)
        self.assertContains(response, "Your course is available.")
        self.assertIn("no-store", response["Cache-Control"])

    def test_mark_read_post_only_and_deduplicate(self):
        notice, _ = notify(self.first, "event-42", "Update", "Course update")
        notify(self.first, "event-42", "Update", "Course update")
        self.assertEqual(StudentNotification.objects.count(), 1)
        self.client.force_login(self.first)
        endpoint = reverse("notification_read", args=[notice.pk])
        self.assertEqual(self.client.get(endpoint).status_code, 405)
        self.assertRedirects(self.client.post(endpoint), reverse("notification_inbox"))
        notice.refresh_from_db()
        self.assertIsNotNone(notice.read_at)
        self.client.post(endpoint)
        self.assertEqual(StudentNotification.objects.count(), 1)
