import os
from pathlib import Path
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


@skipUnless(os.environ.get("RUN_BROWSER_TESTS") == "1", "Playwright runs in its own CI workflow.")
class ManagementBrowserTests(StaticLiveServerTestCase):
    def test_owner_management_desktop_and_mobile(self):
        from playwright.sync_api import sync_playwright

        get_user_model().objects.create_superuser(
            username="reviewowner", email="reviewowner@example.com",
            password="ReviewPassword123!",
        )
        output = Path("management-review")
        output.mkdir(exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for width in (390, 1280):
                    page = browser.new_page(viewport={"width": width, "height": 844})
                    page.goto(self.live_server_url + "/account/login/")
                    page.locator('input[name="username"]').fill("reviewowner")
                    page.locator('input[name="password"]').fill("ReviewPassword123!")
                    page.get_by_role("button", name="Sign In").click()
                    page.wait_for_url("**/management/")
                    assert "Welcome back" in page.locator("h1").inner_text()
                    page.screenshot(path=str(output / f"dashboard-{width}.png"), full_page=True)
                    if width < 740:
                        toggle = page.get_by_role("button", name="Management Menu")
                        assert toggle.get_attribute("aria-expanded") == "false"
                        toggle.click()
                        assert toggle.get_attribute("aria-expanded") == "true"
                        page.screenshot(path=str(output / f"menu-{width}.png"), full_page=True)
                    page.get_by_role("navigation", name="Management").get_by_role("link", name="Courses").click()
                    page.wait_for_url("**/management/content/courses/")
                    page.screenshot(path=str(output / f"courses-{width}.png"), full_page=True)
                    page.get_by_role("link", name="Add new").click()
                    page.wait_for_url("**/management/content/courses/new/")
                    assert page.get_by_role("textbox", name="Title", exact=True).is_visible()
                    dimensions = page.evaluate("""() => ({
                        width: innerWidth,
                        scroll: document.documentElement.scrollWidth,
                        overflowing: [...document.querySelectorAll('*')]
                            .filter(el => el.getBoundingClientRect().right > innerWidth + 2)
                            .slice(0, 8).map(el => el.tagName + '.' + el.className)
                    })""")
                    assert dimensions["scroll"] <= dimensions["width"] + 2, dimensions
                    page.screenshot(path=str(output / f"editor-{width}.png"), full_page=True)
                    page.close()
            finally:
                browser.close()

    def test_owner_can_manage_enquiry_and_view_student_on_mobile(self):
        from playwright.sync_api import sync_playwright
        from courses.models import Category, Course, Enrollment
        from pages.models import ContactEnquiry

        owner = get_user_model().objects.create_superuser(
            username="supportowner", email="supportowner@example.com",
            password="ReviewPassword123!",
        )
        student = get_user_model().objects.create_user(
            username="enrolledstudent", email="enrolledstudent@example.com",
            password="ReviewPassword123!",
        )
        category = Category.objects.create(name="Exam prep", slug="exam-prep")
        course = Course.objects.create(
            category=category, title="Exam Prep 101", slug="exam-prep-101",
            summary="Starter course", description="Introduction", price=0,
            is_published=True,
        )
        Enrollment.objects.create(course=course, student=student)
        enquiry = ContactEnquiry.objects.create(
            name="Interested Learner", email="learner@example.com",
            subject="Batch details", message="Please send details of the next course.",
        )
        output = Path("management-review")
        output.mkdir(exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(self.live_server_url + "/account/login/")
                page.locator('input[name="username"]').fill(owner.username)
                page.locator('input[name="password"]').fill("ReviewPassword123!")
                page.get_by_role("button", name="Sign In").click()
                page.wait_for_url("**/management/")
                page.goto(self.live_server_url + f"/management/students/{student.pk}/")
                assert "Exam Prep 101" in page.locator("body").inner_text()
                assert "enrolledstudent@example.com" in page.locator("body").inner_text()
                page.screenshot(path=str(output / "student-detail-390.png"), full_page=True)
                page.goto(self.live_server_url + f"/management/enquiries/{enquiry.pk}/")
                assert page.get_by_role("heading", name="Batch details").is_visible()
                page.get_by_label("Status").select_option("in_progress")
                page.get_by_label("Internal notes").fill("Call student after 4 PM.")
                page.get_by_role("button", name="Save follow-up").click()
                assert "Enquiry updated." in page.locator("body").inner_text()
                assert page.get_by_label("Status").input_value() == "in_progress"
                assert "Call student after 4 PM." in page.locator("body").inner_text()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
                page.screenshot(path=str(output / "enquiry-detail-390.png"), full_page=True)
            finally:
                browser.close()
