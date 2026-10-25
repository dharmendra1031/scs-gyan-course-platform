from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from courses.models import Category, Course, Enrollment
from .models import Assessment, Attempt, AttemptAnswer, Choice, Question


class AssessmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.student = User.objects.create_user(
            username="quizstudent", email="quizstudent@example.com", password="SafePassword123!"
        )
        cls.other = User.objects.create_user(
            username="otherquizstudent", email="otherquizstudent@example.com", password="SafePassword123!"
        )
        category = Category.objects.create(name="Mock Exams", slug="mock-exams")
        cls.course = Course.objects.create(
            category=category, title="Exam Preparation", slug="exam-preparation",
            summary="Mock tests", description="Preparation",
            price=Decimal("500.00"), is_published=True,
        )
        cls.assessment = Assessment.objects.create(
            course=cls.course, title="Practice Quiz", kind=Assessment.Kind.QUIZ,
            duration_minutes=30, is_published=True,
        )
        cls.question = Question.objects.create(
            assessment=cls.assessment, text="Which answer is correct?", marks=2,
        )
        cls.correct = Choice.objects.create(
            question=cls.question, text="Correct answer", is_correct=True,
        )
        cls.wrong = Choice.objects.create(
            question=cls.question, text="Wrong answer", is_correct=False,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)

    def take_url(self):
        return reverse("exam_take", args=[self.assessment.pk])

    def test_login_and_enrollment_required(self):
        self.assertRedirects(
            self.client.get(self.take_url()),
            f"{reverse('login')}?next={self.take_url()}",
        )
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.take_url()).status_code, 404)
        self.assertEqual(self.client.post(self.take_url(), {}).status_code, 404)
        self.assertFalse(Attempt.objects.filter(student=self.other).exists())

    def test_quiz_is_visible_on_course_learning_page(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("course_learn", args=[self.course.slug]))
        self.assertContains(response, "Practice Quiz")
        self.assertContains(response, self.take_url())

    def test_correct_scoring_and_duplicate_submit(self):
        self.client.force_login(self.student)
        self.assertContains(self.client.get(self.take_url()), "Which answer is correct?")
        values = {f"question_{self.question.pk}": str(self.correct.pk)}
        response = self.client.post(self.take_url(), values)
        attempt = Attempt.objects.get(student=self.student, assessment=self.assessment)
        self.assertRedirects(response, reverse("exam_result", args=[attempt.pk]))
        self.assertEqual((attempt.score, attempt.total_marks), (2, 2))
        self.assertEqual(AttemptAnswer.objects.filter(attempt=attempt).count(), 1)
        self.assertContains(self.client.get(reverse("exam_result", args=[attempt.pk])), "100%")
        self.client.post(self.take_url(), {f"question_{self.question.pk}": str(self.wrong.pk)})
        attempt.refresh_from_db()
        self.assertEqual(attempt.score, 2)
        self.assertEqual(AttemptAnswer.objects.count(), 1)

    def test_wrong_and_unanswered_score_zero(self):
        self.client.force_login(self.student)
        self.client.post(self.take_url(), {f"question_{self.question.pk}": str(self.wrong.pk)})
        self.assertEqual(Attempt.objects.get(student=self.student).score, 0)

    def test_invalid_choice_is_rejected_without_submission(self):
        outsider = Question.objects.create(
            assessment=self.assessment, text="Second question",
        )
        other_choice = Choice.objects.create(
            question=outsider, text="Answer", is_correct=True,
        )
        Choice.objects.create(question=outsider, text="Other", is_correct=False)
        self.client.force_login(self.student)
        self.assertEqual(
            self.client.post(
                self.take_url(), {f"question_{self.question.pk}": str(other_choice.pk)}
            ).status_code,
            400,
        )
        self.assertIsNone(Attempt.objects.get(student=self.student).submitted_at)

    def test_expired_attempt_cannot_score(self):
        self.client.force_login(self.student)
        attempt = Attempt.objects.create(
            assessment=self.assessment, student=self.student,
            started_at=timezone.now() - timedelta(minutes=35),
        )
        self.client.post(self.take_url(), {f"question_{self.question.pk}": str(self.correct.pk)})
        attempt.refresh_from_db()
        self.assertIsNotNone(attempt.submitted_at)
        self.assertEqual(attempt.score, 0)
        self.assertEqual(attempt.total_marks, 2)

    def test_result_is_private(self):
        attempt = Attempt.objects.create(
            student=self.student, assessment=self.assessment,
            score=2, total_marks=2, submitted_at=timezone.now(),
        )
        url = reverse("exam_result", args=[attempt.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).status_code, 200)
        Enrollment.objects.filter(student=self.student).update(is_active=False)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_draft_and_invalid_question_bank_are_hidden(self):
        self.client.force_login(self.student)
        self.assessment.is_published = False
        self.assessment.save(update_fields=["is_published"])
        self.assertEqual(self.client.get(self.take_url()).status_code, 404)
        self.assessment.is_published = True
        self.assessment.save(update_fields=["is_published"])
        self.wrong.is_correct = True
        self.wrong.save(update_fields=["is_correct"])
        self.assertEqual(self.client.get(self.take_url()).status_code, 404)

    def test_admin_performance_is_private(self):
        url = reverse("management:results")
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(url).status_code, 403)
        admin = get_user_model().objects.create_superuser(
            username="examadmin", email="examadmin@example.com", password="SafePassword123!"
        )
        self.client.force_login(admin)
        self.assertContains(self.client.get(url), "Student performance")

    def test_daily_quiz_hides_future_date_and_requires_enrollment(self):
        daily = Assessment.objects.create(
            course=self.course, title="Current Affairs Daily Quiz",
            kind=Assessment.Kind.DAILY, daily_date=timezone.localdate() + timedelta(days=1),
            is_published=True,
        )
        question = Question.objects.create(assessment=daily, text="Current affairs question")
        Choice.objects.create(question=question, text="Answer A", is_correct=True)
        Choice.objects.create(question=question, text="Answer B", is_correct=False)
        self.client.force_login(self.student)
        self.assertNotContains(self.client.get(reverse("daily_quizzes")), daily.title)
        self.assertEqual(self.client.get(reverse("exam_take", args=[daily.pk])).status_code, 404)
        daily.daily_date = timezone.localdate()
        daily.save(update_fields=["daily_date"])
        self.assertContains(self.client.get(reverse("daily_quizzes")), daily.title)
        self.assertEqual(self.client.get(reverse("exam_take", args=[daily.pk])).status_code, 200)
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("daily_quizzes")), daily.title)
        self.assertEqual(self.client.get(reverse("exam_take", args=[daily.pk])).status_code, 404)

    def test_answer_review_and_private_personal_rank(self):
        self.question.explanation = "This is the documented reasoning."
        self.question.save(update_fields=["explanation"])
        Enrollment.objects.create(student=self.other, course=self.course)
        Attempt.objects.create(
            assessment=self.assessment, student=self.other,
            score=2, total_marks=2, submitted_at=timezone.now(),
        )
        self.client.force_login(self.student)
        self.client.post(self.take_url(), {f"question_{self.question.pk}": str(self.wrong.pk)})
        attempt = Attempt.objects.get(student=self.student)
        result_url = reverse("exam_result", args=[attempt.pk])
        response = self.client.get(result_url)
        self.assertContains(response, "Your rank:")
        self.assertContains(response, "2 of 2")
        self.assertContains(response, "Wrong answer")
        self.assertContains(response, "Correct answer")
        self.assertContains(response, "This is the documented reasoning.")
        self.assertNotContains(response, self.other.email)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(result_url).status_code, 404)

    def test_daily_assessment_admin_requires_date(self):
        from management.forms import AssessmentForm

        form = AssessmentForm(data={
            "course": self.course.pk, "title": "No date",
            "kind": Assessment.Kind.DAILY, "duration_minutes": 10,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("Daily quizzes require a date.", str(form.errors))
