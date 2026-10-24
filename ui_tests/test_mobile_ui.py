import os
from unittest import skipUnless

from django.contrib.staticfiles.testing import StaticLiveServerTestCase


@skipUnless(os.environ.get("RUN_BROWSER_TESTS") == "1", "Playwright runs in browser CI.")
class MobileUiTests(StaticLiveServerTestCase):
    def test_accessible_compact_menu_at_320_and_390_pixels(self):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for width in (320, 390):
                    page = browser.new_page(viewport={"width": width, "height": 740})
                    page.goto(self.live_server_url + "/")
                    toggle = page.get_by_role("button", name="Menu")
                    navigation = page.get_by_role("navigation", name="Main navigation")
                    link = navigation.get_by_role("link", name="Courses")
                    assert toggle.is_visible()
                    assert toggle.get_attribute("aria-expanded") == "false"
                    assert not link.is_visible()
                    toggle.click()
                    assert toggle.get_attribute("aria-expanded") == "true"
                    assert link.is_visible()
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth + 2"
                    )
                    page.keyboard.press("Escape")
                    assert toggle.get_attribute("aria-expanded") == "false"
                    assert not link.is_visible()
                    toggle.click()
                    link.click()
                    page.wait_for_url("**/courses/")
                    assert "Explore Courses" in page.locator("body").inner_text()
                    page.close()
            finally:
                browser.close()

    def test_contact_form_mobile_validation_and_submit(self):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(self.live_server_url + "/contact/")
                page.get_by_label("Name").fill("Course Enquirer")
                page.get_by_label("Email").fill("student@example.com")
                page.get_by_label("Subject").fill("Enrollment question")
                page.get_by_label("Message").fill("I would like details about your upcoming classes.")
                page.get_by_role("button", name="Send Enquiry").click()
                assert "Your enquiry has been received." in page.locator("body").inner_text()
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth + 2"
                )
            finally:
                browser.close()
