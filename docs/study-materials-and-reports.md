# Study Materials, Test History and Course Reports

## Course-level PDFs

Use **Django Admin → Courses → Study Materials** to assign a PDF to a course,
add a title/description, and publish it. Only a published PDF belonging to a
published course is offered in its learning page.

An authenticated student needs an **active Enrollment in that course** to
download. The response streams the PDF as an attachment with no-cache headers.
Private files are stored under `PRIVATE_MEDIA_ROOT`, not in the publicly served
`MEDIA_ROOT`. Do **not** expose `PRIVATE_MEDIA_ROOT` through nginx, IIS,
static-file aliases, buckets with public-read permissions or a Django URL.

Existing lesson-specific notes remain supported. This module adds reusable
course-level PDFs rather than replacing lesson notes.

The current upload validator checks the PDF extension; full malware/file-content
scanning and secure remote object-storage configuration are **not implemented**.

## Student Test History

Students can select **View My Test History** on the dashboard or navigate to
`/assessments/history/`. Results are paginated, private to the authenticated
student, and show completed attempts in actively enrolled courses.

Unsubmitted attempts, another student's results, and results from revoked
enrollments are excluded. This is not a public leaderboard.

## Course-wise Admin Report

A superuser can open **Django Admin → Courses → Course Reports** or
`/admin/courses/course/reports/`.

Reports show:
- Active student enrollments (unique students per course)
- Published lesson and PDF counts
- Pending orders
- Gateway-verified captured order counts and amount

This is an **operational report, not an accounting ledger**. Gateway payment
totals exclude manual approvals, but currently do **not** adjust for future
refunds, chargebacks, settlement fees or GST. Refund/reconciliation integration
remains pending. Only superusers can access the report.

## Verification

GitHub Actions separately checks Django with SQLite, SQL Server integration
on a disposable container, and Playwright Chromium browser flows. Production
storage permissions, payment reconciliation and client acceptance are still
required before launch.
