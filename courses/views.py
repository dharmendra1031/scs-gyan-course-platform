from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import FileResponse, Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from .models import Category, Chapter, Course, CourseCertificate, Enrollment, Lesson, LessonProgress, Order, StudyMaterial
from .certificates import issue_certificate, render_certificate
from accounts.notifications import notify


class CourseListView(ListView):
    template_name = "courses/list.html"
    context_object_name = "courses"
    paginate_by = 9

    def get_queryset(self):
        queryset = Course.objects.filter(is_published=True).select_related("category")
        category = self.request.GET.get("category", "").strip()
        search = self.request.GET.get("q", "").strip()
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(summary__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["current_category"] = self.request.GET.get("category", "")
        context["search"] = self.request.GET.get("q", "")
        return context


class CourseDetailView(DetailView):
    template_name = "courses/detail.html"
    context_object_name = "course"
    slug_field = "slug"

    def get_queryset(self):
        return Course.objects.filter(is_published=True).select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chapters"] = Chapter.objects.filter(course=self.object).prefetch_related(
            Prefetch("lessons", queryset=Lesson.objects.filter(is_published=True))
        )
        context["outcomes"] = [
            item.strip() for item in self.object.learning_outcomes.splitlines() if item.strip()
        ]
        if self.request.user.is_authenticated:
            context["is_enrolled"] = Enrollment.objects.filter(
                course=self.object, student=self.request.user, is_active=True
            ).exists()
            context["pending_order"] = Order.objects.filter(
                course=self.object, student=self.request.user, status=Order.Status.PENDING
            ).exists()
        return context


@login_required
@require_POST
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    with transaction.atomic():
        if Enrollment.objects.filter(course=course, student=request.user, is_active=True).exists():
            return redirect("course_learn", slug=slug)
        if course.price == Decimal("0"):
            enrollment, _ = Enrollment.objects.update_or_create(
                student=request.user, course=course, defaults={"is_active": True}
            )
            notify(
                request.user, f"enrolled-{course.pk}", "Course enrollment",
                f"You are enrolled in {course.title}.",
                url_name="course_learn", args=[course.slug],
            )
            messages.success(request, "You are enrolled in this course.")
            return redirect("course_learn", slug=slug)
        # Never grant access to a paid course until payment is verified.
        order, created = Order.objects.get_or_create(
            student=request.user, course=course,
            defaults={"amount": course.price},
        )
        if not created and order.status == Order.Status.CANCELLED:
            if order.gateway_order_id or order.gateway_payment_id:
                messages.error(request, "Please contact support to review this cancelled payment.")
                return redirect("dashboard")
            order.status = Order.Status.PENDING
            order.amount = course.price
            order.save(update_fields=["status", "amount", "updated_at"])
    messages.info(request, "Your order is pending payment verification. Course access is not active yet.")
    return redirect("dashboard")


def enrolled_lesson(request, lesson_id):
    lesson = get_object_or_404(
        Lesson.objects.select_related("chapter__course"),
        pk=lesson_id, is_published=True, chapter__course__is_published=True,
    )
    enrollment = get_object_or_404(
        Enrollment, course=lesson.chapter.course, student=request.user, is_active=True
    )
    return lesson, enrollment


