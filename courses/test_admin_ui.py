from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Chapter, Course, Lesson, StudyMaterial


class ContentAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        admin = get_user_model().objects.create_superuser(
            username="contentadmin", email="contentadmin@example.com",
            password="AdminPassphrase123!",
        )
        cls.admin = admin
        cat = Category.objects.create(name="Public Policy", slug="public-policy")
        cls.course = Course.objects.create(
            category=cat, title="Policy Foundations", slug="policy-foundations",
            summary="Structured preparation", description="Course details",
            price=Decimal("299.00"), is_published=True,
        )
        chapter = Chapter.objects.create(course=cls.course, title="Unit One")
        Lesson.objects.create(chapter=chapter, title="Public lesson", is_published=True)
        Lesson.objects.create(chapter=chapter, title="Draft lesson", is_published=False)
        StudyMaterial.objects.create(
            course=cls.course, title="Governance PDF",
            file="course-materials/sample.pdf", is_published=True,
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_course_admin_displays_published_lesson_count(self):
        response = self.client.get(reverse("admin:courses_course_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published lessons")
        result = next(
            entry for entry in response.context["cl"].result_list
            if entry.pk == self.course.pk
        )
        self.assertEqual(result._published_lessons, 1)

    def test_admin_edit_form_groups_fields(self):
        response = self.client.get(reverse("admin:courses_course_change", args=[self.course.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Learning information")
        self.assertContains(response, "Search appearance")

    def test_admin_lesson_and_study_material_search(self):
        lessons = self.client.get(
            reverse("admin:courses_lesson_changelist"), {"q": "Public lesson"},
        )
        self.assertContains(lessons, "Public lesson")
        self.assertNotContains(lessons, "Draft lesson")
        materials = self.client.get(
            reverse("admin:courses_studymaterial_changelist"), {"q": "Governance PDF"},
        )
        self.assertContains(materials, "Governance PDF")
