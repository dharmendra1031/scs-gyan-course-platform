from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from articles.models import Article
from courses.models import Category, Course


class SeoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cat = Category.objects.create(name="SEO", slug="seo")
        cls.published_course = Course.objects.create(
            category=cat, title="Published Course", slug="published-seo",
            summary="Course summary", seo_title="SEO Course Title",
            seo_description="Search-friendly course summary",
            description="Content", price=Decimal("0"), is_published=True,
        )
        Course.objects.create(
            category=cat, title="Draft Course", slug="draft-seo",
            summary="Draft", description="Draft", price=Decimal("0"), is_published=False,
        )
        cls.article = Article.objects.create(
            title="Published Article", slug="published-article",
            summary="Article summary", seo_title="SEO Article Title",
            seo_description="Search-friendly article summary",
            content="Article content", is_published=True,
        )
        Article.objects.create(
            title="Future Article", slug="future-seo",
            summary="Future", content="Future content", is_published=True,
            published_at=timezone.now() + timedelta(days=2),
        )

    def test_sitemap_excludes_drafts_future_and_student_pages(self):
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("/courses/published-seo/", body)
        self.assertIn("/articles/published-article/", body)
        self.assertNotIn("/courses/draft-seo/", body)
        self.assertNotIn("/articles/future-seo/", body)
        self.assertNotIn("/account/", body)
        self.assertNotIn("/assessments/", body)

    def test_meta_title_description_and_clean_canonical(self):
        response = self.client.get(
            self.published_course.get_absolute_url(), {"utm_source": "newsletter"}
        )
        self.assertContains(response, "SEO Course Title | SCS Gyan")
        self.assertContains(response, 'content="Search-friendly course summary"')
        self.assertContains(
            response, f'href="http://testserver{self.published_course.get_absolute_url()}"'
        )
        self.assertNotContains(response, "utm_source")
        self.assertContains(
            self.client.get(self.article.get_absolute_url()),
            "SEO Article Title | SCS Gyan",
        )

    def test_robots_references_public_sitemap(self):
        response = self.client.get(reverse("robots_txt"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")
        self.assertContains(response, "Disallow: /account/")
