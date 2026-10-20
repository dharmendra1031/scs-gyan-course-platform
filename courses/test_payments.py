import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Course, Enrollment, Order
from .payments import confirm_gateway_payment


@override_settings(
    RAZORPAY_KEY_ID="rzp_test_demo", RAZORPAY_KEY_SECRET="demo-secret",
    RAZORPAY_WEBHOOK_SECRET="webhook-secret",
)
class PaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="buyer", email="buyer@example.com", password="TestStrong123!"
        )
        cls.other = get_user_model().objects.create_user(
            username="otherbuyer", email="otherbuyer@example.com", password="TestStrong123!"
        )
        category = Category.objects.create(name="Exam Prep", slug="exam-prep")
        cls.course = Course.objects.create(
            category=category, title="Paid Course", slug="paid-course",
            summary="Course", description="Course details",
            price=Decimal("750.00"), is_published=True,
        )
        cls.order = Order.objects.create(
            student=cls.user, course=cls.course, amount=cls.course.price,
        )

    def payment(self, **changes):
        data = {
            "id": "pay_test_123", "order_id": "order_test_123",
            "status": "captured", "amount": 75000, "currency": "INR",
        }
        data.update(changes)
        return data

    def signature(self):
        return hmac.new(
            b"demo-secret", b"order_test_123|pay_test_123", hashlib.sha256,
        ).hexdigest()

    @patch("courses.payment_views.create_gateway_order", return_value="order_test_123")
    def test_checkout_is_post_only_and_idempotent(self, create_order):
        self.client.force_login(self.user)
        url = reverse("course_checkout", args=[self.order.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertContains(self.client.post(url), "Pay ₹750.00")
        self.assertContains(self.client.post(url), "order_test_123")
        self.assertEqual(create_order.call_count, 1)

    @patch("courses.payment_views.create_gateway_order")
    def test_another_student_cannot_checkout(self, create_order):
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post(reverse("course_checkout", args=[self.order.pk])).status_code, 404,
        )
        create_order.assert_not_called()

    @patch("courses.payment_views.fetch_gateway_payment")
    def test_payment_must_be_signed_and_captured(self, gateway):
        self.order.gateway_order_id = "order_test_123"
        self.order.save(update_fields=["gateway_order_id"])
        self.client.force_login(self.user)
        url = reverse("course_payment_verify", args=[self.order.pk])
        request = {
            "razorpay_order_id": "order_test_123",
            "razorpay_payment_id": "pay_test_123",
            "razorpay_signature": self.signature(),
        }
        gateway.return_value = self.payment(status="authorized")
        self.assertEqual(self.client.post(url, request).status_code, 400)
        gateway.return_value = self.payment(amount=100)
        self.assertEqual(self.client.post(url, request).status_code, 400)
        request["razorpay_signature"] = "0" * 64
        self.assertEqual(self.client.post(url, request).status_code, 400)
        request["razorpay_signature"] = self.signature()
        gateway.return_value = self.payment()
        self.assertRedirects(
            self.client.post(url, request), reverse("course_learn", args=[self.course.slug]),
        )
        self.assertRedirects(
            self.client.post(url, request), reverse("course_learn", args=[self.course.slug]),
        )
        self.assertEqual(Enrollment.objects.count(), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)

    def test_gateway_reference_cannot_be_reused(self):
        self.order.gateway_order_id = "order_test_123"
        self.order.save(update_fields=["gateway_order_id"])
        confirm_gateway_payment(self.order.pk, "order_test_123", self.payment())
        course = Course.objects.create(
            category=self.course.category, title="Second Course", slug="second-course",
            summary="Another", description="Another course", price=self.course.price,
            is_published=True,
        )
        other = Order.objects.create(
            student=self.other, course=course, amount=course.price,
            gateway_order_id="order_test_456",
        )
        with self.assertRaises(ValueError):
            confirm_gateway_payment(
                other.pk, "order_test_456", self.payment(order_id="order_test_456"),
            )
        self.assertFalse(Enrollment.objects.filter(student=self.other).exists())

    def test_webhook_requires_valid_signature_and_is_idempotent(self):
        self.order.gateway_order_id = "order_test_123"
        self.order.save(update_fields=["gateway_order_id"])
        body = json.dumps({
            "event": "payment.captured",
            "payload": {"payment": {"entity": self.payment()}},
        }).encode()
        url = reverse("course_payment_webhook")
        self.assertEqual(
            self.client.post(url, body, content_type="application/json",
                             HTTP_X_RAZORPAY_SIGNATURE="invalid").status_code, 400,
        )
        signature = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()
        for _ in range(2):
            self.assertEqual(
                self.client.post(url, body, content_type="application/json",
                                 HTTP_X_RAZORPAY_SIGNATURE=signature).status_code, 200,
            )
        self.assertEqual(Enrollment.objects.count(), 1)

    def test_signed_malformed_webhook_is_rejected(self):
        body = b'[]'
        signature = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()
        self.assertEqual(
            self.client.post(
                reverse("course_payment_webhook"), body,
                content_type="application/json",
                HTTP_X_RAZORPAY_SIGNATURE=signature,
            ).status_code,
            400,
        )
        self.assertFalse(Enrollment.objects.exists())

    @override_settings(RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="")
    def test_missing_credentials_never_enroll(self):
        self.client.force_login(self.user)
        self.assertRedirects(
            self.client.post(reverse("course_checkout", args=[self.order.pk])),
            reverse("dashboard"),
        )
        self.assertFalse(Enrollment.objects.exists())
