from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.template.response import TemplateResponse
from django.urls import path

from .models import Category, Chapter, Course, Enrollment, Lesson, LessonProgress, Order, StudyMaterial
from .services import approve_order


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    change_list_template = "admin/courses/course/change_list.html"
    list_display = ("title", "category", "mode", "price", "is_published", "created_at")
    list_filter = ("is_published", "mode", "category")
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    inlines = [ChapterInline]

    def get_urls(self):
        return [
            path("reports/", self.admin_site.admin_view(self.reports), name="courses_course_reports"),
        ] + super().get_urls()

    def reports(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied
        courses = list(
            Course.objects.annotate(
                active_students=Count(
                    "enrollments", filter=Q(enrollments__is_active=True), distinct=True,
                ),
                published_lessons=Count(
                    "chapters__lessons",
                    filter=Q(chapters__lessons__is_published=True), distinct=True,
                ),
                published_materials=Count(
                    "materials", filter=Q(materials__is_published=True), distinct=True,
                ),
            ).order_by("title")
        )
        pending = dict(
            Order.objects.filter(status=Order.Status.PENDING)
            .values_list("course_id")
            .annotate(total=Count("id"))
        )
        paid = {
            item["course_id"]: item
            for item in Order.objects.filter(
                status=Order.Status.PAID,
                gateway_payment_id__isnull=False,
                verified_at__isnull=False,
            ).values("course_id").annotate(
                total=Sum("amount"), payments=Count("id"),
            )
        }
        rows = [{
            "course": course,
            "active_students": course.active_students,
            "published_lessons": course.published_lessons,
            "published_materials": course.published_materials,
            "pending_orders": pending.get(course.pk, 0),
            "captured_payments": paid.get(course.pk, {}).get("payments", 0),
            "captured_value": paid.get(course.pk, {}).get("total", 0),
        } for course in courses]
        return TemplateResponse(request, "admin/courses/course/reports.html", {
            **self.admin_site.each_context(request),
            "title": "Course performance report",
            "rows": rows,
            "opts": self.model._meta,
        })


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "position")
    list_filter = ("course",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "chapter", "position", "is_published")
    list_filter = ("is_published", "chapter__course")


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "is_published", "created_at")
    list_filter = ("course", "is_published")
    search_fields = ("title", "course__title")
    list_editable = ("is_published",)


@admin.action(description="Approve verified payments and enroll students")
def approve_verified_payments(modeladmin, request, queryset):
    if not request.user.is_superuser:
        modeladmin.message_user(request, "Only superusers can approve payments.", messages.ERROR)
        return
    approved = 0
    for order in queryset:
        if order.status != Order.Status.PENDING:
            continue
        approve_order(order.pk)
        approved += 1
    modeladmin.message_user(request, f"Approved {approved} order(s).", messages.SUCCESS)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "course", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("student__username", "student__email", "course__title")
    readonly_fields = ("student", "course", "amount", "status", "created_at", "updated_at")
    actions = [approve_verified_payments]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop('approve_verified_payments', None)
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "is_active", "created_at")
    list_filter = ("is_active", "course")
    search_fields = ("student__email", "course__title")

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "completed_at")
    readonly_fields = ("enrollment", "lesson", "completed_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
