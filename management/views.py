from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg, Count, Max, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from accounts.models import User
from articles.models import Article
from courses.models import Course, Enrollment, Order
from courses.payments import PaymentError
from courses.reconciliation import reconcile_from_gateway
from courses.services import approve_order
from exams.models import Assessment, Attempt
from pages.models import ContactEnquiry

from .resources import RESOURCES


def owner_only(view):
    @login_required
    @never_cache
    @wraps(view)
    def protected(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return protected


@owner_only
def dashboard(request):
    stats = [
        ("Published courses", Course.objects.filter(is_published=True).count(), "courses"),
        ("Active enrollments", Enrollment.objects.filter(is_active=True).count(), "students"),
        ("Pending orders", Order.objects.filter(status=Order.Status.PENDING).count(), "orders"),
        ("Student enquiries", ContactEnquiry.objects.count(), "enquiries"),
    ]
    return render(request, "management/dashboard.html", {
        "stats": stats,
        "recent_orders": Order.objects.select_related("student", "course")[:6],
        "recent_enquiries": ContactEnquiry.objects.all()[:6],
    })


def resource_config(resource):
    config = RESOURCES.get(resource)
    if config is None:
        raise Http404("Content type not found.")
    return config


@owner_only
def content_list(request, resource):
    config = resource_config(resource)
    entries = config.model.objects.all()
    if config.related:
        entries = entries.select_related(*config.related)
    query = request.GET.get("q", "").strip()[:100]
    if query:
        predicate = Q()
        for field in config.search:
            predicate |= Q(**{f"{field}__icontains": query})
        entries = entries.filter(predicate)
    from django.core.paginator import Paginator
    page = Paginator(entries.order_by("-pk"), 25).get_page(request.GET.get("page"))
    return render(request, "management/list.html", {
        "heading": config.label, "resource": resource,
        "page": page, "query": query,
    })


@owner_only
def content_form(request, resource, pk=None):
    config = resource_config(resource)
    instance = get_object_or_404(config.model, pk=pk) if pk is not None else None
    form = config.form(
        request.POST or None,
        request.FILES or None,
        instance=instance,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{config.label} saved.")
        return redirect("management:list", resource=resource)
    return render(request, "management/form.html", {
        "heading": config.label,
        "resource": resource,
        "form": form,
        "editing": instance is not None,
    })


@owner_only
def orders(request):
    entries = Order.objects.select_related("student", "course").order_by("-created_at")
    status = request.GET.get("status", "")
    if status in Order.Status.values:
        entries = entries.filter(status=status)
    from django.core.paginator import Paginator
    page = Paginator(entries, 25).get_page(request.GET.get("page"))
    return render(request, "management/orders.html", {"page": page, "status": status})


@owner_only
@require_POST
def order_action(request, pk, action):
    order = get_object_or_404(Order, pk=pk)
    try:
        if action == "approve":
            if order.status != Order.Status.PENDING:
                raise ValueError("Only pending orders can be approved.")
            approve_order(order.pk)
            messages.success(request, f"Order #{pk} approved.")
        elif action == "reconcile":
            reconcile_from_gateway(order.pk)
            messages.success(request, f"Order #{pk} refund status updated.")
        else:
            raise Http404("Unknown action")
    except (ValueError, PaymentError):
        messages.error(request, "Could not process this order. Check payment state or provider credentials.")
    return redirect("management:orders")


@owner_only
def reports(request):
    courses = list(
        Course.objects.annotate(
            active_students=Count("enrollments", filter=Q(enrollments__is_active=True), distinct=True),
            published_lessons=Count(
                "chapters__lessons", filter=Q(chapters__lessons__is_published=True), distinct=True,
            ),
            published_materials=Count(
                "materials", filter=Q(materials__is_published=True), distinct=True,
            ),
        ).order_by("title")
    )
    pending = dict(
        Order.objects.filter(status=Order.Status.PENDING)
        .values_list("course_id").annotate(total=Count("id"))
    )
    paid = {
        item["course_id"]: item
        for item in Order.objects.filter(
            status=Order.Status.PAID,
            gateway_payment_id__isnull=False,
            verified_at__isnull=False,
        ).values("course_id").annotate(
            total=Sum("amount"), refunds=Sum("refunded_amount"), payments=Count("id"),
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
        "recorded_refunds": paid.get(course.pk, {}).get("refunds", 0),
        "net_recorded_value": paid.get(course.pk, {}).get("total", 0)
                              - paid.get(course.pk, {}).get("refunds", 0),
    } for course in courses]
    return render(request, "management/reports.html", {"rows": rows})


@owner_only
def enquiries(request):
    from django.core.paginator import Paginator
    page = Paginator(ContactEnquiry.objects.all(), 25).get_page(request.GET.get("page"))
    return render(request, "management/enquiries.html", {"page": page})


@owner_only
def students(request):
    from django.core.paginator import Paginator
    students = User.objects.filter(is_staff=False).order_by("-date_joined")
    page = Paginator(students, 25).get_page(request.GET.get("page"))
    return render(request, "management/students.html", {"page": page})


@owner_only
def results(request):
    summary = (
        Attempt.objects.filter(submitted_at__isnull=False)
        .values("assessment__title", "assessment__course__title")
        .annotate(students=Count("id"), average_score=Avg("score"), highest_score=Max("score"))
        .order_by("assessment__course__title", "assessment__title")
    )
    return render(request, "management/results.html", {"summary": summary})
