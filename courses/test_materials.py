import tempfile
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Chapter, Course, Enrollment, Lesson, Order, StudyMaterial


class StudyMaterialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.student = User.objects.create_user(
            username="materialstudent", email="materialstudent@example.com",
            password="StrongPassword123!",
        )
        cls.other = User.objects.create_user(
            username="materialother", email="materialother@example.com",
            password="StrongPassword123!",
        )
        cls.category = Category.objects.create(name="PDF Courses", slug="pdf-courses")
        cls.course = Course.objects.create(
            category=cls.category, title="PDF Course", slug="pdf-course",
            summary="Notes", description="Course notes",
            price=Decimal("199.00"), is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        field = StudyMaterial._meta.get_field("file")
        original_storage = field.storage
        field.storage = FileSystemStorage(location=directory.name)
        self.addCleanup(setattr, field, "storage", original_storage)
        self.material = StudyMaterial.objects.create(
            course=self.course, title="Study Guide",
            file=SimpleUploadedFile(
                "study-guide.pdf", b"%PDF-1.4\nSample study material",
                content_type="application/pdf",
            ),
            is_published=True,
        )

    def url(self):
        return reverse("material_download", args=[self.material.pk])

    def test_only_enrolled_student_downloads_pdf(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn(b"%PDF-1.4", b"".join(response.streaming_content))
        self.assertContains(
            self.client.get(reverse("course_learn", args=[self.course.slug])),
            "Study Guide",
        )

    def test_draft_and_inactive_enrollment_block_download(self):
        self.client.force_login(self.student)
        self.material.is_published = False
        self.material.save(update_fields=["is_published"])
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.material.is_published = True
        self.material.save(update_fields=["is_published"])
        Enrollment.objects.filter(student=self.student, course=self.course).update(is_active=False)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_unpublished_course_and_missing_file_return_404(self):
        self.client.force_login(self.student)
        self.course.is_published = False
        self.course.save(update_fields=["is_published"])
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.course.is_published = True
        self.course.save(update_fields=["is_published"])
        Path(self.material.file.path).unlink()
        self.assertEqual(self.client.get(self.url()).status_code, 404)


class CourseReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.superuser = User.objects.create_superuser(
            username="reportadmin", email="reportadmin@example.com",
            password="StrongPassword123!",
        )
        cls.staff = User.objects.create_user(
            username="reportstaff", email="reportstaff@example.com",
            password="StrongPassword123!", is_staff=True,
        )
        cls.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="courses",
            content_type__model="course",
            codename="view_course",
        ))
        cls.student = User.objects.create_user(
            username="reportstudent", email="reportstudent@example.com",
            password="StrongPassword123!",
        )
        cls.pending_student = User.objects.create_user(
            username="pendingstudent", email="pendingstudent@example.com",
            password="StrongPassword123!",
        )
        cls.category = Category.objects.create(name="Reports", slug="reports")
        cls.course = Course.objects.create(
            category=cls.category, title="Reports Course", slug="reports-course",
            summary="Reporting", description="Reports course",
            price=Decimal("500.00"), is_published=True,
        )
        Enrollment.objects.create(student=cls.student, course=cls.course)
        chapter = Chapter.objects.create(course=cls.course, title="Unit 1")
        Lesson.objects.create(chapter=chapter, title="Published lesson", is_published=True)
        StudyMaterial.objects.create(
            course=cls.course, title="Material", file="course-materials/test.pdf",
            is_published=True,
        )
        Order.objects.create(
            student=cls.student, course=cls.course, amount=cls.course.price,
            status=Order.Status.PAID,
            gateway_order_id="order_report_one",
            gateway_payment_id="pay_report_one",
            verified_at=timezone.now(),
        )
        Order.objects.create(
            student=cls.pending_student, course=cls.course,
            amount=cls.course.price, status=Order.Status.PENDING,
        )

    def test_reports_superuser_only(self):
        url = reverse("management:reports")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.superuser)
        response = self.client.get(url)
        self.assertContains(response, "Reports Course")
        self.assertContains(response, "500.00")
        row = next(row for row in response.context["rows"] if row["course"].pk == self.course.pk)
        self.assertEqual(row["active_students"], 1)
        self.assertEqual(row["published_lessons"], 1)
        self.assertEqual(row["published_materials"], 1)
        self.assertEqual(row["pending_orders"], 1)
        self.assertEqual(row["captured_payments"], 1)
        self.assertEqual(row["captured_value"], Decimal("500.00"))
