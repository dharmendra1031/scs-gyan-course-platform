from django.shortcuts import render

from courses.models import Course


def home(request):
    courses = Course.objects.filter(is_published=True).select_related("category")[:3]
    return render(request, "pages/home.html", {"featured_courses": courses})


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")
