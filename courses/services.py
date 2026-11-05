from django.db import transaction
from django.utils import timezone

from accounts.notifications import notify
from .models import Enrollment, Order


@transaction.atomic
def approve_order(order_id, *, reference="", approved_by=None):
    """Grant manual access only after an owner records external payment evidence."""
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status == Order.Status.CANCELLED:
        raise ValueError("Cancelled orders cannot be approved.")
    if order.fully_refunded:
        raise ValueError("Fully refunded orders cannot be reactivated.")

    if (
        approved_by is None or not approved_by.is_active
        or not approved_by.is_superuser
    ):
        raise ValueError("Only an active owner can approve external payments.")

    reference = reference.strip()
    if not 6 <= len(reference) <= 120:
        raise ValueError("Enter a valid external payment or receipt reference.")

    if order.status == Order.Status.PAID:
        if order.manual_payment_reference != reference:
            raise ValueError("The order is already paid.")
        return Enrollment.objects.get(student=order.student, course=order.course)

    if (
        order.status != Order.Status.PENDING or order.gateway_order_id
        or order.gateway_payment_id or order.verified_at
    ):
        raise ValueError("Gateway orders must be verified through the payment provider.")

    if Order.objects.filter(
        manual_payment_reference=reference,
    ).exclude(pk=order.pk).exists():
        raise ValueError("This payment reference is already recorded for another order.")

    enrollment, _ = Enrollment.objects.update_or_create(
        student=order.student, course=order.course, defaults={"is_active": True},
    )
    order.status = Order.Status.PAID
    order.manual_payment_reference = reference
    order.manual_verified_at = timezone.now()
    order.manual_verified_by = approved_by
    order.save(update_fields=[
        "status", "manual_payment_reference", "manual_verified_at",
        "manual_verified_by", "updated_at",
    ])
    notify(
        order.student, f"manual-order-{order.pk}", "Course access approved",
        f"Your enrollment in {order.course.title} has been approved.",
        url_name="course_learn", args=[order.course.slug],
    )
    return enrollment
