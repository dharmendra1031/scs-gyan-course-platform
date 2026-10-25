from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import StudentNotification
from .models import (
    Category, Chapter, Course, CourseCertificate, Enrollment, Lesson, LessonProgress,
)


class CertificateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.student = User.objects.create_user(
            username="graduate", email="graduate@example.com", password="SafePassword123!"
        )
        cls.other = User.objects.create_user(
            username="visitor", email="visitor@example.com", password="SafePassword123!"
        )
        category = Category.objects.create(name="Certificates", slug="certificates")
        cls.course = Course.objects.create(
            category=category, title="Certificate Course", slug="certificate-course",
            summary="Foundation", description="Complete the lessons",
            is_published=True, price=Decimal("0.00"),
        )
        chapter = Chapter.objects.create(course=cls.course, title="Module One")
        cls.first = Lesson.objects.create(
            chapter=chapter, title="Part 1", is_published=True,
        )
        cls.second = Lesson.objects.create(
            chapter=chapter, title="Part 2", is_published=True,
        )
        Lesson.objects.create(chapter=chapter, title="Draft part", is_published=False)
        cls.enrollment = Enrollment.objects.create(
            student=cls.student, course=cls.course,
        )

    def test_certificate_requires_all_published_lessons(self):
        self.client.force_login(self.student)
        request_url = reverse("course_certificate_request", args=[self.course.slug])
        self.assertEqual(self.client.get(request_url).status_code, 405)
        self.client.post(reverse("lesson_complete", args=[self.first.pk]))
        self.assertFalse(CourseCertificate.objects.exists())
        self.assertRedirects(
            self.client.post(request_url),
            reverse("course_learn", args=[self.course.slug]),
        )
        self.client.post(reverse("lesson_complete", args=[self.second.pk]))
        certificate = CourseCertificate.objects.get(enrollment=self.enrollment)
        self.assertRedirects(
            self.client.post(request_url),
            reverse("course_certificate", args=[certificate.pk]),
        )
        self.client.post(reverse("lesson_complete", args=[self.second.pk]))
        self.assertEqual(CourseCertificate.objects.count(), 1)
        self.assertEqual(
            StudentNotification.objects.filter(
                student=self.student, event_key=f"certificate-{certificate.pk}",
            ).count(), 1,
        )

    def test_download_is_private_and_is_valid_pdf(self):
        LessonProgress.objects.create(enrollment=self.enrollment, lesson=self.first)
        self.client.force_login(self.student)
        self.client.post(reverse("lesson_complete", args=[self.second.pk]))
        cert = CourseCertificate.objects.get(enrollment=self.enrollment)
        url = reverse("course_certificate", args=[cert.pk])
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.student)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("no-store", response["Cache-Control"])
        Enrollment.objects.filter(pk=self.enrollment.pk).update(is_active=False)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_unenrolled_student_cannot_issue_certificate(self):
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post(
                reverse("course_certificate_request", args=[self.course.slug]),
            ).status_code,
            404,
        )

    def test_empty_course_never_generates_certificate(self):
        category = self.course.category
        empty_course = Course.objects.create(
            category=category, title="No Lessons", slug="no-lessons",
            summary="Empty", description="Empty",
            price=Decimal("0.00"), is_published=True,
        )
        Enrollment.objects.create(student=self.student, course=empty_course)
        self.client.force_login(self.student)
        self.assertRedirects(
            self.client.post(
                reverse("course_certificate_request", args=[empty_course.slug]),
            ),
            reverse("course_learn", args=[empty_course.slug]),
        )
        self.assertFalse(CourseCertificate.objects.filter(
            enrollment__course=empty_course,
        ).exists())
