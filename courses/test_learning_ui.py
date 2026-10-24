from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Chapter, Course, Enrollment, Lesson, LessonProgress


class LearningUiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = get_user_model().objects.create_user(
            username="learningui", email="learningui@example.com",
            password="Password123!strong",
        )
        category = Category.objects.create(name="UI Learning", slug="ui-learning")
        cls.course = Course.objects.create(
            category=category, title="Learning Course", slug="learning-course",
            summary="Learning", description="Practice", price=Decimal("0"),
            is_published=True,
        )
        chapter = Chapter.objects.create(course=cls.course, title="Chapter One", position=1)
        cls.first = Lesson.objects.create(
            chapter=chapter, title="First Lesson", position=1, is_published=True,
        )
        cls.second = Lesson.objects.create(
            chapter=chapter, title="Second Lesson", position=2, is_published=True,
        )
        cls.draft = Lesson.objects.create(
            chapter=chapter, title="Unpublished Lesson", position=3, is_published=False,
        )
        cls.enrollment = Enrollment.objects.create(student=cls.student, course=cls.course)

    def test_progress_and_next_lesson_follow_completion(self):
        self.client.force_login(self.student)
        url = reverse("course_learn", args=[self.course.slug])
        page = self.client.get(url)
        self.assertContains(page, "0 of 2 published lessons")
        self.assertContains(page, "Continue: First Lesson")
        self.assertNotContains(page, "Unpublished Lesson")
        LessonProgress.objects.create(enrollment=self.enrollment, lesson=self.first)
        next_page = self.client.get(url)
        self.assertContains(next_page, "1 of 2 published lessons")
        self.assertContains(next_page, "Continue: Second Lesson")
        self.assertContains(next_page, "✓ Completed")
        LessonProgress.objects.create(enrollment=self.enrollment, lesson=self.second)
        last_page = self.client.get(url)
        self.assertContains(last_page, "all currently published lessons")
        self.assertNotContains(last_page, "Continue: First Lesson")

    def test_lesson_previous_next_are_ordered_and_private(self):
        self.client.force_login(self.student)
        first = self.client.get(reverse("lesson_detail", args=[self.first.pk]))
        self.assertContains(first, "Next lesson")
        self.assertNotContains(first, "Previous lesson")
        second = self.client.get(reverse("lesson_detail", args=[self.second.pk]))
        self.assertContains(second, "Previous lesson")
        self.assertNotContains(second, "Next lesson")
        self.assertNotContains(second, "Unpublished Lesson")
        self.client.logout()
        self.assertEqual(self.client.get(reverse("lesson_detail", args=[self.second.pk])).status_code, 302)

    def test_progress_ignores_draft_completion(self):
        self.client.force_login(self.student)
        LessonProgress.objects.create(enrollment=self.enrollment, lesson=self.draft)
        page = self.client.get(reverse("course_learn", args=[self.course.slug]))
        self.assertContains(page, "0 of 2 published lessons")