@login_required
def learn(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    enrollment = get_object_or_404(Enrollment, course=course, student=request.user, is_active=True)
    chapters = course.chapters.prefetch_related(
        Prefetch("lessons", queryset=Lesson.objects.filter(is_published=True))
    )
    completed_ids = set(enrollment.completed_lessons.values_list("lesson_id", flat=True))
    published_ids = set(Lesson.objects.filter(
        chapter__course=course, is_published=True,
    ).values_list("id", flat=True))
    certificate = CourseCertificate.objects.filter(enrollment=enrollment).first()
    chapters = list(chapters)
    next_lesson = next(
        (lesson for chapter in chapters for lesson in chapter.lessons.all()
         if lesson.pk not in completed_ids),
        None,
    )
    return render(request, "courses/learn.html", {
        "course": course, "chapters": chapters, "completed_ids": completed_ids,
        "assessments": course.assessments.filter(is_published=True),
        "materials": course.materials.filter(is_published=True),
        "certificate": certificate,
        "certificate_ready": bool(published_ids and published_ids.issubset(completed_ids)),
        "published_count": len(published_ids),
        "completed_count": len(published_ids.intersection(completed_ids)),
        "next_lesson": next_lesson,
    })


@login_required
@never_cache
def lesson_detail(request, lesson_id):
    lesson, enrollment = enrolled_lesson(request, lesson_id)
    completed = enrollment.completed_lessons.filter(lesson=lesson).exists()
    lessons = list(
        Lesson.objects.filter(chapter__course=lesson.chapter.course, is_published=True)
        .order_by("chapter__position", "chapter__id", "position", "id")
        .only("id", "title")
    )
    position = next(index for index, item in enumerate(lessons) if item.pk == lesson.pk)
    return render(request, "courses/lesson.html", {
        "lesson": lesson, "completed": completed,
        "previous_lesson": lessons[position - 1] if position else None,
        "next_lesson": lessons[position + 1] if position + 1 < len(lessons) else None,
    })


@login_required
@never_cache
def open_video(request, lesson_id):
    lesson, _ = enrolled_lesson(request, lesson_id)
    if not lesson.video_url:
        raise Http404("Video is not available.")
    return HttpResponseRedirect(lesson.video_url)


@login_required
@never_cache
def download_notes(request, lesson_id):
    lesson, _ = enrolled_lesson(request, lesson_id)
    if not lesson.notes:
        raise Http404("Notes are not available.")
    try:
        file = lesson.notes.open("rb")
    except FileNotFoundError as exc:
        raise Http404("Notes are not available.") from exc
    return FileResponse(file, as_attachment=True, filename=f"lesson-{lesson.pk}.pdf", content_type="application/pdf")


@login_required
@require_POST
def complete_lesson(request, lesson_id):
    lesson, enrollment = enrolled_lesson(request, lesson_id)
    LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
    issue_certificate(enrollment.pk)
    messages.success(request, "Lesson marked as complete.")
    return redirect("course_learn", slug=lesson.chapter.course.slug)


@login_required
@never_cache
def download_material(request, material_id):
    material = get_object_or_404(
        StudyMaterial.objects.select_related("course"),
        pk=material_id, is_published=True, course__is_published=True,
    )
    get_object_or_404(
        Enrollment, student=request.user, course=material.course, is_active=True,
    )
    if not material.file:
        raise Http404("Study material is not available.")
    try:
        content = material.file.open("rb")
    except (FileNotFoundError, OSError) as exc:
        raise Http404("Study material is not available.") from exc
    response = FileResponse(
        content, as_attachment=True, filename=f"study-material-{material.pk}.pdf",
        content_type="application/pdf",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def request_certificate(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    enrollment = get_object_or_404(
        Enrollment, student=request.user, course=course, is_active=True,
    )
    certificate = issue_certificate(enrollment.pk)
    if certificate is None:
        messages.error(request, "Complete all published lessons before requesting a certificate.")
        return redirect("course_learn", slug=course.slug)
    return redirect("course_certificate", certificate_id=certificate.pk)


@login_required
@never_cache
def download_certificate(request, certificate_id):
    certificate = get_object_or_404(
        CourseCertificate.objects.select_related(
            "enrollment__student", "enrollment__course",
        ),
        pk=certificate_id, enrollment__student=request.user,
        enrollment__is_active=True,
    )
    pdf = render_certificate(certificate)
    response = HttpResponse(
        pdf, content_type="application/pdf",
    )
    response["Content-Disposition"] = (
        f'attachment; filename="scs-gyan-certificate-{certificate.pk}.pdf"'
    )
    return response
