from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from courses.models import Enrollment, Order
from courses.payments import gateway_enabled
from .models import StudentNotification

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
        completed_count=Count(
            "completed_lessons",
            filter=Q(completed_lessons__lesson__is_published=True), distinct=True,
        ),
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


@login_required
@never_cache
def notification_inbox(request):
    notifications = StudentNotification.objects.filter(student=request.user)[:50]
    return render(request, "accounts/notifications.html", {
        "notifications": notifications,
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        StudentNotification, pk=notification_id, student=request.user,
    )
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect("notification_inbox")
