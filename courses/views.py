from django.db.models import Q
from django.views.generic import DetailView, ListView

from .models import Category, Course


class CourseListView(ListView):
    template_name = "courses/list.html"
    context_object_name = "courses"
    paginate_by = 9

    def get_queryset(self):
        queryset = Course.objects.filter(is_published=True).select_related("category")
        category = self.request.GET.get("category", "").strip()
        search = self.request.GET.get("q", "").strip()
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(summary__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["current_category"] = self.request.GET.get("category", "")
        context["search"] = self.request.GET.get("q", "")
        return context


class CourseDetailView(DetailView):
    template_name = "courses/detail.html"
    context_object_name = "course"
    slug_field = "slug"

    def get_queryset(self):
        return Course.objects.filter(is_published=True).select_related("category")
