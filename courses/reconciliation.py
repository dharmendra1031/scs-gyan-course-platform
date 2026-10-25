from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from accounts.notifications import notify
from .models import Enrollment, Order
from .payments import amount_in_paise, fetch_gateway_payment


@transaction.atomic
def reconcile_order_refund(order_id, payment):
    """Record Razorpay's observed refund total. This never initiates a refund."""
    order = Order.objects.select_for_update().get(pk=order_id)
    if (
        order.status != Order.Status.PAID
        or not order.gateway_payment_id
        or not order.gateway_order_id
        or order.verified_at is None
    ):
        raise ValueError("Only gateway-verified payments can be reconciled.")
    amount = payment.get("amount")
    refunded = payment.get("amount_refunded")
    if (
        payment.get("id") != order.gateway_payment_id
        or payment.get("order_id") != order.gateway_order_id
        or payment.get("currency") != "INR"
        or payment.get("status") not in ("captured", "refunded")
        or type(amount) is not int or amount != amount_in_paise(order.amount)
        or type(refunded) is not int or not 0 <= refunded <= amount
        or (payment.get("status") == "refunded" and refunded != amount)
    ):
        raise ValueError("Gateway payment does not match the order.")
    refunded_amount = Decimal(refunded) / Decimal(100)
    if refunded_amount < order.refunded_amount:
        raise ValueError("Gateway response is older than recorded refunds.")
    order.refunded_amount = refunded_amount
    order.refund_checked_at = timezone.now()
    order.save(update_fields=["refunded_amount", "refund_checked_at", "updated_at"])

    if order.fully_refunded:
        Enrollment.objects.filter(student=order.student, course=order.course).update(is_active=False)
        notify(
            order.student, f"full-refund-{order.pk}", "Refund recorded",
            f"Your full refund for {order.course.title} was confirmed. Course access is inactive.",
        )
    return order


def reconcile_from_gateway(order_id):
    order = Order.objects.get(pk=order_id)
    if not order.gateway_payment_id or order.status != Order.Status.PAID:
        raise ValueError("Only paid gateway orders can be reconciled.")
    payment = fetch_gateway_payment(order.gateway_payment_id)
    return reconcile_order_refund(order_id, payment)
