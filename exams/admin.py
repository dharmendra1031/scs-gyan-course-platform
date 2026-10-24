from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count
from django.template.response import TemplateResponse
from django.urls import path

from .models import Assessment, Attempt, AttemptAnswer, Choice, Question


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "kind", "duration_minutes", "is_published")
    list_filter = ("kind", "is_published", "course")
    search_fields = ("title", "course__title")

    def save_model(self, request, obj, form, change):
        if obj.duration_minutes == 0:
            raise ValidationError("Duration must be at least one minute.")
        super().save_model(request, obj, form, change)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
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
            .annotate(students=Count("id"), average_score=Avg("score"))
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
