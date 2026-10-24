from django.urls import path

from . import views

urlpatterns = [
    path("<int:assessment_id>/", views.take_assessment, name="exam_take"),
    path("results/<int:attempt_id>/", views.assessment_result, name="exam_result"),
]
