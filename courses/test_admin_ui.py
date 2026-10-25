from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Chapter, Course, Lesson, StudyMaterial


class ContentManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_superuser(
            username="contentowner", email="contentowner@example.com",
            password="OwnerPassword123!",
        )
        cls.category = Category.objects.create(name="Public Policy", slug="public-policy")
        cls.course = Course.objects.create(
            category=cls.category, title="Policy Foundations",
            slug="policy-foundations", summary="Structured preparation",
            description="Course details", price=Decimal("299.00"), is_published=True,
        )
        chapter = Chapter.objects.create(course=cls.course, title="Unit One")
        Lesson.objects.create(chapter=chapter, title="Public lesson", is_published=True)
        Lesson.objects.create(chapter=chapter, title="Draft lesson", is_published=False)
        StudyMaterial.objects.create(
            course=cls.course, title="Governance PDF",
            file="course-materials/sample.pdf", is_published=True,
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_course_list_and_editor_load(self):
        self.assertContains(
            self.client.get(reverse("management:list", args=["courses"])),
            "Policy Foundations",
        )
        page = self.client.get(reverse("management:edit", args=["courses", self.course.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Learning outcomes")
        self.assertContains(page, "SEO title")

    def test_lesson_and_material_search(self):
        url = reverse("management:list", args=["lessons"])
        result = self.client.get(url, {"q": "Public lesson"})
        self.assertContains(result, "Public lesson")
        self.assertNotContains(result, "Draft lesson")
        page = self.client.get(
            reverse("management:list", args=["materials"]), {"q": "Governance PDF"}
        )
        self.assertContains(page, "Governance PDF")

    def test_course_create_and_edit(self):
        url = reverse("management:create", args=["courses"])
        payload = {
            "category": self.category.pk,
            "title": "New policy workshop", "slug": "",
            "summary": "New workshop", "description": "Study together",
            "mode": "recorded", "price": "0.00",
        }
        self.assertRedirects(self.client.post(url, payload),
                             reverse("management:list", args=["courses"]))
        course = Course.objects.get(title="New policy workshop")
        self.assertEqual(course.slug, "new-policy-workshop")
        payload["title"] = "Updated workshop"
        payload["slug"] = "new-policy-workshop"
        self.assertRedirects(
            self.client.post(reverse("management:edit", args=["courses", course.pk]), payload),
            reverse("management:list", args=["courses"]),
        )
        course.refresh_from_db()
        self.assertEqual(course.title, "Updated workshop")

    def test_missing_and_unknown_resources_are_not_exposed(self):
        self.assertEqual(self.client.get(reverse("management:list", args=["orders"])).status_code, 404)
        self.assertEqual(
            self.client.get(reverse("management:edit", args=["courses", 999999])).status_code,
            404,
        )
