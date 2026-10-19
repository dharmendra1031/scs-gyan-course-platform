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


class EnrollmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth import get_user_model
        from .models import Chapter, Lesson

        cls.user = get_user_model().objects.create_user(
            username="buyer", email="buyer@example.com", password="SafePassword123!"
        )
        cls.other_user = get_user_model().objects.create_user(
            username="other", email="other@example.com", password="SafePassword123!"
        )
        cls.category = Category.objects.create(name="Exams", slug="exams")
        cls.course = Course.objects.create(
            category=cls.category, title="Exam Course", slug="exam-course",
            summary="Exam guide", description="Learn exams", price=Decimal("599.00"), is_published=True,
        )
        chapter = Chapter.objects.create(course=cls.course, title="Introduction")
        cls.lesson = Lesson.objects.create(chapter=chapter, title="Getting Started", is_published=True)

    def test_post_only_enrollment(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("course_enroll", args=[self.course.slug])).status_code, 405)

    def test_paid_course_requires_manual_approval(self):
        from .models import Enrollment, Order
        from .services import approve_order

        self.client.force_login(self.user)
        for _ in range(2):
            self.assertRedirects(self.client.post(reverse("course_enroll", args=[self.course.slug])), reverse("dashboard"))
        self.assertFalse(Enrollment.objects.filter(student=self.user, course=self.course).exists())
        order = Order.objects.get(student=self.user, course=self.course)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.amount, Decimal("599.00"))
        self.assertEqual(self.client.get(reverse("course_learn", args=[self.course.slug])).status_code, 404)

        approve_order(order.pk)
        approve_order(order.pk)
        self.assertEqual(Enrollment.objects.filter(student=self.user, course=self.course).count(), 1)
        self.assertEqual(self.client.get(reverse("course_learn", args=[self.course.slug])).status_code, 200)

    def test_free_course_enrollment_is_idempotent(self):
        from .models import Enrollment

        self.course.price = Decimal("0")
        self.course.save(update_fields=["price"])
        self.client.force_login(self.user)
        for _ in range(2):
            self.assertRedirects(
                self.client.post(reverse("course_enroll", args=[self.course.slug])),
                reverse("course_learn", args=[self.course.slug]),
            )
        self.assertEqual(Enrollment.objects.filter(student=self.user, course=self.course).count(), 1)

    def test_only_active_enrolled_students_can_view_lessons(self):
        from .models import Enrollment

        url = reverse("lesson_detail", args=[self.lesson.id])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 404)
        enrollment = Enrollment.objects.create(student=self.user, course=self.course)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(url).status_code, 404)
        enrollment.is_active = False
        enrollment.save(update_fields=["is_active"])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_lesson_completion_is_idempotent(self):
        from .models import Enrollment, LessonProgress

        enrollment = Enrollment.objects.create(student=self.user, course=self.course)
        self.client.force_login(self.user)
        for _ in range(2):
            self.assertRedirects(
                self.client.post(reverse("lesson_complete", args=[self.lesson.id])),
                reverse("course_learn", args=[self.course.slug]),
            )
        self.assertEqual(LessonProgress.objects.filter(enrollment=enrollment, lesson=self.lesson).count(), 1)
        self.assertContains(self.client.get(reverse("dashboard")), "1 of 1 lessons completed")

    def test_notes_are_not_public(self):
        from .models import Enrollment

        notes_url = reverse("lesson_notes", args=[self.lesson.pk])
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(notes_url).status_code, 404)
        Enrollment.objects.create(student=self.user, course=self.course)
        self.assertEqual(self.client.get(notes_url).status_code, 404)

    def test_draft_course_and_lesson_are_not_accessible(self):
        from .models import Enrollment

        Enrollment.objects.create(student=self.user, course=self.course)
        self.client.force_login(self.user)
        self.lesson.is_published = False
        self.lesson.save(update_fields=["is_published"])
        self.assertEqual(self.client.get(reverse("lesson_detail", args=[self.lesson.pk])).status_code, 404)
        self.lesson.is_published = True
        self.lesson.save(update_fields=["is_published"])
        self.course.is_published = False
        self.course.save(update_fields=["is_published"])
        self.assertEqual(self.client.get(reverse("course_learn", args=[self.course.slug])).status_code, 404)
        self.assertEqual(self.client.get(reverse("lesson_detail", args=[self.lesson.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("course_enroll", args=[self.course.slug])).status_code, 404)

    def test_cancelled_order_cannot_be_approved(self):
        from .models import Order
        from .services import approve_order

        order = Order.objects.create(student=self.user, course=self.course, amount=self.course.price, status=Order.Status.CANCELLED)
        with self.assertRaises(ValueError):
            approve_order(order.pk)
        self.assertFalse(self.user.enrollments.exists())
