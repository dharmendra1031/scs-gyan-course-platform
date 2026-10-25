from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Assessment(models.Model):
    class Kind(models.TextChoices):
        QUIZ = "quiz", "Quiz"
        TEST = "test", "Test Series"
        DAILY = "daily", "Daily Quiz"

    course = models.ForeignKey("courses.Course", on_delete=models.PROTECT, related_name="assessments")
    title = models.CharField(max_length=180)
    kind = models.CharField(max_length=5, choices=Kind.choices, default=Kind.QUIZ)
    daily_date = models.DateField(blank=True, null=True)
    duration_minutes = models.PositiveSmallIntegerField(default=30)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title


class Question(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    position = models.PositiveIntegerField(default=0)
    marks = models.PositiveSmallIntegerField(default=1)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.text[:100]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text


class Attempt(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT, related_name="attempts")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exam_attempts")
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(fields=["assessment", "student"], name="unique_student_assessment_attempt"),
        ]

    @property
    def expires_at(self):
        return self.started_at + timedelta(minutes=self.assessment.duration_minutes)

    @property
    def percent(self):
        return round(100 * self.score / self.total_marks) if self.total_marks else 0


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    choice = models.ForeignKey(Choice, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="unique_attempt_question_answer"),
        ]
