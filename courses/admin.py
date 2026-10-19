from django.contrib import admin

from .models import Category, Course


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "mode", "price", "is_published", "created_at")
    list_filter = ("is_published", "mode", "category")
    search_fields = ("title", "summary")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
