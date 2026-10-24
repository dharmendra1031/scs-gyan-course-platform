from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article


class ArticleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.published = Article.objects.create(
            title="Today's current affairs", slug="today-current-affairs",
            section=Article.Section.CURRENT_AFFAIRS, summary="Daily summary",
            content="Learning details", is_published=True,
        )
        Article.objects.create(
            title="Draft article", slug="draft-article", summary="Not public",
            content="Private", is_published=False,
        )
        Article.objects.create(
            title="Future article", slug="future-article", summary="Not yet published",
            content="Scheduled", is_published=True,
            published_at=timezone.now() + timedelta(days=2),
        )

    def test_only_published_articles_are_visible(self):
        response = self.client.get(reverse("article_list"))
        self.assertContains(response, "Today's current affairs")
        self.assertNotContains(response, "Draft article")
        self.assertNotContains(response, "Future article")
        self.assertContains(self.client.get(self.published.get_absolute_url()), "Learning details")

    def test_future_and_draft_articles_return_404(self):
        for slug in ("draft-article", "future-article"):
            self.assertEqual(
                self.client.get(reverse("article_detail", args=[slug])).status_code, 404,
            )

    def test_search_and_section_filter(self):
        response = self.client.get(reverse("article_list"), {"q": "Today's", "section": "current_affairs"})
        self.assertContains(response, "Today's current affairs")
        self.assertEqual(len(response.context["articles"]), 1)
        response = self.client.get(reverse("article_list"), {"section": "blog"})
        self.assertNotContains(response, "Today's current affairs")
