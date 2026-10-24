from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView

from .models import Article


def published_articles():
    return Article.objects.filter(is_published=True, published_at__lte=timezone.now())


class ArticleListView(ListView):
    template_name = "articles/list.html"
    context_object_name = "articles"
    paginate_by = 12

    def get_queryset(self):
        queryset = published_articles()
        section = self.request.GET.get("section", "")
        if section in Article.Section.values:
            queryset = queryset.filter(section=section)
        search = self.request.GET.get("q", "").strip()[:100]
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(summary__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections"] = Article.Section.choices
        context["current_section"] = self.request.GET.get("section", "")
        context["search"] = self.request.GET.get("q", "")
        return context


def article_detail(request, slug):
    article = get_object_or_404(published_articles(), slug=slug)
    return render(request, "articles/detail.html", {"article": article})
