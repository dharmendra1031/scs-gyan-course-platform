from django.urls import path

from . import views, payment_views

urlpatterns = [
    path("payments/<int:order_id>/checkout/", payment_views.checkout, name="course_checkout"),
    path("payments/<int:order_id>/verify/", payment_views.verify_payment, name="course_payment_verify"),
    path("payments/webhook/", payment_views.payment_webhook, name="course_payment_webhook"),
    path("payments/<int:order_id>/receipt/", payment_views.payment_receipt, name="course_payment_receipt"),
    path("", views.CourseListView.as_view(), name="course_list"),
    path("<slug:slug>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("<slug:slug>/enroll/", views.enroll, name="course_enroll"),
    path("<slug:slug>/learn/", views.learn, name="course_learn"),
    path("lessons/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<int:lesson_id>/notes/", views.download_notes, name="lesson_notes"),
    path("materials/<int:material_id>/download/", views.download_material, name="material_download"),
    path("lessons/<int:lesson_id>/video/", views.open_video, name="lesson_video"),
    path("lessons/<int:lesson_id>/complete/", views.complete_lesson, name="lesson_complete"),
]
