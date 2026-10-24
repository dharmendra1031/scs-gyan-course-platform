# Client UI demo acceptance

This repository includes an automated `Client Demo Review` GitHub Actions
workflow. It creates a **disposable local Django demo** on the CI runner,
loads `courses/fixtures/demo_courses.json`, opens real Django pages in
Chromium and captures screenshots. This is **not** a production deployment
or a persistent staging URL.

## How to obtain client screenshots

1. Open GitHub → Actions → **Client Demo Review**.
2. Pick a successful workflow run, ideally on the latest `development` commit.
3. Download the **scs-gyan-client-ui-review** artifact.
4. Extract it, open `index.html`, and share the gallery/screenshots with the
   client for layout acceptance. GitHub artifact permissions may require login.
5. Replace demonstration course titles, descriptions and prices with client-
   approved content before publishing any public URL.

The workflow checks HTTP 200, expected content, navigation link clipping and
horizontal overflow on desktop (1280px), tablet (768px), mobile (390px), and
a separate 320px small-phone check. The gallery includes desktop, tablet,
mobile screenshots and three small-mobile samples.

## Client sign-off checklist

- SCS Gyan logo, colors, typography, menu labels and home section order
- Course cards, category search, course details and approved pricing
- Current Affairs, login/sign-up and contact pages
- Layout at desktop/tablet/small mobile sizes, readable text and navigation
- Student login, paid/free course access and learning progress
- Exams, PDFs, certificates and notifications
- Privacy text, refund policy, terms, approved course images and content

Mark each area as accepted or needing changes before deploying publicly.
This screenshot workflow does **not** cover WCAG accessibility auditing,
real third-party payments, end-to-end admin acceptance or load testing.

## Real staging deployment requirements

A genuine shareable staging URL needs approved hosting/domain, a trusted
HTTPS proxy, SQL Server connection and private media storage. Do not deploy
the SQLite demo or enable `DEBUG=True` on the internet. Make a staging
database separate from production; install dependencies, run migrations and
collectstatic, and enforce login/role boundaries. Keep Razorpay live
credentials **disabled** until payment sandbox acceptance is complete.
