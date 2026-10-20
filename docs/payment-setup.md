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
- Payment refunds, partial refunds and tax invoices are not implemented.
  Reconciliation and real Razorpay sandbox tests are still required.
- Lesson video links require an active enrollment before redirecting to the
  external video provider. This is not DRM: an externally shared provider URL
  might still work independently of SCS Gyan.
