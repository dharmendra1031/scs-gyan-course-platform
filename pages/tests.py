from django.test import TestCase
from django.urls import reverse


class PublicPagesTests(TestCase):
    def test_homepage_loads(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_contact_page_loads(self):
        self.assertEqual(self.client.get(reverse("contact")).status_code, 200)
