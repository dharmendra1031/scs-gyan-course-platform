from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from courses.models import Enrollment, Order
from courses.payments import gateway_enabled

from .forms import SignupForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("dashboard")

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard(request):
    enrollments = Enrollment.objects.filter(
        student=request.user, is_active=True,
    ).select_related("course").annotate(
        completed_count=Count("completed_lessons", distinct=True),
        lesson_count=Count(
            "course__chapters__lessons",
            filter=Q(course__chapters__lessons__is_published=True), distinct=True,
        ),
    )
    orders = Order.objects.filter(student=request.user).select_related("course")
    return render(request, "accounts/dashboard.html", {
        "enrollments": enrollments, "orders": orders,
        "payments_enabled": gateway_enabled(),
    })
