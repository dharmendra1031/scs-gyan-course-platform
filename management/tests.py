from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from articles.models import Article
from courses.models import Category, Course, Order
from exams.models import Assessment, Attempt, Choice, Question
from pages.models import ContactEnquiry


class ManagementAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        cls.owner = user.objects.create_superuser(
            username="owner", email="owner@scsgyan.example",
            password="OwnerPassword123!",
        )
        cls.staff = user.objects.create_user(
            username="staff", email="staff@scsgyan.example",
            password="StaffPassword123!", is_staff=True,
        )
        cls.student = user.objects.create_user(
            username="student", email="student@scsgyan.example",
            password="StudentPassword123!",
        )
        category = Category.objects.create(name="UPSC", slug="upsc")
        cls.course = Course.objects.create(
            category=category, title="UPSC Essentials", slug="upsc-essentials",
            summary="Learn", description="Preparation", price=Decimal("200.00"),
            is_published=True,
        )
        cls.order = Order.objects.create(
            student=cls.student, course=cls.course, amount=cls.course.price,
        )

    def test_django_admin_route_is_disabled(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)
        self.assertEqual(self.client.get("/admin/login/").status_code, 404)

    def test_anonymous_redirect_and_staff_student_denial(self):
        url = reverse("management:dashboard")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")
        protected = [
            url,
            reverse("management:list", args=["courses"]),
            reverse("management:create", args=["courses"]),
            reverse("management:orders"),
            reverse("management:reports"),
            reverse("management:enquiries"),
            reverse("management:students"),
            reverse("management:results"),
            reverse("management:order_action", args=[self.order.pk, "approve"]),
        ]
        for user in (self.staff, self.student):
            self.client.force_login(user)
            for path in protected:
                with self.subTest(user=user.username, path=path):
                    self.assertEqual(self.client.get(path).status_code, 403)
            self.client.logout()

    def test_owner_can_open_custom_management(self):
        self.client.force_login(self.owner)
        for name in ("dashboard", "orders", "reports", "enquiries", "students", "results"):
            self.assertEqual(self.client.get(reverse("management:" + name)).status_code, 200)
        self.assertContains(self.client.get(reverse("management:dashboard")), "Control Centre")
        self.assertNotContains(self.client.get(reverse("management:dashboard")), "Django administration")

    def test_login_redirects_owner_to_management(self):
        response = self.client.post(reverse("login"), {
            "username": self.owner.username, "password": "OwnerPassword123!",
        })
        self.assertRedirects(response, reverse("management:dashboard"))

    def test_payment_actions_require_post(self):
        self.client.force_login(self.owner)
        url = reverse("management:order_action", args=[self.order.pk, "approve"])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertRedirects(self.client.post(url), reverse("management:orders"))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(
            self.client.get(reverse("management:order_action", args=[self.order.pk, "reconcile"])).status_code,
            405,
        )

    def test_enquiries_and_student_data_are_private(self):
        ContactEnquiry.objects.create(
            name="Visitor", email="visitor@example.org", subject="Course question",
            message="I would like to discuss the course.",
        )
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("management:enquiries")).status_code, 403)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse("management:enquiries")), "visitor@example.org")

    def test_published_test_requires_valid_answer_choices(self):
        self.client.force_login(self.owner)
        assessment = Assessment.objects.create(course=self.course, title="Practice set")
        question = Question.objects.create(assessment=assessment, text="First question?")
        url = reverse("management:edit", args=["assessments", assessment.pk])
        payload = {
            "course": self.course.pk, "title": assessment.title, "kind": "quiz",
            "duration_minutes": "30", "is_published": "on",
        }
        response = self.client.post(url, payload)
        self.assertContains(response, "at least two choices and exactly one correct answer")
        self.assertFalse(Assessment.objects.get(pk=assessment.pk).is_published)
        Choice.objects.create(question=question, text="Yes", is_correct=True)
        Choice.objects.create(question=question, text="No", is_correct=False)
        self.assertRedirects(self.client.post(url, payload),
                             reverse("management:list", args=["assessments"]))
        self.assertTrue(Assessment.objects.get(pk=assessment.pk).is_published)


    def test_published_question_cannot_be_edited_or_moved(self):
        self.client.force_login(self.owner)
        published = Assessment.objects.create(
            course=self.course, title="Live test", is_published=True,
        )
        draft = Assessment.objects.create(course=self.course, title="Draft test")
        question = Question.objects.create(assessment=published, text="Original?", marks=2)
        Choice.objects.create(question=question, text="Yes", is_correct=True)
        Choice.objects.create(question=question, text="No")

        url = reverse("management:edit", args=["questions", question.pk])
        data = {
            "assessment": published.pk, "text": "Changed?", "position": 0,
            "marks": 5, "explanation": "",
        }
        self.assertContains(
            self.client.post(url, data),
            "Unpublish the assessment before editing its questions.",
        )
        data["assessment"] = draft.pk
        self.assertContains(
            self.client.post(url, data),
            "Unpublish the assessment before editing its questions.",
        )
        question.refresh_from_db()
        self.assertEqual(
            (question.assessment_id, question.text, question.marks),
            (published.pk, "Original?", 2),
        )

        create_url = reverse("management:create", args=["questions"])
        self.assertContains(self.client.post(create_url, {
            "assessment": published.pk, "text": "Another?",
            "position": 0, "marks": 1, "explanation": "",
        }), "Unpublish the assessment before editing its questions.")
        self.assertEqual(Question.objects.filter(assessment=published).count(), 1)

        self.assertRedirects(self.client.post(create_url, {
            "assessment": draft.pk, "text": "Draft question",
            "position": 0, "marks": 1, "explanation": "",
        }), reverse("management:list", args=["questions"]))

    def test_published_choice_cannot_be_moved_to_draft(self):
        self.client.force_login(self.owner)
        published = Assessment.objects.create(
            course=self.course, title="Published", is_published=True,
        )
        draft = Assessment.objects.create(course=self.course, title="Draft")
        question = Question.objects.create(assessment=published, text="Published question")
        target = Question.objects.create(assessment=draft, text="Draft question")
        answer = Choice.objects.create(question=question, text="Correct", is_correct=True)
        Choice.objects.create(question=question, text="Wrong")

        url = reverse("management:edit", args=["choices", answer.pk])
        self.assertContains(self.client.post(url, {
            "question": target.pk, "text": "Changed", "is_correct": "on",
        }), "Unpublish the assessment before editing its answers.")
        answer.refresh_from_db()
        self.assertEqual((answer.question_id, answer.text), (question.pk, "Correct"))

    def test_zero_duration_and_started_test_changes_are_blocked(self):
        self.client.force_login(self.owner)
        assessment = Assessment.objects.create(course=self.course, title="Timed test")
        url = reverse("management:edit", args=["assessments", assessment.pk])
        data = {
            "course": self.course.pk, "title": assessment.title,
            "kind": "quiz", "duration_minutes": 0,
        }
        self.assertContains(
            self.client.post(url, data), "Duration must be at least one minute.",
        )
        assessment.refresh_from_db()
        self.assertEqual(assessment.duration_minutes, 30)

        Attempt.objects.create(assessment=assessment, student=self.student)
        data["duration_minutes"] = 60
        self.assertContains(
            self.client.post(url, data),
            "Course, date and duration cannot change after a student starts a test.",
        )
        assessment.refresh_from_db()
        self.assertEqual(assessment.duration_minutes, 30)

    def test_article_editor(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("management:create", args=["articles"])).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("management:list", args=["articles"])).status_code, 200,
        )
