from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from courses.models import Enrollment
from .models import Assessment, Attempt, AttemptAnswer, Choice, Question


def available_assessment(request, assessment_id):
    assessment = get_object_or_404(
        Assessment.objects.select_related("course"),
        pk=assessment_id, is_published=True, course__is_published=True,
    )
    get_object_or_404(
        Enrollment, student=request.user, course=assessment.course, is_active=True,
    )
    return assessment


def valid_questions(assessment):
    questions = list(
        Question.objects.filter(assessment=assessment).prefetch_related("choices")
    )
    if not questions or any(
        question.marks == 0 or len(question.choices.all()) < 2
        or sum(choice.is_correct for choice in question.choices.all()) != 1
        for question in questions
    ):
        raise Http404("This test is not ready.")
    return questions


@login_required
@never_cache
def take_assessment(request, assessment_id):
    assessment = available_assessment(request, assessment_id)
    questions = valid_questions(assessment)
    total_marks = sum(question.marks for question in questions)
    with transaction.atomic():
        attempt, _ = Attempt.objects.get_or_create(
            assessment=assessment, student=request.user,
        )
        attempt = Attempt.objects.select_for_update().get(pk=attempt.pk)
        if attempt.submitted_at:
            return redirect("exam_result", attempt_id=attempt.pk)

        expired = timezone.now() >= attempt.expires_at
        if expired or request.method == "POST":
            selected = []
            if not expired:
                for question in questions:
                    field = f"question_{question.pk}"
                    values = request.POST.getlist(field)
                    if len(values) > 1:
                        return HttpResponseBadRequest("Invalid answer.")
                    if not values or not values[0]:
                        continue
                    if not values[0].isdecimal():
                        return HttpResponseBadRequest("Invalid answer.")
                    choice = next(
                        (item for item in question.choices.all()
                         if item.pk == int(values[0])), None,
                    )
                    if choice is None:
                        return HttpResponseBadRequest("Invalid answer.")
                    selected.append((question, choice))

            attempt.total_marks = total_marks
            attempt.score = sum(question.marks for question, choice in selected if choice.is_correct)
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["score", "total_marks", "submitted_at"])
            AttemptAnswer.objects.bulk_create([
                AttemptAnswer(attempt=attempt, question=question, choice=choice)
                for question, choice in selected
            ])
            return redirect("exam_result", attempt_id=attempt.pk)

    return render(request, "exams/take.html", {
        "assessment": assessment, "questions": questions, "expires_at": attempt.expires_at,
    })


@login_required
@never_cache
def assessment_result(request, attempt_id):
    attempt = get_object_or_404(
        Attempt.objects.select_related("assessment__course"),
        pk=attempt_id, student=request.user, submitted_at__isnull=False,
    )
    get_object_or_404(
        Enrollment, student=request.user, course=attempt.assessment.course, is_active=True,
    )
    return render(request, "exams/result.html", {"attempt": attempt})
