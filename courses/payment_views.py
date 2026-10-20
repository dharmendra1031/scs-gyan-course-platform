import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Order
from .payments import (
    PaymentError, amount_in_paise, confirm_gateway_payment,
    create_gateway_order, fetch_gateway_payment, gateway_enabled,
    valid_signature, valid_webhook,
)


@login_required
@require_POST
def checkout(request, order_id):
    if not gateway_enabled():
        messages.error(request, "Online payments are not available yet.")
        return redirect("dashboard")
    try:
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update().select_related("course"),
                pk=order_id, student=request.user,
                status=Order.Status.PENDING, course__is_published=True,
            )
            if not order.gateway_order_id:
                order.gateway_order_id = create_gateway_order(order)
                order.save(update_fields=["gateway_order_id", "updated_at"])
    except PaymentError:
        messages.error(request, "Payment service is unavailable. Try again.")
        return redirect("dashboard")
    return render(request, "courses/checkout.html", {
        "order": order, "gateway_key": settings.RAZORPAY_KEY_ID,
        "amount_paise": amount_in_paise(order.amount),
    })


@login_required
@require_POST
def verify_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id, student=request.user)
    order_id_from_client = request.POST.get("razorpay_order_id", "")
    payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")
    if (not gateway_enabled() or not order.gateway_order_id
            or order.gateway_order_id != order_id_from_client
            or not valid_signature(order.gateway_order_id, payment_id, signature)):
        return HttpResponseBadRequest("Invalid payment confirmation.")
    try:
        payment = fetch_gateway_payment(payment_id)
        confirm_gateway_payment(order.pk, order.gateway_order_id, payment)
    except PaymentError:
        return HttpResponse("Payment verification unavailable. Check orders later.", status=503)
    except ValueError:
        return HttpResponseBadRequest("Payment has not been captured for this order.")
    messages.success(request, "Payment verified. Your course is now available.")
    return redirect("course_learn", slug=order.course.slug)


@login_required
@never_cache
def payment_receipt(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("course"),
        pk=order_id, student=request.user, status=Order.Status.PAID,
    )
    return render(request, "courses/receipt.html", {"order": order})


@csrf_exempt
@require_POST
def payment_webhook(request):
    if not valid_webhook(request.body, request.headers.get("X-Razorpay-Signature", "")):
        return HttpResponseBadRequest("Invalid webhook signature.")
    try:
        event = json.loads(request.body)
        if event.get("event") != "payment.captured":
            return HttpResponse(status=200)
        payment = event["payload"]["payment"]["entity"]
        order = Order.objects.get(gateway_order_id=payment["order_id"])
        confirm_gateway_payment(order.pk, payment["order_id"], payment)
    except (KeyError, TypeError, ValueError, Order.DoesNotExist):
        return HttpResponseBadRequest("Invalid webhook payload.")
    return HttpResponse(status=200)
