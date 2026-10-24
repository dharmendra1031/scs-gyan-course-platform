# Production acceptance checklist

This file is a deployment guide, not evidence of a live deployment.

## Environment

- Run with `DEBUG=False`, a fresh unpredictable `SECRET_KEY`, and explicit
  `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Use environment variables / server secret storage. Never commit `.env`,
  SQL credentials, live Razorpay API secrets or webhook signing secret.
- Put the Django site behind HTTPS and a supported WSGI app server.
  On Windows IIS, use a correctly configured reverse proxy to the WSGI server;
  do not use `runserver` for production.
- Install ODBC Driver 18, use an application DB login with least privilege,
  and verify SQL Server TLS certificate validation.
- Keep `PRIVATE_MEDIA_ROOT` outside all public static/media mounts. Verify
  permissions on course PDFs and make backup/restore plans.
- Run `python manage.py check --deploy`,
  `python manage.py migrate --noinput`,
  and `python manage.py collectstatic --noinput` before release.
- Set `TRUST_REVERSE_PROXY_HTTPS=True` **only** when the upstream trusted
  proxy strips untrusted client-supplied forwarded protocol headers.
- Once HTTPS and all subdomains are confirmed safe, progressively enable
  `SECURE_HSTS_SECONDS`, optional includeSubDomains and preload; do not
  preload an unverified domain.

## Student notifications

In-app notifications live at `/account/notifications/` and are user-private.
They are deduplicated per event and do not send emails, SMS or WhatsApp
messages. Configure actual delivery later if requested.

## Certificates

Completing all currently published lessons in an active course enrollment
issues a course-completion PDF with a numeric SCS Gyan reference.
A course must have at least one published lesson; expired/revoked enrollments
cannot download their certificates through the student portal.

The PDF is an **informal course-completion statement**, not an accredited
qualification or verification of exam passing. It currently uses ReportLab's
English font; non-Latin (including Hindi) output requires a properly licensed
Unicode font and shaping verification before acceptance. Do not add licensed
fonts to the public GitHub repository.

Published lessons added after issuing an existing certificate do not revoke
the already-issued certificate: issuance is a snapshot of completion.

## SEO

Configure course/article SEO title and description through Django Admin.
Only published courses and articles whose publication date has arrived appear
in sitemap.xml. Canonical links exclude query strings. Crawlers may ignore
robots.txt, so authorization remains mandatory.

## Outstanding acceptance

- Real Razorpay sandbox test with provider callbacks and test webhooks
- Refund, reversal/chargeback handling and financial reconciliation
- Actual client domain, HTTPS certificates, IIS/proxy setup, SQL backup/restore
- File content inspection, malware scanning and storage provider authorization
- Video streaming DRM if contractually required; external links are not DRM
- SEO audit, responsive UX/accessibility review, email/SMS preferences
- Production observability, rate limits, logs and restore testing
