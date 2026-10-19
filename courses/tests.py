from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Course


class CoursePagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="UPSC", slug="upsc")
        cls.course = Course.objects.create(
            category=cls.category,
            title="UPSC Foundation",
            slug="upsc-foundation",
            summary="Learn the foundations.",
            description="A demonstration course.",
            price=Decimal("999.00"),
            is_published=True,
        )

    def test_homepage_shows_published_course(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "UPSC Foundation")

    def test_course_detail_page(self):
        response = self.client.get(self.course.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "UPSC Foundation")

    def test_draft_course_is_not_public(self):
        self.course.is_published = False
        self.course.save()
        self.assertEqual(self.client.get(self.course.get_absolute_url()).status_code, 404)

    def test_search_filter(self):
        response = self.client.get(reverse("course_list"), {"q": "foundation"})
        self.assertContains(response, "UPSC Foundation")
        self.assertEqual(len(response.context["courses"]), 1)
