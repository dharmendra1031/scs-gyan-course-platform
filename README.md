# SCS Gyan Course Platform

Django course selling platform starter with a responsive public website, student account foundation and a custom SCS Gyan management portal.

Client UI concept: open `design-preview.html` in a local browser. This is a static demonstration, not the running Django site. See `docs/development-plan.md` for planned modules and delivery stages.

## Stack

- Python 3.12+, Django 5.2 LTS
- SQL Server via `mssql-django` and ODBC Driver 18
- Django templates, plain CSS (no SPA build step)
- Numeric auto-increment `BigAutoField` primary keys for project models

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For Windows, copy `.env.example` to `.env` with File Explorer or `copy .env.example .env`. Change `SECRET_KEY` and SQL Server settings before running. Install Microsoft ODBC Driver 18 for SQL Server on the host.

Configure an empty SQL Server database called `scs_gyan` and a database login with appropriate schema permissions.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Go to `http://127.0.0.1:8000/` for the public website and `/management/` for owner-only course management.

For a **local-only UI demo** without SQL Server, set `DEBUG=True` and `DB_ENGINE=sqlite` in `.env`. Then run `migrate` and optionally load demonstration content:

```bash
python manage.py loaddata demo_courses
```

Fixtures use made-up sample courses and prices for demonstrating layout only; they are not actual approved products.

## Testing

```bash
# Use a disposable test database; never run destructive tests on a production database.
python manage.py test
python manage.py makemigrations --check --dry-run
```

GitHub Actions runs the Django unit tests on SQLite, a separate SQL Server
integration workflow (SQL Server 2022 container), and Playwright Chromium browser
tests on each push to `development` and pull request to `main`.

## Implemented so far

- Public course catalog and responsive pages
- Student signup, login and course dashboard
- Course, Chapter and Lesson management in the custom owner portal
- Free enrollment, pending paid orders, student lesson progress, protected PDF notes
- Optional Razorpay checkout with server-side signature verification, payment capture
  validation, idempotent webhooks, and superuser-only manual approval
- Quiz, Test Series and enrolled-student Daily Quiz with server-side scoring,
  answer explanations, private results and personal rank
- Current Affairs, Editorial and Blog with publish scheduling, search and filters
- Management-portal course PDF study materials served from private storage to enrolled students
- Student test history with private result links and pagination
- Superuser-only course reports with enrollments, lessons, PDF counts, pending orders and verified gateway order value
- Read-only Razorpay refund reconciliation with partial/full refund tracking and net recorded value
- Numeric auto-increment IDs (BigAutoField) for application models

See [Content and Exams](docs/content-and-exams.md) for publishing and student
access rules. See [Study Materials and Reports](docs/study-materials-and-reports.md)
for new features and deployment notes.

## Payment setup

See [Payment Setup](docs/payment-setup.md). Leave the gateway keys blank until the
client selects Razorpay and its test-mode account is ready. The gateway is disabled
without both key ID and secret. A successful CI run **does not** mean live money
handling or production deployment has been verified.

## Remaining

- Razorpay test-mode acceptance with actual provider API/webhooks and refund lifecycle
- Production database and storage verification; tax invoices and dispute processes
- Client content, advanced test analytics and configurable retakes
- SEO editor, certificates, bookstore/DLP workflows and production reporting
- UI/UX acceptance, deployment and real production security review

## Client demo screenshots

A [Client Demo Review](docs/client-demo-review.md) workflow renders the running
Django site in Chromium at desktop/tablet/mobile sizes, checks horizontal
overflow and uploads an offline screenshot gallery as a GitHub Actions artifact.
The review uses fictional demo courses on disposable SQLite and does not
deploy a publicly accessible staging environment.

## Phase 9 — Staging package

GitHub Actions **Staging Release Package** creates an archived Django/Waitress
release (source code, collected static assets, file checksum manifest).
The workflow also starts the extracted ZIP locally and checks its public
routes. See [Staging Deployment](docs/staging-deployment.md) for Windows IIS,
ODBC 18, SQL Server, configuration and HTTPS instructions.

The package contains no database, secret `.env`, private student PDF or
customer content. Production hosting, real TLS and SQL Server integration
on the target environment remain separate acceptance steps.

## Important

Do not commit `.env`, SQL connection strings, payment secrets or licensed course assets. Public repositories expose their entire committed history. Require pull-request reviews and passing CI checks before merging to `main`.

## Phase 6 additions

- Editable SEO metadata, canonical links, published-only XML sitemap and robots.txt
- Course-completion certificate PDFs after completing all published lessons
- Student in-app notifications for enrollment, payment confirmation and certificate issue
- Production configuration checks and deployment checklist (see
  [Production Checklist](docs/production-checklist.md))

**Not yet accepted for production:** Real Razorpay sandbox transactions and refunds,
approved domain/hosting, backups, production private storage, end-to-end admin UI
acceptance, and deployment monitoring.

## Custom management portal

Django's built-in Admin interface is **not installed or routed**. Only
authenticated active superusers can access `/management/`. It includes
content editing (categories, courses, lessons, materials, articles, questions,
and answer choices), student and enquiry lists, paid order approval, read-only
Razorpay refund checks, and performance reports.

Create an initial owner with `python manage.py createsuperuser`; staff accounts
alone cannot access management. Access checks are server-side. Session logout
uses POST and all editing and payment actions require CSRF-protected POST.
The portal shares Django authentication and SQL Server persistence but uses
independent templates and a small `management.css` design layer.

It does not provide granular staff roles or live gateway settlement; those
need separate acceptance and authorization design.
