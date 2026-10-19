from django.urls import path

from . import views

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course_list"),
    path("<slug:slug>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("<slug:slug>/enroll/", views.enroll, name="course_enroll"),
    path("<slug:slug>/learn/", views.learn, name="course_learn"),
    path("lessons/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<int:lesson_id>/notes/", views.download_notes, name="lesson_notes"),
    path("lessons/<int:lesson_id>/complete/", views.complete_lesson, name="lesson_complete"),
]
