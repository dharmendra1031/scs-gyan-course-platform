from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Category, Course, Enrollment
from .models import Assessment, Attempt


class StudentHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.student = User.objects.create_user(
            username="historystudent", email="historystudent@example.com",
            password="StrongPassword123!",
        )
        cls.other = User.objects.create_user(
            username="historyother", email="historyother@example.com",
            password="StrongPassword123!",
        )
        category = Category.objects.create(name="History", slug="history")
        cls.course = Course.objects.create(
            category=category, title="History Course", slug="history-course",
            summary="Exam history", description="Exam results",
            price=Decimal("0.00"), is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)
        cls.assessment = Assessment.objects.create(
            course=cls.course, title="Finished Practice",
            is_published=True, duration_minutes=15,
        )
        Attempt.objects.create(
            assessment=cls.assessment, student=cls.student,
            submitted_at=timezone.now(), score=7, total_marks=10,
        )

    def test_history_requires_login_and_shows_only_own_submissions(self):
        url = reverse("exam_history")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(url), "Finished Practice")
        self.client.force_login(self.student)
        response = self.client.get(url)
        self.assertContains(response, "Finished Practice")
        self.assertContains(response, "70%")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertContains(
            self.client.get(reverse("dashboard")), "View My Test History",
        )

    def test_unsubmitted_and_revoked_attempts_hidden(self):
        extra = Assessment.objects.create(
            course=self.course, title="Incomplete Practice",
        )
        Attempt.objects.create(assessment=extra, student=self.student)
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get(reverse("exam_history")), "Incomplete Practice")
        Enrollment.objects.filter(student=self.student, course=self.course).update(is_active=False)
        self.assertNotContains(self.client.get(reverse("exam_history")), "Finished Practice")

    def test_history_is_paginated(self):
        for i in range(18):
            assessment = Assessment.objects.create(
                course=self.course, title=f"Practice {i}", duration_minutes=15,
            )
            Attempt.objects.create(
                assessment=assessment, student=self.student,
                submitted_at=timezone.now(), score=1, total_marks=2,
            )
        self.client.force_login(self.student)
        response = self.client.get(reverse("exam_history"))
        self.assertEqual(len(response.context["page"]), 15)
        next_page = self.client.get(reverse("exam_history"), {"page": 2})
        self.assertEqual(len(next_page.context["page"]), 4)
