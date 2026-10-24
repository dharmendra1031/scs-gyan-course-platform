from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.db.models import Avg, Count, Max
from django.template.response import TemplateResponse
from django.urls import path

from .models import Assessment, Attempt, AttemptAnswer, Choice, Question


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = "__all__"

    def clean_duration_minutes(self):
        duration = self.cleaned_data["duration_minutes"]
        if duration < 1:
            raise forms.ValidationError("Duration must be at least one minute.")
        return duration

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("kind") == Assessment.Kind.DAILY and not cleaned.get("daily_date"):
            raise forms.ValidationError("Daily quizzes require a date.")
        if cleaned.get("is_published") and (
            not self.instance.pk or not self.instance.questions.exists()
        ):
            raise forms.ValidationError("Create questions before publishing this assessment.")
        return cleaned


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    form = AssessmentForm
    list_display = ("title", "course", "kind", "daily_date", "duration_minutes", "is_published")
    list_filter = ("kind", "is_published", "course")
    search_fields = ("title", "course__title")

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "__all__"

    def clean_marks(self):
        marks = self.cleaned_data["marks"]
        if marks < 1:
            raise forms.ValidationError("Marks must be at least one.")
        return marks


class ChoiceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        choices = [
            form.cleaned_data for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE")
        ]
        if len(choices) < 2 or sum(bool(choice.get("is_correct")) for choice in choices) != 1:
            raise forms.ValidationError("Add at least two choices and mark exactly one correct.")


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceFormSet
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm
    list_display = ("text", "assessment", "position", "marks")
    list_filter = ("assessment",)
    search_fields = ("text",)
    inlines = [ChoiceInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "assessment", "score", "total_marks", "percent_display", "submitted_at")
    list_filter = ("assessment__course", "assessment", "submitted_at")
    search_fields = ("student__username", "student__email", "assessment__title")
    readonly_fields = ("student", "assessment", "started_at", "submitted_at", "score", "total_marks")
    change_list_template = "admin/exams/attempt/change_list.html"

    @admin.display(description="Score %")
    def percent_display(self, obj):
        return f"{obj.percent}%"

    def get_urls(self):
        return [
            path("performance/", self.admin_site.admin_view(self.performance), name="exams_attempt_performance"),
        ] + super().get_urls()

    def performance(self, request):
        if not self.has_view_permission(request):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        summary = (
            Attempt.objects.filter(submitted_at__isnull=False)
            .values("assessment__title", "assessment__course__title")
            .annotate(students=Count("id"), average_score=Avg("score"), highest_score=Max("score"))
            .order_by("assessment__course__title", "assessment__title")
        )
        return TemplateResponse(request, "admin/exams/attempt/performance.html", {
            **self.admin_site.each_context(request),
            "title": "Student performance",
            "summary": summary,
            "opts": self.model._meta,
        })

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
