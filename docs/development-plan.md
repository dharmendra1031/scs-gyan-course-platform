# SCS Gyan — Development Plan

## Reference and product goal

Reference: https://www.drishtiias.com/eng

Build a new SCS Gyan-branded educational website. Reference the information architecture and teaching flows; do not reuse Drishti branding, copyrighted media or private code.

## Screens

### Public
- Homepage with courses, highlights, latest updates and calls to action
- About, contact, FAQs, policy pages
- Course catalog with search, categories and course details
- Online courses, classroom programmes, distance learning programmes
- News/current affairs, editorial articles and daily/weekly quizzes
- Media/videos, blog and downloadable study material
- Test series listing, programme details and enrollment
- Store product catalog, cart and order pages (if physical products are approved)

### Students
- Registration/login/password reset/profile
- Purchased/enrolled courses, lessons, video player, PDF notes
- Progress tracking, test attempts, results and answer review
- Order history, invoices and help requests

### Admin
- Users and permissions, course categories, courses, pricing and lessons
- Enrollments, orders, payments, discounts and refunds status
- Batches, live class metadata, materials and test series
- CMS articles, blog, current affairs, videos and banners
- SEO metadata and site settings
- Student, course and sales reports

## Proposed database (SQL Server)

All new PK columns are numeric `BIGINT IDENTITY` / Django `BigAutoField`. Foreign keys store numeric IDs. No UUID/GUID identifiers.

| Domain | Planned tables |
| --- | --- |
| Authentication | User, Group/Permission (Django auth) |
| Courses | Category, Course, CourseSection, Lesson, LessonMaterial |
| Students | Enrollment, LessonProgress |
| Commerce | Order, OrderItem, Payment, Coupon, Invoice |
| Exams | TestSeries, Test, Question, AnswerOption, TestAttempt, AttemptAnswer |
| Editorial | ContentCategory, Article, Announcement, MediaItem |
| Store | Product, CartItem, ShippingAddress, Shipment (if applicable) |
| Operations | ContactInquiry, SiteBanner, Setting |

Only initial User, Category and Course tables are implemented in the starter.

## Build sequence (target 30 calendar days, subject to approved scope)

1. Days 1–5: SCS Gyan desktop/mobile design approval, homepage and public site foundation.
2. Days 6–10: SQL Server migration verification, accounts, roles, courses, categories, lessons and course admin.
3. Days 11–17: Checkout, verified payment webhooks, enrollments, access control and student learning pages.
4. Days 18–23: Test series, current affairs, blogs, media, CMS, programme/DLP pages and store scope.
5. Days 24–27: Admin reports, SEO, caching, email templates, security checks, responsive/UI QA.
6. Days 28–30: Regression tests, payment sandbox, SQL Server integration tests, deployment and handover.

A full feature-equivalent Drishti-scale platform, including dedicated native apps, proprietary video DRM, sophisticated answer evaluation and complete physical-store logistics, is **larger than a guaranteed 30-day/₹50,000 delivery**. Agree exact acceptance criteria and third-party services before committing to those features within the original quote.

## Delivery standards

- Server-rendered Django with clean app boundaries and reusable templates.
- SQL Server on production; SQLite permitted for fast local UI tests only.
- All IDs numeric, auto-increment. No UUID/GUID.
- Never trust client-side totals; compute server-side and verify payment webhooks.
- Restrict paid lessons to enrolled students and protect media using signed URLs/private storage (later phase).
- Use CSRF protection, safe password storage, role-based permissions and secrets only in environment.
- Run CI checks on pull requests. Test real SQL Server migrations, checkout, browser journeys and backups before go-live.
- Do not commit credentials or course videos to the public repository.

## Current status

Code package created locally; not pushed to GitHub. UI concept screenshots made via Playwright using an HTML prototype. Python syntax and JSON fixture were checked. The environment could not download/install Django, therefore Django tests and database migrations have **not** run. SQL Server, payment integration and deployment are not complete.


## Phase 2 progress (development branch)

- Chapters and lessons can be managed through Django Admin.
- Student enrollment for free courses is immediate; paid course requests create **pending** orders only.
- A trusted admin can approve an order **after independently verifying payment**; approval is idempotent.
- Enrolled students can view published lessons, download access-controlled PDF notes, and track completion.
- Student and administrator access use Django session authentication and built-in staff/permission controls.
- PDF notes are stored outside public MEDIA_ROOT under PRIVATE_MEDIA_ROOT; deploy with private storage and backups.
- External video links are **not** DRM protected. Never use a public URL for confidential video assets.
- **Not implemented:** payment gateway, payment webhooks, refunds, coupons, teacher roles, video DRM, SQL Server live integration and production deployment.
- **Required testing:** Django CI (SQLite), SQL Server/ODBC integration, real admin manual-approval flow, browser and security acceptance.
