from io import BytesIO
from xml.sax.saxutils import escape

from django.db import transaction
from django.db.models import Count
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from accounts.notifications import notify
from .models import CourseCertificate, Enrollment, Lesson, LessonProgress


@transaction.atomic
def issue_certificate(enrollment_id):
    enrollment = Enrollment.objects.select_for_update().select_related(
        "course", "student",
    ).get(pk=enrollment_id)
    if not enrollment.is_active or not enrollment.course.is_published:
        return None
    published = Lesson.objects.filter(
        chapter__course=enrollment.course, is_published=True,
    )
    published_count = published.count()
    if not published_count:
        return None
    completed_count = LessonProgress.objects.filter(
        enrollment=enrollment, lesson__in=published,
    ).values("lesson_id").distinct().count()
    if completed_count != published_count:
        return None
    certificate, created = CourseCertificate.objects.get_or_create(
        enrollment=enrollment,
    )
    if created:
        notify(
            enrollment.student, f"certificate-{certificate.pk}",
            "Course completed",
            f"Your completion certificate for {enrollment.course.title} is ready.",
            url_name="course_certificate", args=[certificate.pk],
        )
    return certificate


def render_certificate(certificate):
    """Generate a simple English PDF; Indic font support needs separate font setup."""
    stream = BytesIO()
    document = SimpleDocTemplate(
        stream, pagesize=landscape(A4), rightMargin=50, leftMargin=50,
        topMargin=65, bottomMargin=45,
    )
    centered = ParagraphStyle(
        "centered", fontName="Helvetica", alignment=TA_CENTER,
        fontSize=16, leading=27, textColor=colors.HexColor("#152b50"),
        spaceAfter=16,
    )
    heading = ParagraphStyle(
        "heading", parent=centered, fontName="Helvetica-Bold",
        fontSize=30, leading=40, spaceAfter=25,
    )
    small = ParagraphStyle("small", parent=centered, fontSize=11)
    student = escape(certificate.enrollment.student.get_full_name()
                     or certificate.enrollment.student.username)
    title = escape(certificate.enrollment.course.title)
    content = [
        Paragraph("SCS GYAN", heading),
        Paragraph("CERTIFICATE OF COURSE COMPLETION", heading),
        Spacer(1, 20),
        Paragraph("This certifies that", centered),
        Paragraph(student, heading),
        Paragraph("has completed the published lessons of", centered),
        Paragraph(title, heading),
        Spacer(1, 18),
        Paragraph(
            f"Issued {certificate.issued_at:%d %B %Y} · No. {certificate.number}", small,
        ),
        Paragraph("This is a course-completion record, not an accredited qualification.", small),
    ]
    document.build(content)
    return stream.getvalue()
