from django.db import transaction

from .models import Enrollment, Order


@transaction.atomic
def approve_order(order_id):
    """Administrative payment approval; call only after verifying payment externally."""
    order = Order.objects.select_for_update().get(pk=order_id)
    if order.status == Order.Status.CANCELLED:
        raise ValueError("Cancelled orders cannot be approved.")

    enrollment, _ = Enrollment.objects.get_or_create(
        student=order.student,
        course=order.course,
    )
    if not enrollment.is_active:
        enrollment.is_active = True
        enrollment.save(update_fields=["is_active"])

    if order.status != Order.Status.PAID:
        order.status = Order.Status.PAID
        order.save(update_fields=["status", "updated_at"])
    return enrollment
