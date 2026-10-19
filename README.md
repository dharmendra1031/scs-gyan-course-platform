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

The initial GitHub Actions workflow runs unit tests against temporary SQLite to catch application regressions quickly. A dedicated SQL Server integration job, payment gateway sandbox tests and Playwright E2E tests are **not implemented yet**. Those are required before production acceptance.

## Existing first slice

- Responsive homepage, about and contact placeholders
- Published course catalog, category/search filters and course details
- Student signup, login, logout and protected dashboard placeholder
- Course/category management in Django Admin
- Initial migrations, security defaults and basic unit tests

## Next phase (not yet implemented)

Approved UI design, checkout/payments, enrollment, lessons, media, quizzes, test series, articles/current affairs, SEO editor, receipts, reports, bookstore/DLP workflows and integration testing.

## Important

Do not commit `.env`, SQL connection strings, payment secrets or licensed course assets. Public repositories expose their entire committed history. Require pull-request reviews and passing CI checks before merging to `main`.
