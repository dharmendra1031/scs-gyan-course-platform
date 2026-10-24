from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from courses.models import Course
from .forms import ContactForm


def home(request):
    courses = Course.objects.filter(is_published=True).select_related("category")[:3]
    return render(request, "pages/home.html", {"featured_courses": courses})


def about(request):
    return render(request, "pages/about.html")


@never_cache
def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not form.cleaned_data["website"]:
            form.save()
        messages.success(request, "Your enquiry has been received.")
        return redirect("contact")
    return render(request, "pages/contact.html", {"form": form})
