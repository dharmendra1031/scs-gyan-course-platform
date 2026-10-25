from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Category, Course, Enrollment
from pages.models import ContactEnquiry


class ManagementDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_superuser(
            username="portal-owner", email="portal-owner@example.com", password="SecurePassword123!"
        )
        cls.student = User.objects.create_user(
            username="course-student", email="course-student@example.com", password="SecurePassword123!"
        )
        category = Category.objects.create(name="Preparation", slug="preparation")
        cls.course = Course.objects.create(
            category=category, title="Preparation Basics", slug="preparation-basics",
            summary="Preparation foundations", description="First lessons",
            price=0, is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)
        cls.enquiry = ContactEnquiry.objects.create(
            name="New Student", email="new@example.com",
            subject="Enrollment help", message="I need help choosing a course.",
        )

    def test_only_owner_can_view_student_detail_and_enquiry(self):
        paths = [
            reverse("management:student_detail", args=[self.student.pk]),
            reverse("management:enquiry_detail", args=[self.enquiry.pk]),
        ]
        for path in paths:
            self.assertRedirects(self.client.get(path), f"/account/login/?next={path}")
            self.client.force_login(self.student)
            self.assertEqual(self.client.get(path).status_code, 403)
            self.client.logout()
            self.client.force_login(self.owner)
            self.assertEqual(self.client.get(path).status_code, 200)
            self.client.logout()

    def test_student_detail_read_only_and_restricted_to_students(self):
        self.client.force_login(self.owner)
        detail = reverse("management:student_detail", args=[self.student.pk])
        self.assertContains(self.client.get(detail), "Preparation Basics")
        self.assertEqual(self.client.post(detail, {"is_superuser": "on"}).status_code, 200)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_superuser)
        self.assertEqual(self.client.get(reverse("management:student_detail", args=[self.owner.pk])).status_code, 404)

    def test_enquiry_status_and_follow_up_save(self):
        self.client.force_login(self.owner)
        url = reverse("management:enquiry_detail", args=[self.enquiry.pk])
        self.assertContains(self.client.get(url), "Save follow-up")
        date = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(url, {
            "status": "in_progress",
            "follow_up_at": date,
            "internal_notes": "Call during office hours.",
        })
        self.assertRedirects(response, url)
        self.enquiry.refresh_from_db()
        self.assertEqual(self.enquiry.status, ContactEnquiry.Status.IN_PROGRESS)
        self.assertEqual(self.enquiry.internal_notes, "Call during office hours.")
        self.assertIsNotNone(self.enquiry.follow_up_at)
        self.assertContains(self.client.get(reverse("management:enquiries") + "?status=in_progress"), "Enrollment help")
        self.assertNotContains(self.client.get(reverse("management:enquiries") + "?status=resolved"), "Enrollment help")

    def test_invalid_enquiry_status_does_not_save(self):
        self.client.force_login(self.owner)
        url = reverse("management:enquiry_detail", args=[self.enquiry.pk])
        self.assertContains(self.client.post(url, {"status": "unknown"}), "valid choice")
        self.enquiry.refresh_from_db()
        self.assertEqual(self.enquiry.status, ContactEnquiry.Status.NEW)

    def test_student_cannot_change_enquiry(self):
        self.client.force_login(self.student)
        url = reverse("management:enquiry_detail", args=[self.enquiry.pk])
        self.assertEqual(self.client.post(url, {
            "status": "resolved", "internal_notes": "Unauthorised",
        }).status_code, 403)
        self.enquiry.refresh_from_db()
        self.assertEqual(self.enquiry.status, ContactEnquiry.Status.NEW)
