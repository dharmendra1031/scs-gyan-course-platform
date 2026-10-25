# Content and Exams

## Current Affairs, Editorials and Blog

Admins manage Articles at `/admin/articles/article/`. Each article has a section,
slug, summary, content, publish flag, and publish date. A public article appears
on `/articles/` only when published and its publish date is not in the future.
The website supports title/summary search and section filters.

Drafts and scheduled articles return 404 to public visitors until their
publication conditions are met. The current version uses plain-text content,
rendered with safe line breaks; it does not support arbitrary uploaded HTML.

## Question Bank and Test Series

An admin creates an Assessment for a Course, adds Questions and choices, and
marks exactly one correct choice per question. Publish only when the questions
are complete. A Question can include an optional explanation.

`quiz` — regular course quiz

`test` — course test series

`daily` — date-restricted daily quiz. Set the daily date. Future quizzes are
not listed or directly accessible.

Students must have an active Enrollment in a published Course to start a
published assessment. The daily quiz list at `/assessments/daily/` shows only
date-eligible quizzes from their active courses.

### Student results

- One attempt per student and assessment (current policy).
- Score is calculated server-side from the persisted correct choices.
- Unanswered and incorrect answers earn zero marks. The assessment expires
  at its server-side deadline, even if the browser timer is manipulated.
- Review of correct answers and explanations is visible only after submission.
- Students see their own rank (equal scores share a rank) among submitted
  attempts with the same total possible marks; the system never publishes a
  named student leaderboard.
- Result URLs require both ownership and active course enrollment.

Admin performance summaries are available through Django Admin and show
submitted attempts, average marks and highest marks.

## Limitations

Published question content/answers should not be edited after students have
attempted the assessment; assessment versioning and retake windows are not yet
implemented. Browser countdown is for usability; the server is authoritative.

Automated Django, SQL Server and Chromium tests are run in GitHub Actions.
This does not replace review of real curriculum content or a production
accessibility/security acceptance test.
