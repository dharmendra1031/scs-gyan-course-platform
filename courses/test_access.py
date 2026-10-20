from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Chapter, Course, Enrollment, Lesson, Order


class StudentAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.student = User.objects.create_user(
            username="student_a", email="student_a@example.com", password="ExamplePass123!"
        )
        cls.other = User.objects.create_user(
            username="student_b", email="student_b@example.com", password="ExamplePass123!"
        )
        cls.staff = User.objects.create_user(
            username="content_staff", email="staff@example.com",
            password="ExamplePass123!", is_staff=True,
        )
        for app, model, permission in [
            ("accounts", "user", "change_user"),
            ("accounts", "user", "view_user"),
            ("courses", "enrollment", "add_enrollment"),
            ("courses", "enrollment", "change_enrollment"),
        ]:
            cls.staff.user_permissions.add(Permission.objects.get(
                content_type__app_label=app,
                content_type__model=model,
                codename=permission,
            ))
        category = Category.objects.create(name="Starter", slug="starter")
        cls.course = Course.objects.create(
            category=category, title="Starter Course", slug="starter-course",
            summary="Starter", description="Starter lessons",
            price=Decimal("500.00"), is_published=True,
        )
        chapter = Chapter.objects.create(course=cls.course, title="Chapter 1")
        cls.lesson = Lesson.objects.create(
            chapter=chapter, title="Video Lesson",
            video_url="https://example.com/video/lesson-one",
            is_published=True,
        )
        cls.order = Order.objects.create(
            student=cls.student, course=cls.course, amount=cls.course.price,
        )

    def test_video_requires_active_enrollment(self):
        url = reverse("lesson_video", args=[self.lesson.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).status_code, 404)
        enrollment = Enrollment.objects.create(student=self.student, course=self.course)
        response = self.client.get(url)
        self.assertRedirects(response, self.lesson.video_url, fetch_redirect_response=False)
        self.assertIn("no-store", response.headers["Cache-Control"])
        page = self.client.get(reverse("lesson_detail", args=[self.lesson.pk]))
        self.assertNotContains(page, self.lesson.video_url)
        self.assertContains(page, url)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        enrollment.is_active = False
        enrollment.save(update_fields=["is_active"])
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_video_requires_published_content(self):
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.force_login(self.student)
        url = reverse("lesson_video", args=[self.lesson.pk])
        self.lesson.is_published = False
        self.lesson.save(update_fields=["is_published"])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.lesson.is_published = True
        self.lesson.save(update_fields=["is_published"])
        self.course.is_published = False
        self.course.save(update_fields=["is_published"])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_payment_confirmation_private_and_only_for_paid_order(self):
        url = reverse("course_payment_receipt", args=[self.order.pk])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.order.status = Order.Status.PAID
        self.order.gateway_payment_id = "pay_example"
        self.order.verified_at = timezone.now()
        self.order.save(update_fields=["status", "gateway_payment_id", "verified_at"])
        response = self.client.get(url)
        self.assertContains(response, "Payment acknowledgement")
        self.assertContains(response, "pay_example")
        self.assertContains(response, "not a GST tax invoice")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_manual_approval_not_mislabeled_online_payment(self):
        self.order.status = Order.Status.PAID
        self.order.save(update_fields=["status"])
        self.client.force_login(self.student)
        response = self.client.get(reverse("course_payment_receipt", args=[self.order.pk]))
        self.assertContains(response, "Enrollment confirmation")
        self.assertContains(response, "approved manually")
        self.assertNotContains(response, "Payment acknowledgement")

    def test_staff_permissions_cannot_grant_courses_or_promote_users(self):
        self.client.force_login(self.staff)
        self.assertEqual(
            self.client.get(reverse("admin:accounts_user_change", args=[self.student.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse("admin:courses_enrollment_add")).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(reverse("admin:courses_enrollment_add"), {
                "student": self.student.pk, "course": self.course.pk, "is_active": "on",
            }).status_code,
            403,
        )
        self.assertFalse(Enrollment.objects.filter(student=self.student).exists())
