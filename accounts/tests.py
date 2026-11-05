from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_signup_creates_student(self):
        response = self.client.post(reverse("signup"), {
            "username": "student1", "email": "student@example.com",
            "first_name": "Test", "last_name": "Student",
            "password1": "StrongPassword!234", "password2": "StrongPassword!234",
        })
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(get_user_model().objects.filter(email="student@example.com").exists())

    def test_signup_returns_student_to_requested_course(self):
        course_url = "/courses/example-course/"
        response = self.client.post(reverse("signup"), {
            "username": "course_student", "email": "course@example.com",
            "first_name": "Course", "last_name": "Student",
            "password1": "StrongPassword!234", "password2": "StrongPassword!234",
            "next": course_url,
        })
        self.assertRedirects(response, course_url, fetch_redirect_response=False)
        self.assertTrue(get_user_model().objects.filter(username="course_student").exists())

    def test_signup_rejects_external_next_redirect(self):
        response = self.client.post(reverse("signup"), {
            "username": "safe_student", "email": "safe@example.com",
            "first_name": "Safe", "last_name": "Student",
            "password1": "StrongPassword!234", "password2": "StrongPassword!234",
            "next": "https://evil.example/steal",
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_signup_keeps_safe_next_for_login_link(self):
        response = self.client.get(reverse("signup"), {
            "next": "/courses/example-course/",
        })
        self.assertContains(response, "next=/courses/example-course/")

    def test_duplicate_email_is_rejected(self):
        get_user_model().objects.create_user(username="existing", email="student@example.com", password="StrongPassword!234")
        response = self.client.post(reverse("signup"), {
            "username": "student1", "email": "STUDENT@example.com",
            "first_name": "Test", "last_name": "Student",
            "password1": "StrongPassword!234", "password2": "StrongPassword!234",
        })
        self.assertContains(response, "already exists")

    def test_student_signup_has_no_admin_access(self):
        response = self.client.post(reverse("signup"), {
            "username": "student2", "email": "student2@example.com",
            "first_name": "Test", "last_name": "Student",
            "password1": "StrongPassword!234", "password2": "StrongPassword!234",
            "is_staff": "on", "is_superuser": "on",
        })
        self.assertEqual(response.status_code, 302)
        student = get_user_model().objects.get(username="student2")
        self.assertFalse(student.is_staff)
        self.assertFalse(student.is_superuser)
        self.assertEqual(self.client.get("/management/").status_code, 403)
        self.assertEqual(self.client.get("/admin/").status_code, 404)
