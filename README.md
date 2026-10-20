# SCS Gyan Course Platform

Django course selling platform starter with a responsive public website, student account foundation and Django Admin course management.

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

Go to `http://127.0.0.1:8000/` for the public website and `/admin/` for course management.

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
- Course, Chapter and Lesson management in Django Admin
- Free enrollment, pending paid orders, student lesson progress, protected PDF notes
- Optional Razorpay checkout with server-side signature verification, payment capture
  validation, idempotent webhooks, and superuser-only manual approval
- Numeric auto-increment IDs (BigAutoField) for application models

## Payment setup

See [Payment Setup](docs/payment-setup.md). Leave the gateway keys blank until the
client selects Razorpay and its test-mode account is ready. The gateway is disabled
without both key ID and secret. A successful CI run **does not** mean live money
handling or production deployment has been verified.

## Remaining

- Razorpay test-mode acceptance with actual provider API/webhooks
- Production database and storage verification; receipts/refunds and dispute processes
- UI/UX acceptance, quizzes/test series, articles/current affairs, SEO, reports,
  bookstore/DLP workflows, deployment and real production security review

## Important

Do not commit `.env`, SQL connection strings, payment secrets or licensed course assets. Public repositories expose their entire committed history. Require pull-request reviews and passing CI checks before merging to `main`.
