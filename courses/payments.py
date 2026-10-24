import base64
import hashlib
import hmac
import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Enrollment, Order
from accounts.notifications import notify


class PaymentError(Exception):
    pass


def gateway_enabled():
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def amount_in_paise(amount):
    return int(amount * Decimal("100"))


def gateway_request(method, path, payload=None):
    if not gateway_enabled():
        raise PaymentError("Payment gateway is not configured.")
    credentials = f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    token = base64.b64encode(credentials).decode("ascii")
    request = Request(
        f"https://api.razorpay.com/v1/{path}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": f"Basic {token}", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except (HTTPError, URLError, ValueError) as exc:
        raise PaymentError("Payment provider unavailable.") from exc


def create_gateway_order(order):
    response = gateway_request("POST", "orders", {
        "amount": amount_in_paise(order.amount),
        "currency": "INR",
        "receipt": f"scs-{order.pk}",
    })
    if (not isinstance(response, dict)
            or not str(response.get("id", "")).startswith("order_")
            or response.get("amount") != amount_in_paise(order.amount)
            or response.get("currency") != "INR"):
        raise PaymentError("Invalid gateway order.")
    return response["id"]


def fetch_gateway_payment(payment_id):
    if not payment_id.startswith("pay_") or len(payment_id) > 70:
        raise PaymentError("Invalid payment reference.")
    payment = gateway_request("GET", f"payments/{payment_id}")
    if not isinstance(payment, dict) or payment.get("id") != payment_id:
        raise PaymentError("Payment lookup failed.")
    return payment


def valid_signature(order_id, payment_id, signature):
    if not signature or len(signature) != 64:
        return False
    message = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def valid_webhook(body, signature):
    if not settings.RAZORPAY_WEBHOOK_SECRET or not signature:
        return False
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@transaction.atomic
def confirm_gateway_payment(order_id, gateway_order_id, payment):
    order = Order.objects.select_for_update().get(pk=order_id)
    payment_id = payment.get("id")
    if (order.gateway_order_id != gateway_order_id
            or payment.get("order_id") != gateway_order_id
            or payment.get("status") != "captured"
            or payment.get("amount") != amount_in_paise(order.amount)
            or payment.get("currency") != "INR"
            or not isinstance(payment_id, str) or not payment_id.startswith("pay_")
            or len(payment_id) > 70
            or order.status == Order.Status.CANCELLED):
        raise ValueError("Payment does not match the order.")
    if Order.objects.filter(gateway_payment_id=payment_id).exclude(pk=order.pk).exists():
        raise ValueError("Payment reference is already used.")
    if order.status == Order.Status.PAID:
        if order.gateway_payment_id != payment_id:
            raise ValueError("Order is already paid.")
        return Enrollment.objects.get(student=order.student, course=order.course)
    order.gateway_payment_id = payment_id
    order.verified_at = timezone.now()
    order.status = Order.Status.PAID
    order.save(update_fields=["gateway_payment_id", "verified_at", "status", "updated_at"])
    enrollment, _ = Enrollment.objects.update_or_create(
        student=order.student, course=order.course, defaults={"is_active": True},
    )
    notify(
        order.student, f"payment-{order.pk}", "Payment confirmed",
        f"Access to {order.course.title} is active.",
        url_name="course_learn", args=[order.course.slug],
    )
    return enrollment
