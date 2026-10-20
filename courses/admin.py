from django.contrib import admin, messages

from .models import Category, Chapter, Course, Enrollment, Lesson, LessonProgress, Order
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
    list_display = ("title", "category", "mode", "price", "is_published", "created_at")
    list_filter = ("is_published", "mode", "category")
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    inlines = [ChapterInline]


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
