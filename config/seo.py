from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from articles.models import Article
from courses.models import Course


def canonical_context(request):
    return {"canonical_url": request.build_absolute_uri(request.path)}


class CourseSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Course.objects.filter(is_published=True)

    def lastmod(self, item):
        return item.updated_at


class ArticleSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.6

    def items(self):
        return Article.objects.filter(
            is_published=True, published_at__lte=timezone.now(),
        )

    def lastmod(self, item):
        return item.updated_at


class StaticSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return ["home", "course_list", "article_list", "about", "contact"]

    def location(self, item):
        return reverse(item)


sitemaps = {
    "courses": CourseSitemap,
    "articles": ArticleSitemap,
    "pages": StaticSitemap,
}


def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Disallow: /admin/\n"
        "Disallow: /account/\n"
        "Disallow: /assessments/\n"
        "Disallow: /courses/lessons/\n"
        "Disallow: /courses/materials/\n"
        "Disallow: /courses/payments/\n"
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}\n"
    )
    return HttpResponse(content, content_type="text/plain")
