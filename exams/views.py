from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.paginator import Paginator
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
    if assessment.kind == Assessment.Kind.DAILY and (
        not assessment.daily_date or assessment.daily_date > timezone.localdate()
    ):
        raise Http404("Quiz is not available yet.")
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
def daily_quizzes(request):
    quizzes = (
        Assessment.objects.filter(
            kind=Assessment.Kind.DAILY, is_published=True,
            course__is_published=True, daily_date__lte=timezone.localdate(),
            course__enrollments__student=request.user,
            course__enrollments__is_active=True,
        )
        .select_related("course")
        .order_by("-daily_date", "-id")
    )
    return render(request, "exams/daily.html", {"quizzes": quizzes})


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
    questions = (
        Question.objects.filter(assessment=attempt.assessment)
        .prefetch_related("choices")
    )
    selected = dict(attempt.answers.values_list("question_id", "choice_id"))
    review = []
    for question in questions:
        choices = list(question.choices.all())
        chosen = next((choice for choice in choices if choice.pk == selected.get(question.pk)), None)
        correct = next((choice for choice in choices if choice.is_correct), None)
        review.append({"question": question, "selected": chosen, "correct": correct})

    higher_scores = Attempt.objects.filter(
        assessment=attempt.assessment, submitted_at__isnull=False,
        total_marks=attempt.total_marks, score__gt=attempt.score,
    ).count()
    participants = Attempt.objects.filter(
        assessment=attempt.assessment, submitted_at__isnull=False,
        total_marks=attempt.total_marks,
    ).count()
    return render(request, "exams/result.html", {
        "attempt": attempt, "review": review, "rank": higher_scores + 1,
        "participants": participants,
    })


@login_required
@never_cache
def assessment_history(request):
    attempts = (
        Attempt.objects.filter(
            student=request.user, submitted_at__isnull=False,
            assessment__course__enrollments__student=request.user,
            assessment__course__enrollments__is_active=True,
        )
        .select_related("assessment__course")
        .order_by("-submitted_at", "-pk")
    )
    page = Paginator(attempts, 15).get_page(request.GET.get("page"))
    return render(request, "exams/history.html", {"page": page})
