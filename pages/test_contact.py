from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import ContactEnquiry


class ContactEnquiryTests(TestCase):
    def valid_data(self):
        return {
            "name": "Prospective Student",
            "email": "student@example.com",
            "subject": "Course guidance",
            "message": "Please share details of upcoming batches.",
        }

    def test_enquiry_is_saved_and_redirected(self):
        url = reverse("contact")
        self.assertContains(self.client.get(url), "Send Enquiry")
        response = self.client.post(url, self.valid_data(), follow=True)
        self.assertEqual(response.redirect_chain, [(url, 302)])
        self.assertEqual(ContactEnquiry.objects.count(), 1)
        self.assertContains(response, "Your enquiry has been received.")

    def test_invalid_email_and_short_message_cannot_submit(self):
        payload = self.valid_data()
        payload["email"] = "bad-email"
        payload["message"] = "short"
        response = self.client.post(reverse("contact"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valid email address")
        self.assertContains(response, "at least 10 characters")
        self.assertFalse(ContactEnquiry.objects.exists())

    def test_spam_honeypot_does_not_create_enquiry(self):
        payload = self.valid_data()
        payload["website"] = "https://automated-spam.example"
        self.assertRedirects(self.client.post(reverse("contact"), payload), reverse("contact"))
        self.assertFalse(ContactEnquiry.objects.exists())

    def test_only_superusers_can_view_enquiries(self):
        User = get_user_model()
        staff = User.objects.create_user(
            username="support", email="support@example.com",
            password="Passphrase123!secure", is_staff=True,
        )
        staff.user_permissions.add(Permission.objects.get(
            content_type__app_label="pages",
            content_type__model="contactenquiry",
            codename="view_contactenquiry",
        ))
        self.client.force_login(staff)
        self.assertEqual(
            self.client.get(reverse("management:enquiries")).status_code,
            403,
        )
        admin = User.objects.create_superuser(
            username="owner", email="owner@example.com", password="Passphrase123!secure",
        )
        self.client.force_login(admin)
        self.assertEqual(
            self.client.get(reverse("admin:pages_contactenquiry_changelist")).status_code,
            200,
        )
