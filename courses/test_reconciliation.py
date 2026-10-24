from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import StudentNotification
from .models import Category, Course, Enrollment, Order
from .reconciliation import reconcile_order_refund


@override_settings(
    RAZORPAY_KEY_ID="rzp_test_only", RAZORPAY_KEY_SECRET="not-real",
)
class RefundReconciliationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        cls.student = user.objects.create_user(
            username="refund_student", email="refund.student@example.com",
            password="SamplePassword123!",
        )
        cls.superuser = user.objects.create_superuser(
            username="refund_admin", email="refund.admin@example.com",
            password="SamplePassword123!",
        )
        cls.staff = user.objects.create_user(
            username="refund_staff", email="refund.staff@example.com",
            password="SamplePassword123!", is_staff=True,
        )
        cls.staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="courses",
            content_type__model="order", codename="change_order",
        ))
        category = Category.objects.create(name="Refund Courses", slug="refund-courses")
        cls.course = Course.objects.create(
            category=category, title="Refund Test Course", slug="refund-test-course",
            summary="Refunds", description="Refund testing",
            is_published=True, price=Decimal("600.00"),
        )
        cls.enrollment = Enrollment.objects.create(student=cls.student, course=cls.course)
        cls.order = Order.objects.create(
            student=cls.student, course=cls.course,
            status=Order.Status.PAID, amount=Decimal("600.00"),
            gateway_order_id="order_refund_scs",
            gateway_payment_id="pay_refund_scs",
            verified_at=timezone.now(),
        )

    def payment(self, refunded=0, **changed):
        data = {
            "id": "pay_refund_scs", "order_id": "order_refund_scs",
            "amount": 60000, "amount_refunded": refunded,
            "currency": "INR", "status": "refunded" if refunded == 60000 else "captured",
        }
        data.update(changed)
        return data

    def test_partial_refund_keeps_course_access(self):
        order = reconcile_order_refund(self.order.pk, self.payment(25000))
        self.assertEqual(order.refunded_amount, Decimal("250.00"))
        self.assertEqual(order.net_amount, Decimal("350.00"))
        self.assertIsNotNone(order.refund_checked_at)
        self.enrollment.refresh_from_db()
        self.assertTrue(self.enrollment.is_active)
        self.client.force_login(self.student)
        self.assertContains(
            self.client.get(reverse("course_payment_receipt", args=[order.pk])),
            "Recorded refund:",
        )

    def test_full_refund_revokes_access_once(self):
        for _ in range(2):
            order = reconcile_order_refund(self.order.pk, self.payment(60000))
        self.assertTrue(order.fully_refunded)
        self.assertEqual(order.refunded_amount, order.amount)
        self.enrollment.refresh_from_db()
        self.assertFalse(self.enrollment.is_active)
        self.assertEqual(
            StudentNotification.objects.filter(
                student=self.student, event_key=f"full-refund-{order.pk}",
            ).count(), 1,
        )
        self.client.force_login(self.student)
        self.assertEqual(
            self.client.get(reverse("course_learn", args=[self.course.slug])).status_code,
            404,
        )
        self.assertContains(
            self.client.get(reverse("course_payment_receipt", args=[order.pk])),
            "Fully refunded",
        )

    def test_reconciliation_rejects_mismatches_and_stale_data(self):
        bad = [
            self.payment(10000, id="pay_somebody_else"),
            self.payment(10000, order_id="order_somebody_else"),
            self.payment(10000, currency="USD"),
            self.payment(10000, amount=50000),
            self.payment(70000),
            self.payment(-1),
            self.payment("25000"),
            self.payment(True),
            self.payment(10000, status="authorized"),
            self.payment(10000, status="refunded"),
        ]
        for item in bad:
            with self.subTest(payment=item):
                with self.assertRaises(ValueError):
                    reconcile_order_refund(self.order.pk, item)
        self.order.refresh_from_db()
        self.assertEqual(self.order.refunded_amount, Decimal("0"))
        self.assertTrue(self.enrollment.is_active)
        reconcile_order_refund(self.order.pk, self.payment(30000))
        with self.assertRaises(ValueError):
            reconcile_order_refund(self.order.pk, self.payment(10000))
        self.order.refresh_from_db()
        self.assertEqual(self.order.refunded_amount, Decimal("300.00"))

    def test_manual_approved_order_cannot_be_reconciled(self):
        self.order.gateway_payment_id = None
        self.order.save(update_fields=["gateway_payment_id"])
        with self.assertRaises(ValueError):
            reconcile_order_refund(self.order.pk, self.payment(60000))

    @patch("courses.reconciliation.fetch_gateway_payment")
    def test_admin_reconciliation_is_read_only_and_superuser_only(self, fetch):
        fetch.return_value = self.payment(10000)
        url = reverse("admin:courses_order_changelist")
        data = {
            "action": "reconcile_refunds", "_selected_action": [self.order.pk],
        }
        self.client.force_login(self.staff)
        response = self.client.post(url, data)
        self.assertIn(response.status_code, (200, 302))
        fetch.assert_not_called()
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.post(url, data, follow=True).status_code, 200)
        fetch.assert_called_once_with("pay_refund_scs")
        self.order.refresh_from_db()
        self.assertEqual(self.order.refunded_amount, Decimal("100.00"))

    def test_superuser_report_shows_recorded_net_value(self):
        reconcile_order_refund(self.order.pk, self.payment(17500))
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:courses_course_reports"))
        row = next(row for row in response.context["rows"] if row["course"].pk == self.course.pk)
        self.assertEqual(row["captured_value"], Decimal("600.00"))
        self.assertEqual(row["recorded_refunds"], Decimal("175.00"))
        self.assertEqual(row["net_recorded_value"], Decimal("425.00"))
