import os
from decimal import Decimal
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from courses.models import Category, Course


@skipUnless(os.environ.get("RUN_BROWSER_TESTS") == "1", "Playwright runs in its own workflow.")
class StudentBrowserTests(StaticLiveServerTestCase):
    def test_free_course_enrollment_on_mobile(self):
        from playwright.sync_api import sync_playwright

        category = Category.objects.create(name="UPSC", slug="upsc")
        Course.objects.create(
            category=category, title="Free Starter", slug="free-starter",
            summary="Course", description="Starter lesson",
            price=Decimal("0.00"), is_published=True,
        )
        get_user_model().objects.create_user(
            username="browseruser", email="browser@example.com", password="BrowserPass123!"
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(self.live_server_url + "/account/login/")
                page.locator('input[name="username"]').fill("browseruser")
                page.locator('input[name="password"]').fill("BrowserPass123!")
                page.locator('button[type="submit"]').click()
                page.wait_for_url("**/account/dashboard/")
                page.goto(self.live_server_url + "/courses/free-starter/")
                page.get_by_role("button", name="Enroll for free").click()
                page.wait_for_url("**/courses/free-starter/learn/")
                assert "Free Starter" in page.locator("h1").inner_text()
            finally:
                browser.close()

    def test_unenrolled_video_route_denied_in_browser(self):
        from playwright.sync_api import sync_playwright
        from courses.models import Chapter, Lesson

        category = Category.objects.create(name="Video Courses", slug="video-courses")
        course = Course.objects.create(
            category=category, title="Private Video", slug="private-video",
            summary="Video guide", description="Video lesson",
            price=Decimal("500.00"), is_published=True,
        )
        chapter = Chapter.objects.create(course=course, title="First chapter")
        lesson = Lesson.objects.create(
            chapter=chapter, title="Private Lesson",
            video_url="https://example.com/private-video", is_published=True,
        )
        get_user_model().objects.create_user(
            username="noaccess", email="noaccess@example.com", password="BrowserPass123!"
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})
                page.goto(self.live_server_url + "/account/login/")
                page.locator('input[name="username"]').fill("noaccess")
                page.locator('input[name="password"]').fill("BrowserPass123!")
                page.locator('button[type="submit"]').click()
                page.wait_for_url("**/account/dashboard/")
                response = page.goto(
                    self.live_server_url + f"/courses/lessons/{lesson.pk}/video/"
                )
                assert response.status == 404
                assert "https://example.com/private-video" not in page.content()
            finally:
                browser.close()

    def test_student_completes_quiz_on_mobile(self):
        from playwright.sync_api import sync_playwright
        from courses.models import Enrollment
        from exams.models import Assessment, Choice, Question

        category = Category.objects.create(name="Browser Exams", slug="browser-exams")
        course = Course.objects.create(
            category=category, title="Browser Test Course", slug="browser-test-course",
            summary="Quiz practice", description="Sample test",
            price=Decimal("0.00"), is_published=True,
        )
        user = get_user_model().objects.create_user(
            username="browserexam", email="browserexam@example.com", password="BrowserPass123!"
        )
        Enrollment.objects.create(student=user, course=course)
        assessment = Assessment.objects.create(
            course=course, title="Browser MCQ Quiz", duration_minutes=30, is_published=True,
        )
        question = Question.objects.create(assessment=assessment, text="What is two plus two?", marks=1, explanation="Two plus two equals four.")
        correct = Choice.objects.create(question=question, text="Four", is_correct=True)
        Choice.objects.create(question=question, text="Five", is_correct=False)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(self.live_server_url + "/account/login/")
                page.locator('input[name="username"]').fill("browserexam")
                page.locator('input[name="password"]').fill("BrowserPass123!")
                page.locator('button[type="submit"]').click()
                page.wait_for_url("**/account/dashboard/")
                page.goto(self.live_server_url + "/courses/browser-test-course/learn/")
                page.get_by_role("link", name="Browser MCQ Quiz").click()
                page.locator(f'input[name="question_{question.pk}"][value="{correct.pk}"]').check()
                page.get_by_role("button", name="Submit answers").click()
                page.wait_for_url("**/assessments/results/**")
                assert "1 / 1 marks" in page.locator("h2").first.inner_text()
                assert "Two plus two equals four." in page.locator("body").inner_text()
            finally:
                browser.close()

    def test_current_affairs_on_mobile(self):
        from playwright.sync_api import sync_playwright
        from articles.models import Article

        Article.objects.create(
            title="Latest current affairs", slug="latest-current-affairs",
            summary="A published article", content="Editorial study material",
            is_published=True,
        )
        Article.objects.create(
            title="Secret draft", slug="secret-draft",
            summary="Not published", content="Private material",
            is_published=False,
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(self.live_server_url + "/articles/")
                assert "Latest current affairs" in page.locator("body").inner_text()
                assert "Secret draft" not in page.locator("body").inner_text()
                page.get_by_role("link", name="Read article").click()
                page.wait_for_url("**/articles/latest-current-affairs/")
                assert "Editorial study material" in page.locator("body").inner_text()
            finally:
                browser.close()

    def test_student_can_browse_submitted_test_history(self):
        from playwright.sync_api import sync_playwright
        from django.utils import timezone
        from courses.models import Enrollment
        from exams.models import Assessment, Attempt

        category = Category.objects.create(name="Browser History", slug="browser-history")
        course = Course.objects.create(
            category=category, title="Browser History Course", slug="browser-history-course",
            summary="History", description="Test history",
            price=Decimal("0.00"), is_published=True,
        )
        user = get_user_model().objects.create_user(
            username="browsertesthistory", email="browsertesthistory@example.com",
            password="BrowserPass123!",
        )
        Enrollment.objects.create(student=user, course=course)
        assessment = Assessment.objects.create(
            course=course, title="Submitted History Quiz",
            duration_minutes=30, is_published=True,
        )
        Attempt.objects.create(
            assessment=assessment, student=user,
            submitted_at=timezone.now(), score=3, total_marks=5,
        )

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(self.live_server_url + "/account/login/")
                page.locator('input[name="username"]').fill("browsertesthistory")
                page.locator('input[name="password"]').fill("BrowserPass123!")
                page.locator('button[type="submit"]').click()
                page.wait_for_url("**/account/dashboard/")
                page.get_by_role("link", name="View My Test History").click()
                page.wait_for_url("**/assessments/history/")
                assert "Submitted History Quiz" in page.locator("body").inner_text()
                assert "60%" in page.locator("body").inner_text()
            finally:
                browser.close()

    def test_completion_certificate_and_notification_on_mobile(self):
        from playwright.sync_api import sync_playwright
        from courses.models import Chapter, Lesson

        category = Category.objects.create(name="Certificate Browser", slug="certificate-browser")
        course = Course.objects.create(
            category=category, title="Certificate Browser Course",
            slug="certificate-browser-course", summary="Earn a certificate",
            description="Finish the lesson", price=Decimal("0.00"),
            is_published=True,
        )
        chapter = Chapter.objects.create(course=course, title="First")
        Lesson.objects.create(
            chapter=chapter, title="Certificate Lesson", is_published=True,
        )
        get_user_model().objects.create_user(
            username="browsergraduate", email="browsergraduate@example.com",
            password="BrowserPass123!",
        )
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(self.live_server_url + "/account/login/")
                page.locator('input[name="username"]').fill("browsergraduate")
                page.locator('input[name="password"]').fill("BrowserPass123!")
                page.locator('button[type="submit"]').click()
                page.wait_for_url("**/account/dashboard/")
                page.goto(self.live_server_url + "/courses/certificate-browser-course/")
                page.get_by_role("button", name="Enroll for free").click()
                page.wait_for_url("**/courses/certificate-browser-course/learn/")
                page.get_by_role("link", name="Certificate Lesson", exact=True).click()
                page.get_by_role("button", name="Mark as completed").click()
                page.wait_for_url("**/courses/certificate-browser-course/learn/")
                assert page.get_by_role("link", name="Download Certificate").count() == 1
                page.goto(self.live_server_url + "/account/notifications/")
                assert "Course completed" in page.locator("body").inner_text()
            finally:
                browser.close()
