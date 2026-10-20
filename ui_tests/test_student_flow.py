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
