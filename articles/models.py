from django.db import models
from django.urls import reverse
from django.utils import timezone


class Article(models.Model):
    class Section(models.TextChoices):
        CURRENT_AFFAIRS = "current_affairs", "Current Affairs"
        EDITORIAL = "editorial", "Editorial"
        BLOG = "blog", "Blog"

    title = models.CharField(max_length=220)
    slug = models.SlugField(max_length=230, unique=True)
    section = models.CharField(max_length=20, choices=Section.choices, default=Section.CURRENT_AFFAIRS)
    summary = models.CharField(max_length=350)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.CharField(max_length=320, blank=True)
    content = models.TextField()
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("article_detail", kwargs={"slug": self.slug})
