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
