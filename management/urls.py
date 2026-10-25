from django.urls import path
from . import views

app_name = "management"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("content/<slug:resource>/", views.content_list, name="list"),
    path("content/<slug:resource>/new/", views.content_form, name="create"),
    path("content/<slug:resource>/<int:pk>/edit/", views.content_form, name="edit"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:pk>/<slug:action>/", views.order_action, name="order_action"),
    path("reports/", views.reports, name="reports"),
    path("enquiries/", views.enquiries, name="enquiries"),
    path("enquiries/<int:pk>/", views.enquiry_detail, name="enquiry_detail"),
    path("students/", views.students, name="students"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),
    path("results/", views.results, name="results"),
]
