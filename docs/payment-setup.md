# Razorpay test-mode configuration

The checkout is **optional** and remains disabled until the following
environment variables are set on the server:

```dotenv
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
```

1. Create Razorpay **test-mode** credentials in your own dashboard.
2. Put the keys in a local `.env` or production secret store, never in GitHub.
3. Set up a test webhook for `payment.captured` at
   `https://your-domain/courses/payments/webhook/` with a distinct webhook secret.
4. Run Django migrations (`python manage.py migrate`) after deployment.
5. Place a test-mode order in the student dashboard and verify callback and webhook
   handling; double-delivery must not generate a duplicate enrollment.
6. Before enabling live payments, verify capture settings, refund flows,
   reconciliation, HTTPS, CSP and audit logging with the business owner.

All prices and gateway order amounts are server-side values in INR paise.
Neither the checkout callback nor client-side JavaScript can grant course access
without a valid signature and a matching `captured` payment retrieved from the
payment provider. Webhooks require HMAC signature verification.

Orders can be manually approved only by a superuser after independent offline
payment verification. This is an exceptional operational override, not a
payment-gateway success callback.

The GitHub CI tests mock gateway API responses; **they cannot certify real bank
transactions**. Use Razorpay's official test mode before going live.

## Current limitations and acceptance

- The student **payment acknowledgement** uses the verified Razorpay reference.
  A manually approved order instead displays an enrollment confirmation.
  Neither document is a GST tax invoice.
- Old cancelled orders with a gateway reference cannot be silently reused at a
  new course price; ask support to reconcile or refund the original attempt.
- Read-only refund reconciliation is available to superusers through
  **Django Admin → Orders → Reconcile refunds from Razorpay**. This makes a
  `GET /v1/payments/{payment_id}` request and checks the provider's reported
  `amount_refunded`, original amount, payment/order IDs and currency.
- Partial refunds are recorded without revoking course access. A fully
  recorded refund revokes enrollment; re-running reconciliation does not
  duplicate notifications. Recorded refunds never decrease on stale responses.
- Reconciliation **does not initiate a refund**, make a bank transfer, handle
  chargebacks, or certify settlement. For now, initiate refunds only through
  the client's authorized Razorpay Dashboard process and reconcile afterward.
  Real Razorpay test-mode validation, fees, taxes and official invoices are
  still pending.
- Lesson video links require an active enrollment before redirecting to the
  external video provider. This is not DRM: an externally shared provider URL
  might still work independently of SCS Gyan.

## Phase 7 acceptance

Before live money handling, the client must confirm refund eligibility, terms,
who may initiate a refund in Razorpay, and the expected access policy on
partial versus full refunds. Test with Razorpay's test-mode payments and
refunds, including delayed/refused webhook events and manual refunds.

**Razorpay credentials must not be pasted into chat or committed to the
public repository.** Store them as deployment secrets.

Reconciled totals are point-in-time snapshots: without a real scheduler or
refund webhook they can become stale. The Admin course report deducts only
refunds that have been reconciled in the platform. It is not an accounting
ledger, GST invoice or bank settlement reconciliation.
