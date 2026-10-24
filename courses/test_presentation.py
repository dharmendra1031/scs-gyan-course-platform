from decimal import Decimal

from django.test import TestCase

from .models import Category, Chapter, Course, Lesson


class CoursePresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Governance", slug="governance")
        cls.course = Course.objects.create(
            category=category, title="Governance Foundations", slug="governance-foundations",
            summary="Understand governance basics", description="Structured syllabus",
            instructor_name="Faculty Demo", learning_outcomes="Understand concepts\nSolve practice sets",
            price=Decimal("0.00"), is_published=True,
        )
        chapter = Chapter.objects.create(course=cls.course, title="Introduction")
        Lesson.objects.create(chapter=chapter, title="Published introduction", is_published=True)
        Lesson.objects.create(chapter=chapter, title="Private unpublished lesson", is_published=False)

    def test_syllabus_and_faculty_are_displayed_without_draft_lessons(self):
        response = self.client.get(self.course.get_absolute_url())
        self.assertContains(response, "Course syllabus")
        self.assertContains(response, "Published introduction")
        self.assertContains(response, "Faculty Demo")
        self.assertContains(response, "Understand concepts")
        self.assertContains(response, "Solve practice sets")
        self.assertNotContains(response, "Private unpublished lesson")
        self.assertContains(response, "Lesson content and PDFs require course enrollment.")

    def test_free_course_has_free_price_not_zero_rupees(self):
        response = self.client.get(self.course.get_absolute_url())
        self.assertContains(response, ">Free</h2>")
        listing = self.client.get("/courses/")
        self.assertContains(listing, ">Free</strong>")
